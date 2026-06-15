from typing import Any

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


class CodeGenerator:
    def __init__(self, type_map: dict[int, Type]) -> None:
        self.indent_level: int = 0
        self.defer_stack: list[list[str]] = []

        # Pull in the resolved AST types from the Semantic Analyzer
        self.type_map = type_map

    def generate(self, node: Any) -> str:
        if node is None:
            return ""

        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Any) -> str:
        raise NotImplementedError(
            f"Compiler Bug: No C-generation defined for {type(node).__name__}"
        )

    def indent(self) -> str:
        return "    " * self.indent_level

    def fmt_type(self, t: Type | None) -> str:
        if t is None:
            return "void"
        elif isinstance(t, PlainType):
            return t.name
        elif isinstance(t, RefType):
            return f"{self.fmt_type(t.inner)}*"
        elif isinstance(t, ArrayType):
            return f"{self.fmt_type(t.element)}*"
        return "void"

    # ==========================================
    # PROGRAM & IMPORTS
    # ==========================================

    def visit_Program(self, node: Program) -> str:
        out: list[str] = []

        out.append("// ==========================================")
        out.append("// TNT OS API & Standard Library Prelude")
        out.append("// ==========================================")
        out.append("#include <stdint.h>")
        out.append("#include <stdbool.h>")
        out.append("#include <stdlib.h>\n")  # Added for exit()

        for imp in node.imports:
            out.append(self.generate(imp))

        if node.imports:
            out.append("")

        for decl in node.decls:
            out.append(self.generate(decl))
            out.append("")

        return "\n".join(out)

    def visit_ImportSystem(self, node: ImportSystem) -> str:
        return f"#include <{node.path}>"

    def visit_ImportLocal(self, node: ImportLocal) -> str:
        return f'#include "{node.path}"'

    # ==========================================
    # TOP LEVEL DECLARATIONS
    # ==========================================

    def visit_FuncDecl(self, node: FuncDecl) -> str:
        out: list[str] = []
        ret_type = self.fmt_type(node.return_type)
        params = ", ".join(f"{self.fmt_type(p.type)} {p.name}" for p in node.params)

        out.append(f"{ret_type} {node.name}({params}) ")
        out.append(self.generate(node.body))
        return "".join(out)

    def visit_StructDecl(self, node: StructDecl) -> str:
        out: list[str] = []
        out.append(f"typedef struct {node.name} {{\n")
        self.indent_level += 1

        node_fields = getattr(node, "fields", getattr(node, "decls", []))
        for field in node_fields:
            out.append(f"{self.indent()}{self.fmt_type(field.type)} {field.name};\n")

        self.indent_level -= 1
        out.append(f"}} {node.name};")
        return "".join(out)

    # ==========================================
    # STATEMENTS
    # ==========================================

    def visit_Block(self, node: Block) -> str:
        out: list[str] = ["{\n"]
        self.indent_level += 1

        self.defer_stack.append([])

        for stmt in node.stmts:
            stmt_code = self.generate(stmt)
            if stmt_code:
                if not isinstance(stmt, DeferStmt) and not stmt_code.endswith(
                    (";\n", "}\n", ";")
                ):
                    stmt_code += ";"
                out.append(f"{self.indent()}{stmt_code}\n")

        current_defers = self.defer_stack.pop()
        for defer_code in reversed(current_defers):
            out.append(f"{self.indent()}// [defer executed at block end]\n")
            out.append(f"{self.indent()}{defer_code}\n")

        self.indent_level -= 1
        out.append(f"{self.indent()}}}")
        return "".join(out)

    def visit_VarDeclStmt(self, node: VarDeclStmt) -> str:
        if isinstance(node.type, ArrayType):
            elem = self.fmt_type(node.type.element)
            size_str = self.generate(node.type.size) if node.type.size else ""
            base = f"{elem} {node.name}[{size_str}]"
        else:
            base = f"{self.fmt_type(node.type)} {node.name}"
        if node.init:
            return f"{base} = {self.generate(node.init)};"
        return f"{base};"

    def visit_ConstDeclStmt(self, node: ConstDeclStmt) -> str:
        if isinstance(node.type, ArrayType):
            elem = self.fmt_type(node.type.element)
            size_str = self.generate(node.type.size) if node.type.size else ""
            return f"const {elem} {node.name}[{size_str}] = {self.generate(node.init)};"
        return f"const {self.fmt_type(node.type)} {node.name} = {self.generate(node.init)};"

    def visit_IfStmt(self, node: IfStmt) -> str:
        cond_code = self.generate(node.cond)
        if cond_code.startswith("(") and cond_code.endswith(")"):
            cond_code = cond_code[1:-1]

        out = [f"if ({cond_code}) {self.generate(node.then_block)}"]
        if node.else_branch:
            out.append(f" else {self.generate(node.else_branch)}")
        return "".join(out)

    def visit_WhileStmt(self, node: WhileStmt) -> str:
        cond_code = self.generate(node.cond)
        if cond_code.startswith("(") and cond_code.endswith(")"):
            cond_code = cond_code[1:-1]

        return f"while ({cond_code}) {self.generate(node.body)}"

    def visit_ForVarDecl(self, node: ForVarDecl) -> str:
        base = f"{self.fmt_type(node.type)} {node.name}"
        if node.init:
            return f"{base} = {self.generate(node.init)}"
        return base

    def visit_ForStmt(self, node: ForStmt) -> str:
        init_code = self.generate(node.init) if node.init else ""
        cond_code = self.generate(node.cond) if node.cond else ""
        update_code = self.generate(node.update) if node.update else ""
        return (
            f"for ({init_code}; {cond_code}; {update_code}) {self.generate(node.body)}"
        )

    def visit_ReturnStmt(self, node: ReturnStmt) -> str:
        out: list[str] = []

        # Flatten and execute all active defers across all open scopes
        for scope_defers in reversed(self.defer_stack):
            for defer_code in reversed(scope_defers):
                out.append("// [defer executed via return]")
                out.append(defer_code)

        val = f" {self.generate(node.value)}" if node.value else ""
        out.append(f"return{val};")

        # Join with a newline and the current indent to align perfectly
        return f"\n{self.indent()}".join(out)

    def visit_BreakStmt(self, node: BreakStmt) -> str:
        _ = node
        return "break;"

    def visit_ContinueStmt(self, node: ContinueStmt) -> str:
        _ = node
        return "continue;"

    def visit_DeferStmt(self, node: DeferStmt) -> str:
        defer_code = self.generate(node.body)
        if not defer_code.endswith(";"):
            defer_code += ";"
        self.defer_stack[-1].append(defer_code)
        return ""

    def visit_ExprStmt(self, node: ExprStmt) -> str:
        return f"{self.generate(node.expr)};"

    # --- TNT Arguments ---
    def visit_TntStmt(self, node: TntStmt) -> str:
        arg = node.arg
        out: list[str] = []

        # Polymorphic generation based on the OS API requirements
        if isinstance(arg, TntInt):
            out.append(f"exit({arg.value});")
        elif isinstance(arg, TntString):
            out.append(f'fprintf(stderr, "%s\\n", {arg.value});')
            out.append("exit(1);")
        elif isinstance(arg, TntDeref):
            out.append(f'fprintf(stderr, "%d\\n", *{arg.name});')
            out.append("exit(1);")
        elif isinstance(arg, TntVar):
            out.append(f"exit({arg.name});")
        else:
            out.append(f"(void)({self.generate(arg)});")

        return f"\n{self.indent()}".join(out)

    def visit_TntDeref(self, node: TntDeref) -> str:
        return f"*{node.name}"

    def visit_TntString(self, node: TntString) -> str:
        return node.value

    def visit_TntInt(self, node: TntInt) -> str:
        return str(node.value)

    def visit_TntVar(self, node: TntVar) -> str:
        return node.name

    # ==========================================
    # EXPRESSIONS
    # ==========================================

    def visit_Assign(self, node: Assign) -> str:
        return f"{self.generate(node.target)} = {self.generate(node.value)}"

    def visit_BinOp(self, node: BinOp) -> str:
        return f"({self.generate(node.left)} {node.op} {self.generate(node.right)})"

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        op_str = node.op
        if op_str == "addr":
            op_str = "&"
        elif op_str == "->":
            op_str = "*"

        return f"({op_str}{self.generate(node.operand)})"

    def visit_Call(self, node: Call) -> str:
        args = ", ".join(self.generate(arg) for arg in node.args)
        return f"{self.generate(node.callee)}({args})"

    def visit_FieldAccess(self, node: FieldAccess) -> str:
        obj_code = self.generate(node.obj)
        field_name = (
            node.field
            if isinstance(node.field, str)
            else getattr(node.field, "name", str(node.field))
        )

        obj_type = self.type_map.get(id(node.obj))

        if isinstance(obj_type, RefType):
            return f"{obj_code}->{field_name}"

        return f"{obj_code}.{field_name}"

    def visit_Index(self, node: Index) -> str:
        return f"{self.generate(node.obj)}[{self.generate(node.idx)}]"

    def visit_ArrayInit(self, node: ArrayInit) -> str:
        elements = ", ".join(self.generate(e) for e in node.elements)
        return f"{{{elements}}}"

    def visit_CastExpr(self, node: CastExpr) -> str:
        c_type = self.fmt_type(node.target_type)
        return f"({c_type})({self.generate(node.expr)})"

    def visit_Ident(self, node: Ident) -> str:
        return node.name

    # --- Literals ---
    def visit_IntLit(self, node: IntLit) -> str:
        return str(node.value)

    def visit_FloatLit(self, node: FloatLit) -> str:
        return str(node.value)

    def visit_CharLit(self, node: CharLit) -> str:
        return node.value

    def visit_StringLit(self, node: StringLit) -> str:
        return node.value

    def visit_BoolLit(self, node: BoolLit) -> str:
        return "true" if node.value else "false"
