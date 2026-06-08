from lark import Lark

from ast_tree import AstTransformer
from ast_pretty import pretty


def main():
    source_code = ""
    with open("example.tnt") as f:
        source_code = f.read()

    grammar = ""
    with open("tnt.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr")
    parse_tree = parser.parse(source_code)

    ast = AstTransformer().transform(parse_tree)
    print(pretty(ast))


if __name__ == "__main__":
    main()
