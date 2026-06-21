import os

from lark import Lark, ParseTree


def get_used_constructs(parse_tree: ParseTree) -> set:
    constructs = set()
    for subtree in parse_tree.iter_subtrees():
        constructs.add(subtree.data)
    return constructs


def main() -> None:
    grammar = ""
    with open("../../transpiler/tnt.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr", propagate_positions=True)

    used_rules: set = set()
    all_rules: set = set(parser.rules)

    for e in os.scandir("./programs/"):
        if e.is_file():
            with open(e.path, "r") as f:
                try:
                    parse_tree = parser.parse(f.read())
                    used_rules.update(get_used_constructs(parse_tree))
                except Exception:
                    pass

    coverage: float = (len(used_rules) / len(all_rules)) * 100
    print(f"Used: {len(used_rules)} on {len(all_rules)} - {coverage:.2f}%")


if __name__ == "__main__":
    main()
