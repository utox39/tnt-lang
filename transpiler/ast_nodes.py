from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

# === TYPES ===


@dataclass
class RefType:
    """ref <inner>  —  pointer to inner type."""

    inner: Type


@dataclass
class PlainType:
    """int | char | void | float | <CustomIdent>"""

    name: str


@dataclass
class ArrayType:
    """<base_type> [ <size>? ]"""

    element: PlainType
    size: Optional[Expr]


@dataclass
class CType:
    """Opaque return type for c.* external calls — bypasses type checking."""

    pass


Type = Union[RefType, PlainType, ArrayType, CType]


# === EXPRESSIONS ===


@dataclass
class IntLit:
    value: int


@dataclass
class FloatLit:
    value: float


@dataclass
class CharLit:
    """Raw character literal string including the surrounding quotes, e.g. \"'a'\"."""

    value: str


@dataclass
class StringLit:
    """Raw string literal including the surrounding quotes, e.g. '\"hello\"'."""

    value: str


@dataclass
class BoolLit:
    value: bool


@dataclass
class Ident:
    name: str


@dataclass
class Assign:
    """<target> = <value>  (lvalue validity checked by the code generator)."""

    target: Expr
    value: Expr


@dataclass
class BinOp:
    """
    Binary operation.

    op values:
        logical   : "||"  "&&"
        equality  : "=="  "!="
        relational: "<"  ">"  "<="  ">="
        arithmetic: "+"  "-"  "*"  "/"  "%"
    """

    op: str
    left: Expr
    right: Expr


@dataclass
class UnaryOp:
    """
    Unary operation.

    op values:
        "-"    arithmetic negation
        "!"    logical not
        "->"   pointer dereference
        "addr" address-of
    """

    op: str
    operand: Expr


@dataclass
class Call:
    """<callee>(<args>)"""

    callee: Expr
    args: list[Expr]


@dataclass
class FieldAccess:
    """<obj>.<field>"""

    obj: Expr
    field: str


@dataclass
class Index:
    """<obj>[<idx>]"""

    obj: Expr
    idx: Expr


@dataclass
class CastExpr:
    """<expr> as <type>"""

    expr: Expr
    target_type: Type


@dataclass
class ArrayInit:
    """[expr, expr, ...]"""

    elements: list[Expr]


@dataclass
class TypeArg:
    """A type name used as a call argument (e.g., c.sizeof(float))."""

    type: Type


Expr = Union[
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
    CastExpr,
    ArrayInit,
    TypeArg,
]


# === TNT ARGUMENT ===


@dataclass
class TntString:
    """tnt "literal" ;"""

    value: str


@dataclass
class TntInt:
    """tnt 1 ;"""

    value: int


@dataclass
class TntVar:
    """tnt var_name ;"""

    name: str


@dataclass
class TntDeref:
    """tnt ->ptr_name ;"""

    name: str


TntArg = Union[TntString, TntInt, TntVar, TntDeref]


# === STATEMENTS ===


@dataclass
class Block:
    stmts: list[Stmt]


@dataclass
class VarDeclStmt:
    """let <name> : <type> (= <init>)? ;"""

    name: str
    type: Type
    init: Optional[Expr]


@dataclass
class ConstDeclStmt:
    """const <name> : <type> = <init> ;"""

    name: str
    type: Type
    init: Expr


@dataclass
class IfStmt:
    """if (<cond>) <then_block> (else (<else_branch>))?"""

    cond: Expr
    then_block: Block
    else_branch: Optional[Union[IfStmt, Block]]


@dataclass
class WhileStmt:
    """while (<cond>) <body>"""

    cond: Expr
    body: Block


@dataclass
class ForVarDecl:
    """
    Variable declaration in a for-init slot: let <name> : <type> (= <init>)?
    Has no trailing semicolon — the for_stmt rule owns the separators.
    """

    name: str
    type: Type
    init: Optional[Expr]


# ForInit: a variable declaration, an expression, or absent (None).
ForInit = Optional[Union[ForVarDecl, Expr]]

# ForUpdate: an expression or absent (None).
ForUpdate = Optional[Expr]


@dataclass
class ForStmt:
    """for (<init> ; <cond> ; <update>) <body>"""

    init: ForInit
    cond: Expr
    update: ForUpdate
    body: Block


@dataclass
class ReturnStmt:
    """return <value>? ;"""

    value: Optional[Expr]


@dataclass
class BreakStmt:
    """break ;"""


@dataclass
class ContinueStmt:
    """continue ;"""


@dataclass
class DeferStmt:
    """defer (<block> | <expr_stmt>)"""

    body: Union[Block, ExprStmt]


@dataclass
class TntStmt:
    """tnt <arg> ;"""

    arg: TntArg


@dataclass
class ExprStmt:
    """<expr> ;"""

    expr: Expr


Stmt = Union[
    VarDeclStmt,
    ConstDeclStmt,
    IfStmt,
    WhileStmt,
    ForStmt,
    ReturnStmt,
    BreakStmt,
    ContinueStmt,
    DeferStmt,
    TntStmt,
    ExprStmt,
]


# === TOP-LEVEL DECLARATIONS ===


@dataclass
class FieldDecl:
    """<name> : <type> ;  (inside a struct body)"""

    name: str
    type: Type


@dataclass
class StructDecl:
    """struct <name> { <fields>* } ;"""

    name: str
    fields: list[FieldDecl]


@dataclass
class Param:
    """<name> : <type>  (function parameter)"""

    name: str
    type: Type


@dataclass
class FuncDecl:
    """fn <name>(<params>) -> <return_type> <body>"""

    name: str
    params: list[Param]
    return_type: Type
    body: Block


TopLevelDecl = Union[StructDecl, FuncDecl]


# === IMPORTS ===


@dataclass
class ImportLocal:
    """import local ./path/to/file.h"""

    path: str


@dataclass
class ImportSystem:
    """import stdio.h"""

    path: str


Import = Union[ImportLocal, ImportSystem]


# === PROGRAM (root) ===


@dataclass
class Program:
    imports: list[Import]
    decls: list[TopLevelDecl]
