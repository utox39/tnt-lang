import sys
from typing import Any, NoReturn

from ast_nodes import (
    ArrayInit,
    ArrayType,
    Assign,
    BinOp,
    Block,
    BoolLit,
    BreakStmt,
    Call,
    CastExpr,
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


class TntSemanticError(Exception):
    def __init__(
        self,
        title: str,
        details: str,
        hint: str = "",
        line: Any = "?",
        col: Any = "?",
        source_line: str | None = None,
        colored: bool = True,
    ) -> None:
        self.title = title
        self.details = details
        self.hint = hint
        self.line = line
        self.col = col
        self.source_line = source_line
        self.colored = colored

    def print_and_exit(self) -> NoReturn:
        red = "\033[1;31m" if self.colored else ""
        yellow = "\033[1;33m" if self.colored else ""
        blue = "\033[1;36m" if self.colored else ""
        reset = "\033[0m" if self.colored else ""

        location = f"{blue}[Line {self.line}, Col {self.col}]{reset}"

        print(f"\n{red}Error: {self.title}{reset} {location}")
        print(f"    {self.details}")

        if self.source_line is not None:
            gutter = f"{self.line}"
            print(f"\n  {gutter} | {self.source_line}")
            col = self.col if isinstance(self.col, int) else 1
            caret_pad = " " * (len(gutter) + 4 + col)
            print(f"{caret_pad}^")

        if self.hint:
            print(f"\n{yellow}Hint:{reset} {self.hint}")
        print()
        sys.exit(1)


def type_to_str(t: Type | None) -> str:
    if t is None:
        return "void"
    elif isinstance(t, PlainType):
        return t.name
    elif isinstance(t, RefType):
        return f"ref {type_to_str(t.inner)}"
    else:  # It must be ArrayType
        return f"{type_to_str(t.element)}[]"


# ==========================================
# SYMBOL TABLE
# ==========================================


class SymbolTable:
    def __init__(self, source_lines: list[str] | None = None, colored: bool = True) -> None:
        self.scopes: list[dict[str, Type]] = [{}]
        self.structs: dict[str, dict[str, Type]] = {}
        self.source_lines = source_lines
        self.colored = colored

    def enter_scope(self) -> None:
        self.scopes.append({})

    def exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise RuntimeError("Compiler Bug: Attempted to pop the global scope.")

    def declare(self, name: str, var_type: Type, node: Any = None) -> None:
        current_scope = self.scopes[-1]
        if name in current_scope:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Duplicate Declaration",
                details=f"The identifier '{name}' is already defined in this scope.",
                hint="Try renaming this variable.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()
        current_scope[name] = var_type

    def lookup(self, name: str, node: Any = None) -> Type:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        line = getattr(node, "line", "?")
        err = TntSemanticError(
            title="Undefined Identifier",
            details=f"You tried to use '{name}', but it hasn't been declared.",
            hint=f"Did you forget to declare it with 'let {name}: type;'?",
            line=line,
            col=getattr(node, "column", "?"),
            source_line=self.source_lines[line - 1]
            if (self.source_lines and isinstance(line, int))
            else None,
            colored=self.colored,
        )
        err.print_and_exit()

    def define_struct(
        self, name: str, fields: dict[str, Type], node: Any = None
    ) -> None:
        if name in self.structs:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Duplicate Struct",
                details=f"A struct named '{name}' is already defined.",
                hint="Rename this struct.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()
        self.structs[name] = fields

    def get_struct(self, name: str, node: Any = None) -> dict[str, Type]:
        if name not in self.structs:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Undefined Struct",
                details=f"You tried to use struct '{name}', but it hasn't been defined.",
                hint="Ensure the struct is declared before you use it.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()
        return self.structs[name]


# ==========================================
# SEMANTIC ANALYZER
# ==========================================


class SemanticAnalyzer:
    def __init__(self, source_lines: list[str] | None = None, colored: bool = True) -> None:
        self.source_lines = source_lines
        self.colored = colored
        self.symtab = SymbolTable(source_lines=source_lines, colored=colored)
        self.current_function_return_type: Type | None = None
        self.loop_depth: int = 0

        self.type_map: dict[int, Type] = {}
        self.symtab.declare("printf", PlainType("void"))

    def analyze(self, node: Any) -> Any:
        if node is None:
            return None

        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)

        resolved_type = visitor(node)

        if resolved_type is not None:
            self.type_map[id(node)] = resolved_type

        return resolved_type

    def generic_visit(self, node: Any) -> Any:
        raise NotImplementedError(
            f"Compiler Bug: No visit method defined for {type(node).__name__}"
        )

    def expect_type(
        self, expected: Type, actual: Type, context: str, node: Any
    ) -> None:
        if expected != actual:
            exp_str = type_to_str(expected)
            act_str = type_to_str(actual)
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Type Mismatch",
                details=f"In {context}, expected type '{exp_str}', but got '{act_str}'.",
                hint="Check your variable declarations and arithmetic.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
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
        _ = node

    def visit_ImportLocal(self, node: ImportLocal) -> None:
        _ = node

    # ==========================================
    # TOP LEVEL DECLARATIONS
    # ==========================================

    def visit_FuncDecl(self, node: FuncDecl) -> None:
        self.symtab.declare(node.name, node.return_type, node)

        self.symtab.enter_scope()
        self.current_function_return_type = node.return_type

        for param in node.params:
            self.symtab.declare(param.name, param.type, node)

        self.analyze(node.body)

        self.current_function_return_type = None
        self.symtab.exit_scope()

    def visit_StructDecl(self, node: StructDecl) -> None:
        fields: dict[str, Type] = {}
        node_fields = getattr(node, "fields", getattr(node, "decls", []))

        for field in node_fields:
            if field.name in fields:
                line = getattr(node, "line", "?")
                err = TntSemanticError(
                    title="Duplicate Struct Field",
                    details=f"Field '{field.name}' is defined multiple times in '{node.name}'.",
                    hint="Ensure all fields within a struct have unique names.",
                    line=line,
                    col=getattr(node, "column", "?"),
                    source_line=self.source_lines[line - 1]
                    if (self.source_lines and isinstance(line, int))
                    else None,
                    colored=self.colored,
                )
                err.print_and_exit()
            fields[field.name] = field.type

        self.symtab.define_struct(node.name, fields, node)

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
            if isinstance(node.type, ArrayType) and isinstance(init_type, ArrayType):
                if node.type.element != init_type.element:
                    line = getattr(node, "line", "?")
                    err = TntSemanticError(
                        title="Type Mismatch",
                        details=(
                            f"Array element type mismatch in the initialization of '{node.name}': "
                            f"expected '{type_to_str(node.type.element)}', "
                            f"got '{type_to_str(init_type.element)}'."
                        ),
                        hint="Ensure the array literal elements match the declared element type.",
                        line=line,
                        col=getattr(node, "column", "?"),
                        source_line=self.source_lines[line - 1]
                        if (self.source_lines and isinstance(line, int))
                        else None,
                        colored=self.colored,
                    )
                    err.print_and_exit()
            else:
                self.expect_type(
                    node.type, init_type, f"the initialization of '{node.name}'", node
                )
        self.symtab.declare(node.name, node.type, node)

    def visit_ConstDeclStmt(self, node: ConstDeclStmt) -> None:
        init_type = self.analyze(node.init)
        self.expect_type(
            node.type, init_type, f"the initialization of constant '{node.name}'", node
        )
        self.symtab.declare(node.name, node.type, node)

    def visit_IfStmt(self, node: IfStmt) -> None:
        self.analyze(node.cond)
        self.analyze(node.then_block)
        if node.else_branch:
            self.analyze(node.else_branch)

    def visit_WhileStmt(self, node: WhileStmt) -> None:
        self.analyze(node.cond)
        self.loop_depth += 1
        self.analyze(node.body)
        self.loop_depth -= 1

    def visit_ForVarDecl(self, node: ForVarDecl) -> None:
        if node.init:
            init_type = self.analyze(node.init)
            self.expect_type(
                node.type, init_type, f"the for-loop init of '{node.name}'", node
            )
        self.symtab.declare(node.name, node.type, node)

    def visit_ForStmt(self, node: ForStmt) -> None:
        self.symtab.enter_scope()
        if node.init:
            self.analyze(node.init)
        if node.cond:
            self.analyze(node.cond)
        if node.update:
            self.analyze(node.update)

        self.loop_depth += 1
        self.analyze(node.body)
        self.loop_depth -= 1

        self.symtab.exit_scope()

    def visit_ReturnStmt(self, node: ReturnStmt) -> None:
        if node.value:
            actual_type = self.analyze(node.value)
            if self.current_function_return_type:
                self.expect_type(
                    self.current_function_return_type,
                    actual_type,
                    "a return statement",
                    node,
                )

    def visit_BreakStmt(self, node: BreakStmt) -> None:
        if self.loop_depth <= 0:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Invalid Control Flow",
                details="A 'break' statement can only be used inside a loop.",
                hint="Remove this statement or ensure it is wrapped in a 'while' or 'for' block.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

    def visit_ContinueStmt(self, node: ContinueStmt) -> None:
        if self.loop_depth <= 0:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Invalid Control Flow",
                details="A 'continue' statement can only be used inside a loop.",
                hint="Remove this statement or ensure it is wrapped in a 'while' or 'for' block.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

    def visit_DeferStmt(self, node: DeferStmt) -> None:
        self.analyze(node.body)

    def visit_ExprStmt(self, node: ExprStmt) -> None:
        self.analyze(node.expr)

    # --- TNT Arguments ---
    def visit_TntStmt(self, node: TntStmt) -> None:
        self.analyze(node.arg)

    def visit_TntDeref(self, node: TntDeref) -> None:
        self.symtab.lookup(node.name, node)

    def visit_TntString(self, node: TntString) -> None:
        _ = node

    def visit_TntInt(self, node: TntInt) -> None:
        _ = node

    def visit_TntVar(self, node: TntVar) -> None:
        self.symtab.lookup(node.name, node)

    # ==========================================
    # EXPRESSIONS
    # ==========================================

    def visit_Assign(self, node: Assign) -> Type:
        target_type = self.analyze(node.target)
        value_type = self.analyze(node.value)
        self.expect_type(target_type, value_type, "an assignment operation", node)
        return target_type

    def visit_BinOp(self, node: BinOp) -> Type:
        left_type = self.analyze(node.left)
        right_type = self.analyze(node.right)

        def is_type(t: Type, name: str) -> bool:
            return isinstance(t, PlainType) and t.name == name

        if node.op in ["==", "!=", "<", ">", "<=", ">=", "&&", "||"]:
            return PlainType("bool")

        if node.op in ["+", "-", "*", "/", "%"]:
            if left_type == right_type:
                return left_type

            if (is_type(left_type, "int") and is_type(right_type, "float")) or (
                is_type(left_type, "float") and is_type(right_type, "int")
            ):
                if node.op == "%":
                    line = getattr(node, "line", "?")
                    err = TntSemanticError(
                        title="Illegal Modulo",
                        details="The modulo operator '%' cannot be used with floating-point numbers.",
                        hint="Both operands must be integers.",
                        line=line,
                        col=getattr(node, "column", "?"),
                        source_line=self.source_lines[line - 1]
                        if (self.source_lines and isinstance(line, int))
                        else None,
                        colored=self.colored,
                    )
                    err.print_and_exit()
                return PlainType("float")

            line = getattr(node, "line", "?")
            exp_str = type_to_str(left_type)
            act_str = type_to_str(right_type)
            err = TntSemanticError(
                title="Invalid Binary Operation",
                details=f"Cannot apply operator '{node.op}' between '{exp_str}' and '{act_str}'.",
                hint="You may need to explicitly cast one of the variables using the 'as' keyword.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        return PlainType("int")

    def visit_UnaryOp(self, node: UnaryOp) -> Type:
        operand_type = self.analyze(node.operand)
        if node.op == "addr":
            return RefType(operand_type)
        if node.op == "->":
            if isinstance(operand_type, RefType):
                return operand_type.inner
        return operand_type

    def visit_Call(self, node: Call) -> Type:
        return_type = self.analyze(node.callee)
        for arg in node.args:
            self.analyze(arg)
        return return_type

    def visit_FieldAccess(self, node: FieldAccess) -> Type:
        obj_type = self.analyze(node.obj)

        base_type = obj_type
        if isinstance(base_type, RefType):
            base_type = base_type.inner

        if not isinstance(base_type, PlainType):
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Invalid Field Access",
                details=f"Cannot access fields on a non-struct type '{type_to_str(obj_type)}'.",
                hint="Ensure the variable is a valid struct or a reference to a struct.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        struct_name = base_type.name
        struct_def = self.symtab.get_struct(struct_name, node)

        field_name = (
            node.field
            if isinstance(node.field, str)
            else getattr(node.field, "name", str(node.field))
        )

        if field_name not in struct_def:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Unknown Field",
                details=f"Struct '{struct_name}' has no field named '{field_name}'.",
                hint=f"Check the definition of '{struct_name}' for valid fields.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        return struct_def[field_name]

    def visit_Index(self, node: Index) -> Type:
        obj_type = self.analyze(node.obj)
        self.analyze(node.idx)
        if isinstance(obj_type, ArrayType):
            return obj_type.element
        if isinstance(obj_type, RefType):
            inner = obj_type.inner
            if isinstance(inner, ArrayType):
                return inner.element
            return inner
        return PlainType("unknown")

    def visit_CastExpr(self, node: CastExpr) -> Type:
        expr_type = self.analyze(node.expr)
        target_type = node.target_type

        def is_struct(t: Type) -> bool:
            return isinstance(t, PlainType) and t.name in self.symtab.structs

        if is_struct(expr_type) or is_struct(target_type):
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Invalid Cast",
                details=f"Cannot cast from '{type_to_str(expr_type)}' to '{type_to_str(target_type)}'.",
                hint="Structs cannot be directly cast. You must access their individual fields.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        return target_type

    def visit_ArrayInit(self, node: ArrayInit) -> ArrayType:
        if not node.elements:
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Empty Array Literal",
                details="Array literals must contain at least one element.",
                hint="Add at least one element to the array literal, e.g. [0].",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        first_type = self.analyze(node.elements[0])
        if not isinstance(first_type, PlainType):
            line = getattr(node, "line", "?")
            err = TntSemanticError(
                title="Invalid Array Element Type",
                details=f"Array elements must be plain types, but got '{type_to_str(first_type)}'.",
                hint="Array literals only support plain types such as int, char, or float.",
                line=line,
                col=getattr(node, "column", "?"),
                source_line=self.source_lines[line - 1]
                if (self.source_lines and isinstance(line, int))
                else None,
                colored=self.colored,
            )
            err.print_and_exit()

        for i, elem in enumerate(node.elements[1:], 1):
            elem_type = self.analyze(elem)
            self.expect_type(first_type, elem_type, f"array element {i}", elem)

        return ArrayType(element=first_type, size=IntLit(value=len(node.elements)))

    def visit_Ident(self, node: Ident) -> Type:
        return self.symtab.lookup(node.name, node)

    # --- Literals ---
    def visit_IntLit(self, node: IntLit) -> PlainType:
        _ = node
        return PlainType("int")

    def visit_FloatLit(self, node: FloatLit) -> PlainType:
        _ = node
        return PlainType("float")

    def visit_CharLit(self, node: CharLit) -> PlainType:
        _ = node
        return PlainType("char")

    def visit_StringLit(self, node: StringLit) -> RefType:
        _ = node
        return RefType(PlainType("char"))

    def visit_BoolLit(self, node: BoolLit) -> PlainType:
        _ = node
        return PlainType("bool")
