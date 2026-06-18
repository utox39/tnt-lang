import argparse

from lark import Lark

from ast_tree import AstTransformer
from semantic import SemanticAnalyzer
from codegen import CodeGenerator


def main():
    parser = argparse.ArgumentParser(description="TNT language transpiler.")
    parser.add_argument("filepath", type=str, help="The .tnt file path")
    parser.add_argument("--no-color", action="store_true", help="Disable colored error output")
    args = parser.parse_args()
    filepath = args.filepath

    source_code = ""
    with open(filepath) as f:
        source_code = f.read()

    grammar = ""
    with open("tnt.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    parse_tree = parser.parse(source_code)

    ast = AstTransformer().transform(parse_tree)

    analyzer = SemanticAnalyzer(source_lines=source_code.splitlines(), colored=not args.no_color)
    analyzer.analyze(ast)
    print("== INFO == Semantic analysis passed")

    print("== INFO == Generating C code...")
    # Pass the populated type_map into the code generator!
    generator = CodeGenerator(analyzer.type_map)
    c_code = generator.generate(ast)

    with open("output.c", "w") as f:
        f.write(c_code)

    print("== INFO == Compilation successful. Output written to 'output.c'.")


if __name__ == "__main__":
    main()
