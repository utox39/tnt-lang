import sys
from typing import Any, NoReturn

from ast_nodes import (
    ArrayType,
    Assign,
    BinOp,
    Block,
    BoolLit,
    BreakStmt,
    Call,
    CharLit,
    ConstDeclStmt,
    ContinueStmt,
    DeferStmt,
    ExprStmt,
    FieldAccess,
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
    Type,
    UnaryOp,
    VarDeclStmt,
    WhileStmt,
)

# ==========================================
# ERROR REPORTING ENGINE
# ==========================================


class TntSemanticError(Exception):
    def __init__(self, title: str, details: str, hint: str = "") -> None:
        self.title = title
        self.details = details
        self.hint = hint

    def print_and_exit(self) -> NoReturn:
        red = "\033[1;31m"
        yellow = "\033[1;33m"
        reset = "\033[0m"

        print(f"\n {red}Error: {self.title}{reset}")
        print(f"   {self.details}")
        if self.hint:
            print(f"\n {yellow}Hint:{reset} {self.hint}")
        print()
        sys.exit(1)


def type_to_str(t: Type | None) -> str:
    if t is None:
        return "void"
    if isinstance(t, PlainType):
        return t.name
    if isinstance(t, RefType):
        return f"ref {type_to_str(t.inner)}"
    if isinstance(t, ArrayType):
        return f"{type_to_str(t.element)}[]"


# ==========================================
# SYMBOL TABLE
# ==========================================


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: list[dict[str, Type]] = [{}]

    def enter_scope(self) -> None:
        self.scopes.append({})

    def exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise RuntimeError("Compiler Bug: Attempted to pop the global scope.")

    def declare(self, name: str, var_type: Type) -> None:
        current_scope = self.scopes[-1]
        if name in current_scope:
            err = TntSemanticError(
                title="Duplicate Declaration",
                details=f"The identifier '{name}' is already defined in this scope.",
                hint="Try renaming this variable.",
            )
            err.print_and_exit()
        current_scope[name] = var_type

    def lookup(self, name: str) -> Type:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        err = TntSemanticError(
            title="Undefined Identifier",
            details=f"You tried to use '{name}', but it hasn't been declared.",
            hint=f"Did you forget to declare it with 'let {name}: type;'?",
        )
        err.print_and_exit()


