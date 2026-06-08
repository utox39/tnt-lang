from lark import Lark


def main():
    source_code = ""
    with open("example.tnt") as f:
        source_code = f.read()

    grammar = ""
    with open("tnt.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr")
    tree = parser.parse(source_code)

    print(tree.pretty())


if __name__ == "__main__":
    main()
