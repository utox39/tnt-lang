### One agent pattern ###

import logging
import os
import re
import shutil
import subprocess

from pathlib import Path

import ollama

# ============================================================
# Configuration
# ============================================================

OLLAMA_HOST = os.environ["TNT_OLLAMA_HOST"]
OLLAMA_MODEL = os.environ["TNT_OLLAMA_MODEL"]
NUM_PROGRAMS = 100
MAX_ATTEMPTS = 3

# ============================================================
# Paths
# ============================================================

AGENTS_DIR = Path(__file__).parent.resolve()
TRANSPILER_DIR = AGENTS_DIR.parent / "transpiler"
PROGRAMS_DIR = AGENTS_DIR / "programs"
OUTPUT_DIR = AGENTS_DIR / "output"
LOG_FILE = AGENTS_DIR / "agent_run.log"

GRAMMAR = (TRANSPILER_DIR / "tnt.lark").read_text()
EXAMPLE = (TRANSPILER_DIR / "example.tnt").read_text()


# ============================================================
# Setup
# ============================================================


def setup() -> None:
    PROGRAMS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ============================================================
# LLM
# ============================================================

client: ollama.Client | None = None


def get_client() -> ollama.Client:
    global client
    if client is None:
        client = ollama.Client(host=OLLAMA_HOST)
    return client


def call_llm(prompt: str) -> str:
    logging.info("=== PROMPT ===\n%s", prompt)
    # TODO: handle excepitons
    response = get_client().generate(model=OLLAMA_MODEL, prompt=prompt)
    # A little bit janky but it will do the work until we handle the excepitons
    text = response.response if (response.response) else ""
    logging.info("=== RESPONSE ===\n%s", text)
    return text


