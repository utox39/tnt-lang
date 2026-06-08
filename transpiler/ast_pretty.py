from __future__ import annotations

from ast_nodes import (
    ImportLocal,
    ImportSystem,
    RefType,
    PlainType,
    ArrayType,
    IntLit,
    FloatLit,
    CharLit,
    StringLit,
    BoolLit,
    Ident,
    Assign,
    BinOp,
    UnaryOp,
    Call,
    FieldAccess,
    Index,
    TntString,
    TntInt,
    TntVar,
    TntDeref,
    Block,
    VarDeclStmt,
    ConstDeclStmt,
    IfStmt,
    WhileStmt,
    ForStmt,
    ForVarDecl,
    ReturnStmt,
    BreakStmt,
    ContinueStmt,
    DeferStmt,
    TntStmt,
    ExprStmt,
    StructDecl,
    FuncDecl,
    Program,
)

_I = "  "  # one indent level


### Inline formatters ###


def fmt_type(t) -> str:
    match t:
        case RefType(inner):
            return f"ref {fmt_type(inner)}"
        case PlainType(name):
            return name
        case ArrayType(element, size):
            size_s = fmt_expr(size) if size is not None else ""
            return f"{fmt_type(element)}[{size_s}]"
        case _:
            return repr(t)


def fmt_expr(e) -> str:
    match e:
        case IntLit(value):
            return str(value)
        case FloatLit(value):
            return str(value)
        case CharLit(value):
            return value
        case StringLit(value):
            return value
        case BoolLit(value):
            return "true" if value else "false"
        case Ident(name):
            return name
        case Assign(target, value):
            return f"{fmt_expr(target)} = {fmt_expr(value)}"
        case BinOp(op, left, right):
            return f"{fmt_expr(left)} {op} {fmt_expr(right)}"
        case UnaryOp("->", operand):
            return f"->{fmt_expr(operand)}"
        case UnaryOp("addr", operand):
            return f"addr {fmt_expr(operand)}"
        case UnaryOp(op, operand):
            return f"{op}{fmt_expr(operand)}"
        case Call(callee, args):
            args_s = ", ".join(fmt_expr(a) for a in args)
            return f"{fmt_expr(callee)}({args_s})"
        case FieldAccess(obj, field):
            return f"{fmt_expr(obj)}.{field}"
        case Index(obj, idx):
            return f"{fmt_expr(obj)}[{fmt_expr(idx)}]"
        case _:
            return repr(e)


def _fmt_tnt_arg(arg) -> str:
    match arg:
        case TntString(value):
            return value
        case TntInt(value):
            return str(value)
        case TntVar(name):
            return name
        case TntDeref(name):
            return f"->{name}"
        case _:
            return repr(arg)


def _fmt_for_init(init) -> str:
    match init:
        case ForVarDecl(name, type_, init_expr):
            init_s = f" = {fmt_expr(init_expr)}" if init_expr is not None else ""
            return f"let {name} : {fmt_type(type_)}{init_s}"
        case None:
            return ""
        case _:
            return fmt_expr(init)


### Tree builder ###


def _pp_block(block: Block, depth: int) -> list[str]:
    if not block.stmts:
        return [_I * depth + "(empty)"]
    return [line for stmt in block.stmts for line in _pp(stmt, depth)]


def _pp(node, depth: int) -> list[str]:
    """Return the lines for *node* at the given indent depth."""
    pad = _I * depth

    match node:
        ### Imports ###
        case ImportSystem(path):
            return [f"{pad}ImportSystem  {path}"]
        case ImportLocal(path):
            return [f"{pad}ImportLocal   {path}"]

        ### Program ###
        case Program(imports, decls):
            lines = [f"{pad}Program"]
            lines.append(f"{pad}{_I}imports:")
            if imports:
                for imp in imports:
                    lines.extend(_pp(imp, depth + 2))
            else:
                lines.append(f"{pad}{_I * 2}(none)")
            lines.append(f"{pad}{_I}decls:")
            for decl in decls:
                lines.extend(_pp(decl, depth + 2))
            return lines

        ### Struct ###
        case StructDecl(name, fields):
            lines = [f"{pad}StructDecl  {name}"]
            for f in fields:
                lines.append(f"{pad}{_I}{f.name} : {fmt_type(f.type)}")
            return lines

        ### Function ###
        case FuncDecl(name, params, return_type, body):
            params_s = ", ".join(f"{p.name}: {fmt_type(p.type)}" for p in params)
            lines = [f"{pad}FuncDecl  {name}({params_s}) -> {fmt_type(return_type)}"]
            lines.extend(_pp_block(body, depth + 1))
            return lines

        ### Variable / constant declarations ###
        case VarDeclStmt(name, type_, init):
            init_s = f" = {fmt_expr(init)}" if init is not None else ""
            return [f"{pad}VarDeclStmt  {name} : {fmt_type(type_)}{init_s}"]

        case ConstDeclStmt(name, type_, init):
            return [
                f"{pad}ConstDeclStmt  {name} : {fmt_type(type_)} = {fmt_expr(init)}"
            ]

        ### Control flow ###
        case IfStmt(cond, then_block, else_branch):
            lines = [f"{pad}IfStmt  {fmt_expr(cond)}"]
            lines.append(f"{pad}{_I}then:")
            lines.extend(_pp_block(then_block, depth + 2))
            if else_branch is None:
                lines.append(f"{pad}{_I}else:  -")
            else:
                lines.append(f"{pad}{_I}else:")
                match else_branch:
                    case IfStmt():
                        lines.extend(_pp(else_branch, depth + 2))
                    case Block():
                        lines.extend(_pp_block(else_branch, depth + 2))
            return lines

        case WhileStmt(cond, body):
            lines = [f"{pad}WhileStmt  {fmt_expr(cond)}"]
            lines.extend(_pp_block(body, depth + 1))
            return lines

        case ForStmt(init, cond, update, body):
            update_s = fmt_expr(update) if update is not None else ""
            lines = [
                f"{pad}ForStmt  {_fmt_for_init(init)} ; {fmt_expr(cond)} ; {update_s}"
            ]
            lines.extend(_pp_block(body, depth + 1))
            return lines

        case ReturnStmt(value):
            value_s = f"  {fmt_expr(value)}" if value is not None else "  (void)"
            return [f"{pad}ReturnStmt{value_s}"]

        case BreakStmt():
            return [f"{pad}BreakStmt"]

        case ContinueStmt():
            return [f"{pad}ContinueStmt"]

        ### Special statements ###
        case DeferStmt(body):
            lines = [f"{pad}DeferStmt"]
            match body:
                case Block():
                    lines.extend(_pp_block(body, depth + 1))
                case ExprStmt():
                    lines.extend(_pp(body, depth + 1))
            return lines

        case TntStmt(arg):
            return [f"{pad}TntStmt  {_fmt_tnt_arg(arg)}"]

        case ExprStmt(expr):
            return [f"{pad}ExprStmt  {fmt_expr(expr)}"]

        case _:
            return [f"{pad}{repr(node)}"]


def pretty(node) -> str:
    """Return a human-readable, indented string representation of an AST node."""
    return "\n".join(_pp(node, 0))
