from pathlib import Path
import Levenshtein


def main() -> None:
    distances: list[int] = []
    dir = Path("./programs/")
    files = sorted(f for f in dir.glob("*.tnt") if f.is_file())

    pairs = [(files[i], files[i + 1]) for i in range(0, len(files), 2)]

    for _, (f1, f2) in enumerate(pairs, start=1):
        text1 = f1.read_text(encoding="utf-8")
        text2 = f2.read_text(encoding="utf-8")
        distance = Levenshtein.distance(text1, text2)
        distances.append(distance)
        print(f"Distance between {f1} and {f2}: {distance}")

    print(round(sum(distances) / len(distances)))
    print(f"Highest distance: {max(distances)}")
    print(f"Lowest distance: {min(distances)}")


if __name__ == "__main__":
    main()
