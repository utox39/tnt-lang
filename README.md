# tnt-lang

Available languages: [en](https://github.com/utox39/tnt-lang/blob/main/README.md), [it](https://github.com/utox39/tnt-lang/blob/main/README_it.md)

- Project for the "Elements of Programming Language Engineering" course (2025/2026) at [University of Salerno](https://www.unisa.it/)
- Authors: [Domenico Iorio](https://github.com/Blade990), [Vittorio Landi](https://github.com/toyo54), [Francesco Moccaldi](https://github.com/utox39)

- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Agents](#agents)
- [Docs](#docs)

## Description

TNT is a statically typed imperative programming language that transpiles to C.
The syntax is inspired by modern languages such as Rust, Swift, and Zig, while maintaining an execution model and type system compatible with C.
The compiler (transpiler) translates `.tnt` source code into valid C ready to be compiled with any standard C toolchain.

Key features:

- Strong static typing, with no implicit conversions.
- Explicit pointer management via the `ref`, `addr`, and `->` keywords.
- Struct field access always through the `.` operator (the transpiler emits `->` when needed).
- `defer` construct for guaranteed resource management.
- `tnt` construct for immediate program termination (panic).
- Interoperability with external C functions via the `c.` prefix.

## Requirements

- [Python](https://www.python.org/)
- [GCC](https://gcc.gnu.org/)

## Installation

```bash
# 0. Enter the repo directory
cd path/to/tnt-lang

# 1. Create a Python virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
source ./venv/bin/activate

# 3. Install the requirements
pip3 install -r requirements.txt
```

## Usage

```bash
# 0. Enter the repo directory
cd path/to/tnt-lang

# 00. Activate the virtual environment (if not already active)
source ./venv/bin/activate

# 1. Enter the transpiler directory
cd transpiler

# 2. Invoke the transpiler to compile a program written in TNT
python3 transpiler.py example.tnt
```

## Agents

```mermaid
flowchart LR
    GP[Generate Program]
    C[Compiler]
    RP[Repair Program]

    GP -->|candidate program| C
    C -->|ok| GP
    C -->|errors| RP
    RP -->|candidate program| C
```

- Agents Loop v1 Report: [report.pdf]() (Italian only)
- Agents Loop v2 Report: [report.pdf]() (Italian only)

The agents loop was run locally using [Ollama](https://ollama.com/)

```bash
# 0. Enter the repo directory
cd path/to/tnt-lang

# 00. Activate the virtual environment (if not already active)
source ./venv/bin/activate

# 1. Enter the agents directory
cd agents

# 2. Install the requirements
pip3 install -r requirements.txt

# 3. Export the required environment variables
export TNT_OLLAMA_HOST="HOST:PORT" # Address and port of the Ollama server
export TNT_OLLAMA_MODEL="MODEL_NAME" # Name of the model to use (must already be present on the Ollama server)

# 4. Start the agents loop
python3 agents.py
```

## Docs

- Language reference manual: [reference.pdf]()
- Agents Loop v1 Report: [report.pdf]() (Italian only)
- Agents Loop v2 Report: [report.pdf]() (Italian only)