# ==========================================
# SEMANTIC ANALYZER
# ==========================================


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.symtab = SymbolTable()
        self.current_function_return_type: Type | None = None

        # Pre-load system APIs
        self.symtab.declare("printf", PlainType("void"))

    def analyze(self, node: Any) -> Any:
        if node is None:
            return None

        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Any) -> Any:
        raise NotImplementedError(
            f"Compiler Bug: No visit method defined for {type(node).__name__}"
        )

    def expect_type(self, expected: Type, actual: Type, context: str) -> None:
        if expected != actual:
            exp_str = type_to_str(expected)
            act_str = type_to_str(actual)
            err = TntSemanticError(
                title="Type Mismatch",
                details=f"In {context}, expected type '{exp_str}', but got '{act_str}'.",
                hint="Check your variable declarations and arithmetic.",
            )
            err.print_and_exit()

    # ==========================================
    # PROGRAM & IMPORTS
    # ==========================================

    def visit_Program(self, node: Program) -> None:
        for imp in node.imports:
            self.analyze(imp)
        for decl in node.decls:
            self.analyze(decl)

    def visit_ImportSystem(self, node: ImportSystem) -> None:
        pass  # Semantic analyzer ignores imports for now

    def visit_ImportLocal(self, node: ImportLocal) -> None:
        pass

    # ==========================================
    # TOP LEVEL DECLARATIONS
    # ==========================================

    def visit_FuncDecl(self, node: FuncDecl) -> None:
        self.symtab.declare(node.name, node.return_type)

        self.symtab.enter_scope()
        self.current_function_return_type = node.return_type

        for param in node.params:
            self.symtab.declare(param.name, param.type)

        self.analyze(node.body)

        self.current_function_return_type = None
        self.symtab.exit_scope()

    def visit_StructDecl(self, node: StructDecl) -> None:
        pass

    # ==========================================
    # STATEMENTS
    # ==========================================

    def visit_Block(self, node: Block) -> None:
        self.symtab.enter_scope()
        for stmt in node.stmts:
            self.analyze(stmt)
        self.symtab.exit_scope()

    def visit_VarDeclStmt(self, node: VarDeclStmt) -> None:
        if node.init:
            init_type = self.analyze(node.init)
            self.expect_type(
                node.type, init_type, f"the initialization of '{node.name}'"
            )
        self.symtab.declare(node.name, node.type)

    def visit_ConstDeclStmt(self, node: ConstDeclStmt) -> None:
        init_type = self.analyze(node.init)
        self.expect_type(
            node.type, init_type, f"the initialization of constant '{node.name}'"
        )
        self.symtab.declare(node.name, node.type)

    def visit_IfStmt(self, node: IfStmt) -> None:
        self.analyze(node.cond)
        self.analyze(node.then_block)
        if node.else_branch:
            self.analyze(node.else_branch)

    def visit_WhileStmt(self, node: WhileStmt) -> None:
        self.analyze(node.cond)
        self.analyze(node.body)

    def visit_ForVarDecl(self, node: ForVarDecl) -> None:
        if node.init:
            init_type = self.analyze(node.init)
            self.expect_type(
                node.type, init_type, f"the for-loop init of '{node.name}'"
            )
        self.symtab.declare(node.name, node.type)

    def visit_ForStmt(self, node: ForStmt) -> None:
        # The entire for-loop gets a scope so the init variable doesn't leak
        self.symtab.enter_scope()
        if node.init:
            self.analyze(node.init)
        if node.cond:
            self.analyze(node.cond)
        if node.update:
            self.analyze(node.update)
        self.analyze(node.body)
        self.symtab.exit_scope()

    def visit_ReturnStmt(self, node: ReturnStmt) -> None:
        if node.value:
            actual_type = self.analyze(node.value)
            if self.current_function_return_type:
                self.expect_type(
                    self.current_function_return_type, actual_type, "a return statement"
                )

    def visit_BreakStmt(self, node: BreakStmt) -> None:
        pass

    def visit_ContinueStmt(self, node: ContinueStmt) -> None:
        pass

    def visit_DeferStmt(self, node: DeferStmt) -> None:
        self.analyze(node.body)

    def visit_ExprStmt(self, node: ExprStmt) -> None:
        self.analyze(node.expr)

    # --- TNT Arguments ---
    def visit_TntStmt(self, node: TntStmt) -> None:
        self.analyze(node.arg)

    def visit_TntDeref(self, node: TntDeref) -> None:
        self.symtab.lookup(node.name)

    def visit_TntString(self, node: TntString) -> None:
        pass

    def visit_TntInt(self, node: TntInt) -> None:
        pass

    def visit_TntVar(self, node: TntVar) -> None:
        self.symtab.lookup(node.name)

    # ==========================================
    # EXPRESSIONS
    # ==========================================

    def visit_Assign(self, node: Assign) -> Type:
        target_type = self.analyze(node.target)
        value_type = self.analyze(node.value)
        self.expect_type(target_type, value_type, "an assignment operation")
        return target_type

    def visit_BinOp(self, node: BinOp) -> Type:
        self.analyze(node.left)
        self.analyze(node.right)
        return PlainType("int")

    def visit_UnaryOp(self, node: UnaryOp) -> Type:
        operand_type = self.analyze(node.operand)
        if node.op == "addr":
            return RefType(operand_type)
        if node.op == "->":
            if isinstance(operand_type, RefType):
                return operand_type.inner
            # Ideally, throw an error if trying to dereference a non-pointer
        return operand_type

    def visit_Call(self, node: Call) -> Type:
        return_type = self.analyze(node.callee)
        for arg in node.args:
            self.analyze(arg)
        return return_type

    def visit_FieldAccess(self, node: FieldAccess) -> Type:
        self.analyze(node.obj)
        # Until we parse struct fields deeply, assume int
        return PlainType("int")

    def visit_Index(self, node: Index) -> Type:
        obj_type = self.analyze(node.obj)
        self.analyze(node.idx)  # Ensure index is analyzed
        if isinstance(obj_type, ArrayType):
            return obj_type.element
        if isinstance(obj_type, RefType):
            return obj_type.inner
        return PlainType("unknown")

    def visit_Ident(self, node: Ident) -> Type:
        return self.symtab.lookup(node.name)

    # --- Literals ---
    def visit_IntLit(self, node: IntLit) -> PlainType:
        return PlainType("int")

    def visit_FloatLit(self, node: FloatLit) -> PlainType:
        return PlainType("float")

    def visit_CharLit(self, node: CharLit) -> PlainType:
        return PlainType("char")

    def visit_StringLit(self, node: StringLit) -> RefType:
        # A string literal in C is usually an array of chars or a char pointer
        return RefType(PlainType("char"))

    def visit_BoolLit(self, node: BoolLit) -> PlainType:
        return PlainType("int")