def strip_fences(text: str) -> str:
    match = re.search(r"```(?:tnt)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


# ============================================================
# Prompts
# ============================================================


def build_generation_prompt(program_number: int, previous_program: str) -> str:
    return f"""You are a TNT language programmer. Generate a valid, simple, self-contained TNT program.

TNT Language Grammar:
```
{GRAMMAR}
```

Example program:
```tnt
{EXAMPLE}
```

Rules:
- Always start with `import stdio.h`
- Always include a `fn main() -> int` that returns 0
- The program must be syntactically and semantically valid per the grammar above
- Do NOT use `import local` (no local header files are available)
- You can import the standard C libraries.
- Output ONLY the raw TNT code, no explanation, no markdown fences

- Generate program number {program_number}. Vary complexity across programs — use as many constructs of this programming language as you can.
- Pay attention to parentheses and semicolons.
- If a function does not return a value, its return type must be `void`. Example: `fn foo() -> void {{}}`
- The import instructions do not require a semicolon. Wrong: `import stdio.h;`; Correct: `import stdio.h`
- If a custom type has not been declared, it cannot be used.
- No inline `if`.
- To initialize a struct, you must access each field individually.
- Pointers are defined as follows: Example of an `int` pointer: `let foo: ref int;`. You can have pointers to any defined type.
- To obtain the address of a variable you must use the `addr` keyword.
- A struct declaration ends with a semicolon:
  ```
  struct MyType {{
    x: int;
  }};
  ```
- No ternary operator.
- This is how to dereference a pointer: `->ptr`.
- The value `null` and the keyword `null` do not exist.
- No arrays of arrays
- To call a C function, do the following: `c.malloc()`, `c.sizeof(int)`

Try creating a program that does something different from this:
{previous_program}
"""


def build_repair_prompt(program_text: str, error: str, attempt: int) -> str:
    return f"""You are a TNT language programmer. The following TNT program failed to compile.

TNT Language Grammar:
```
{GRAMMAR}
```

Reference program (known correct):
```tnt
{EXAMPLE}
```

Broken program (attempt {attempt}):
```
{program_text}
```

Compilation error:
```
{error}
```

- Do NOT use `import local` (no local header files are available)
- You can import the standard C libraries.
- If a function does not return a value, its return type must be `void`. Example: `fn foo() -> void {{}}`
- The import instructions do not require a semicolon. Wrong: `import stdio.h;`; Correct: `import stdio.h`
- The import instructions do not require a semicolon. Wrong: `import stdio.h;`; Correct: `import stdio.h`
- If a custom type has not been declared, it cannot be used.
- No inline `if`.
- To initialize a struct, you must access each field individually.
- Pointers are defined as follows: Example of an `int` pointer: `let foo: ref int;`. You can have pointers to any defined type.
- To obtain the address of a variable you must use the `addr` keyword.
- A struct declaration ends with a semicolon:
  ```
  struct MyType {{
    x: int;
  }};
  ```
- No ternary operator.
- This is how to dereference a pointer: `->ptr`.
- The value `null` and the keyword `null` do not exist.
- No arrays of arrays
- To call a C function, do the following: `c.malloc()`, `c.sizeof(int)`. You do not need to `import c`

Fix every error in the program. Output ONLY the corrected TNT code, no explanation, no markdown fences."""


# ============================================================
# Generation & Repair
# ============================================================


def generate_program(program_number: int, previous_program: str) -> str:
    text = call_llm(build_generation_prompt(program_number, previous_program))
    return strip_fences(text)


def repair_program(program_text: str, error: str, attempt: int) -> str:
    text = call_llm(build_repair_prompt(program_text, error, attempt))
    return strip_fences(text)


# ============================================================
# Compile (second agent)
# ============================================================


def compile_program(tnt_path: Path, program_number: int) -> tuple[bool, str]:
    # Step 1: TNT transpiler (must run from transpiler/ so tnt.lark is on CWD)
    tnt_result = subprocess.run(
        ["python3", "transpiler.py", str(tnt_path), "--no-color"],
        cwd=str(TRANSPILER_DIR),
        capture_output=True,
        text=True,
    )
    if tnt_result.returncode != 0:
        return False, (tnt_result.stdout + tnt_result.stderr).strip()

    # Step 2: Move output.c to output dir (overwrite previous attempt if any)
    src_c = TRANSPILER_DIR / "output.c"
    dst_c = OUTPUT_DIR / f"output_{program_number}.c"
    shutil.move(str(src_c), str(dst_c))

    # Step 3: GCC (binary named _tmp until we know the final suffix)
    binary_tmp = f"output_{program_number}_tmp"
    gcc_result = subprocess.run(
        ["gcc", f"output_{program_number}.c", "-o", binary_tmp],
        cwd=str(OUTPUT_DIR),
        capture_output=True,
        text=True,
    )
    if gcc_result.returncode != 0:
        return False, (gcc_result.stdout + gcc_result.stderr).strip()

    return True, ""


# ============================================================
# Main loop
# ============================================================


def main() -> None:
    setup()
    logging.info(
        "Starting agent run: %d programs, max %d attempts each",
        NUM_PROGRAMS,
        MAX_ATTEMPTS,
    )

    successful_program = EXAMPLE

    for i in range(1, NUM_PROGRAMS + 1):
        print(f"[Program {i}/{NUM_PROGRAMS}] Generating...", flush=True)
        program_text = generate_program(i, successful_program)

        success = False
        attempts = 0
        last_error = ""
        tmp_path = PROGRAMS_DIR / f"program_{i}_tmp.tnt"

        for attempt in range(MAX_ATTEMPTS):
            attempts += 1
            tmp_path.write_text(program_text, encoding="utf-8")

            print(f"  Attempt {attempts}/{MAX_ATTEMPTS}: compiling...", flush=True)
            ok, error = compile_program(tmp_path.resolve(), i)

            if ok:
                success = True
                print(f"  -> Success on attempt {attempts}")
                break

            last_error = error
            print(f"  -> Compile error: {error}", flush=True)

            if attempt < MAX_ATTEMPTS - 1:
                print("  Repairing...", flush=True)
                program_text = repair_program(program_text, error, attempt + 1)

        # Finalise naming
        suffix = "success" if success else "fail"
        if success:
            successful_program = program_text

        final_tnt = PROGRAMS_DIR / f"program_{i}_{suffix}.tnt"
        tmp_path.rename(final_tnt)

        c_tmp = OUTPUT_DIR / f"output_{i}.c"
        if c_tmp.exists():
            c_tmp.rename(OUTPUT_DIR / f"output_{i}_{suffix}.c")

        bin_tmp = OUTPUT_DIR / f"output_{i}_tmp"
        if success and bin_tmp.exists():
            bin_tmp.rename(OUTPUT_DIR / f"output_{i}_{suffix}")

        logging.info(
            "Program %d: %s after %d attempt(s)%s",
            i,
            suffix.upper(),
            attempts,
            f" | error: {last_error[:200]}" if not success else "",
        )


if __name__ == "__main__":
    main()
