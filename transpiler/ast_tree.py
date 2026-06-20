from __future__ import annotations

from ast_nodes import (
    ArrayInit,
    ArrayType,
    Assign,
    BinOp,
    Block,
    BoolLit,
    NullLit,
    BreakStmt,
    Call,
    CastExpr,
    CharLit,
    ConstDeclStmt,
    ContinueStmt,
    DeferStmt,
    ExprStmt,
    FieldAccess,
    FieldDecl,
    FloatLit,
    ForStmt,
    ForVarDecl,
    FuncDecl,
    Ident,
    IfStmt,
    ImportLocal,
    ImportSystem,
    Index,
    IntLit,
    Param,
    PlainType,
    Program,
    RefType,
    ReturnStmt,
    StringLit,
    StructDecl,
    TntDeref,
    TntInt,
    TntStmt,
    TntString,
    TntVar,
    TypeArg,
    UnaryOp,
    VarDeclStmt,
    WhileStmt,
)
from lark import Transformer


class AstTransformer(Transformer):
    # ==========================================
    # AST METADATA HOOK
    # ==========================================
    def _call_userfunc(self, tree, new_children=None):
        # Intercept the node creation to automatically attach line and column data
        node = super()._call_userfunc(tree, new_children)

        # If the node is a standard object and Lark tracked its physical position
        if hasattr(node, "__dict__") and hasattr(tree, "meta") and not tree.meta.empty:
            # Use setattr to prevent Pyright 'unknown attribute' complaints
            setattr(node, "line", tree.meta.line)
            setattr(node, "column", tree.meta.column)

        return node

    ### Program ###

    def start(self, items):
        # items[0]  : list[Import]  from import_section
        # items[1:] : list[StructDecl | FuncDecl]  (top_level_decl is transparent)
        return Program(imports=items[0], decls=list(items[1:]))

    ### Imports ###

    def import_section(self, items):
        return list(items)

    def import_local(self, items):
        return ImportLocal(path=str(items[0]))

    def import_system(self, items):
        return ImportSystem(path=str(items[0]))

    ### Struct ###

    def struct_decl(self, items):
        # items[0]  : IDENT  (name)
        # items[1:] : list[FieldDecl]
        return StructDecl(name=str(items[0]), fields=list(items[1:]))

    def field_decl(self, items):
        return FieldDecl(name=str(items[0]), type=items[1])

    ### Function ###

    def func_decl(self, items):
        # items[0] : IDENT        (name)
        # items[1] : list[Param]  (param_list)
        # items[2] : Type         (return_type is transparent — type comes directly)
        # items[3] : Block
        return FuncDecl(
            name=str(items[0]),
            params=items[1],
            return_type=items[2],
            body=items[3],
        )

    def param_list(self, items):
        return list(items)

    def param(self, items):
        return Param(name=str(items[0]), type=items[1])

    ### Types ###

    def ref_type(self, items):
        return RefType(inner=items[0])

    def plain_type(self, items):
        # The child is already a PlainType produced by a base_* method.
        return items[0]

    def array_type(self, items):
        # items[0]         : PlainType  (element type)
        # items[1] or None : Expr       (optional size)
        return ArrayType(
            element=items[0],
            size=items[1] if len(items) > 1 else None,
        )

    # base_type aliases — keyword alternatives have no kept children;
    # base_ident has one IDENT token.
    def base_int(self, _):
        return PlainType("int")

    def base_char(self, _):
        return PlainType("char")

    def base_void(self, _):
        return PlainType("void")

    def base_float(self, _):
        return PlainType("float")

    def base_ident(self, items):
        return PlainType(str(items[0]))

    ### Block ###

    def block(self, items):
        # stmt is transparent, so items is already a flat list of Stmt nodes.
        return Block(stmts=list(items))

    ### Statements ###

    def var_decl_stmt(self, items):
        # items[0] : IDENT  (name)
        # items[1] : Type
        # items[2] : Expr   (optional initialiser)
        return VarDeclStmt(
            name=str(items[0]),
            type=items[1],
            init=items[2] if len(items) > 2 else None,
        )

    def const_decl_stmt(self, items):
        return ConstDeclStmt(name=str(items[0]), type=items[1], init=items[2])

    def if_stmt(self, items):
        # items[0] : Expr   (condition)
        # items[1] : Block  (then branch)
        # items[2] : IfStmt | Block  (optional else branch)
        return IfStmt(
            cond=items[0],
            then_block=items[1],
            else_branch=items[2] if len(items) > 2 else None,
        )

    def while_stmt(self, items):
        return WhileStmt(cond=items[0], body=items[1])

    def for_stmt(self, items):
        # items[0] : ForVarDecl | Expr | None  (for_init alias, already transformed)
        # items[1] : Expr                       (condition)
        # items[2] : Expr | None                (for_update alias, already transformed)
        # items[3] : Block
        return ForStmt(init=items[0], cond=items[1], update=items[2], body=items[3])

    def for_var_decl(self, items):
        return ForVarDecl(
            name=str(items[0]),
            type=items[1],
            init=items[2] if len(items) > 2 else None,
        )

    # for_init aliases — each returns the inner node (or None) for for_stmt.
    def for_init_decl(self, items):
        return items[0]  # ForVarDecl

    def for_init_expr(self, items):
        return items[0]  # Expr

    def for_init_empty(self, _):
        return None

    # for_update aliases
    def for_update_expr(self, items):
        return items[0]  # Expr

    def for_update_empty(self, _):
        return None

    def return_stmt(self, items):
        return ReturnStmt(value=items[0] if items else None)

    def break_stmt(self, _):
        return BreakStmt()

    def continue_stmt(self, _):
        return ContinueStmt()

    def defer_stmt(self, items):
        return DeferStmt(body=items[0])

    def tnt_stmt(self, items):
        return TntStmt(arg=items[0])

    # tnt_arg aliases
    def tnt_string(self, items):
        return TntString(value=str(items[0]))

    def tnt_int(self, items):
        return TntInt(value=int(items[0]))

    def tnt_var(self, items):
        return TntVar(name=str(items[0]))

    # tnt_deref grammar: "->" IDENT  — "->" is anonymous (filtered); only IDENT kept.
    def tnt_deref(self, items):
        return TntDeref(name=str(items[0]))

    def expr_stmt(self, items):
        return ExprStmt(expr=items[0])

    ### Expressions ###

    def assign(self, items):
        return Assign(target=items[0], value=items[1])

    # Binary operators — "or" / "and" are Python keywords; defined via setattr below.
    def eq(self, items):
        return BinOp("==", items[0], items[1])

    def neq(self, items):
        return BinOp("!=", items[0], items[1])

    def lt(self, items):
        return BinOp("<", items[0], items[1])

    def gt(self, items):
        return BinOp(">", items[0], items[1])

    def le(self, items):
        return BinOp("<=", items[0], items[1])

    def ge(self, items):
        return BinOp(">=", items[0], items[1])

    def add(self, items):
        return BinOp("+", items[0], items[1])

    def sub(self, items):
        return BinOp("-", items[0], items[1])

    def mul(self, items):
        return BinOp("*", items[0], items[1])

    def div(self, items):
        return BinOp("/", items[0], items[1])

    def mod(self, items):
        return BinOp("%", items[0], items[1])

    def cast_expr(self, items):
        # Transform an 'as' casting expression into a CastExpr AST node
        return CastExpr(expr=items[0], target_type=items[1])

    # Unary operators — "not" is a Python keyword; defined via setattr below.
    def neg(self, items):
        return UnaryOp("-", items[0])

    def deref(self, items):
        return UnaryOp("->", items[0])

    def addr(self, items):
        return UnaryOp("addr", items[0])

    def call(self, items):
        # items[0] : Expr        (callee)
        # items[1] : list[Expr]  (arg_list — already a Python list)
        return Call(callee=items[0], args=items[1])

    def field_access(self, items):
        # items[0] : Expr   (object)
        # items[1] : IDENT  (field name — named terminal, kept by Lark)
        return FieldAccess(obj=items[0], field=str(items[1]))

    def index(self, items):
        return Index(obj=items[0], idx=items[1])

    # Literals
    def int_lit(self, items):
        return IntLit(value=int(items[0]))

    def float_lit(self, items):
        return FloatLit(value=float(items[0]))

    def char_lit(self, items):
        return CharLit(value=str(items[0]))

    def string_lit(self, items):
        return StringLit(value=str(items[0]))

    def true_lit(self, _):
        return BoolLit(value=True)

    def false_lit(self, _):
        return BoolLit(value=False)

    def null_lit(self, _):
        return NullLit()

    def ident(self, items):
        return Ident(name=str(items[0]))

    # paren_expr carries no semantic information; just unwrap.
    def paren_expr(self, items):
        return items[0]

    def array_init(self, items):
        return ArrayInit(elements=list(items))

    def arg_list(self, items):
        return list(items)

    def arg_expr(self, items):
        return items[0]

    def arg_type(self, items):
        return TypeArg(type=items[0])


# "or", "and", "not" are Python reserved keywords and cannot appear as method
# names in a class body.  setattr() works because attribute names are plain
# strings at runtime, not subject to Python's grammar rules.
setattr(AstTransformer, "or", lambda _, items: BinOp("||", items[0], items[1]))
setattr(AstTransformer, "and", lambda _, items: BinOp("&&", items[0], items[1]))
setattr(AstTransformer, "not", lambda _, items: UnaryOp("!", items[0]))
