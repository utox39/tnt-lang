#set page(paper: "a4", margin: 2.5cm)
#set text(size: 11pt, lang: "it", font: "New Computer Modern")
#set heading(numbering: "1.1.")
#set par(justify: true)
#show link: underline

#import "@preview/fletcher:0.5.8": diagram, edge, node

#align(center)[
  #v(3cm)
  #text(size: 22pt, weight: "bold")[Linguaggio TNT] \
  #v(0.6em)
  #text(size: 14pt, style: "italic")[Report Agents Loop v2] \
  #v(1.5em)
  #text(size: 11pt, fill: luma(80))[Elementi di Ingegneria dei Linguaggi di Programmazione 2025/2026] \
  #v(2em)
  #text(size: 11pt)[
    Domenico Iorio \
    Vittorio Landi \
    Francesco Moccaldi
  ]
  #v(3cm)
]

#pagebreak()

#outline(indent: 1.5em)

#pagebreak()

= Info
- Model: #link("https://ollama.com/library/devstral")[devstral:24b]
- LLM runtime: #link("https://ollama.com/")[Ollama]
- Hardware info:
  - OS: Fedora Linux 44 (Workstation Edition) x86_64
  - Kernel: Linux 7.0.12-201.fc44.x86_64
  - CPU: 12th Gen Intel(R) Core(TM) i7-12700K (20) @ 5.00 GHz
  - GPU: NVIDIA GeForce RTX 3060 Lite Hash Rate (12 VRAM)
  - RAM: 32 GB

= Agents pattern

#diagram(
  node-stroke: 1pt,
  node-corner-radius: 8pt,
  spacing: (20mm, 16mm),

  node((0, 0), [Generator Agent], width: 44mm, height: 14mm),
  node((1, 0), [Compiler], width: 44mm, height: 14mm),
  node((1, 1), [Repair Program Agent], width: 44mm, height: 14mm),

  edge((0, 0), (1, 0), "-|>", label: [programma candidato], bend: 10deg),
  edge((1, 0), (0, 0), "-|>", label: [ok], bend: 10deg),

  edge((1, 0), (1, 1), "-|>", label: [errori], bend: 10deg),
  edge((1, 1), (1, 0), "-|>", label: [programma candidato], bend: 10deg),
)

= Prompts

== Generator Agent Prompt

#raw(
  lang: "markdown",
  block: true,
  "
You are a TNT language programmer. Generate a valid, simple, self-contained TNT program.

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
",
)

== Repair Agent Prompt

#raw(
  lang: "markdown",
  block: true,
  "
You are a TNT language programmer. The following TNT program failed to compile.

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

Fix every error in the program. Output ONLY the corrected TNT code, no explanation, no markdown fences.
  ",
)

= Stats

== Validity Rate

Percentuale di programmi generati che non generano errori di compilazione

Compilatore usato: #link("https://gcc.gnu.org/")[GCC]

Comando di compilazione usato: ```sh gcc -o output output.c```

Ogni file valido ha come suffisso `_success.tnt`, quindi per calcolare il numero di programmi validi è stato eseguito il seguente comando
nella directory dei programmi generati:

```bash
ls -lah | grep success | wc -l
```

$"Validity Rate" = ("numero di programmi che compilano") / ("numero di programmi prodotti totali") * 100%$

_Validity Rate_ $= (62) / (100) * 100% = 62%$

== Diversity

Quanto variano i programmi generati tra di loro.

_Approccio_: per ogni coppia di programmi è stata calcolata la distanza di Levenshtein e poi fatta la media tra le varie distanze di edit.

_Diversity_ $= 1135$

Distanza di edit più alta $= 2765$

Distanza di edit più bassa $= 66$

Si veda #raw("tnt-lang/agents/agents_loop_v2/diversity.py") per vedere come è stato fatto il calcolo della _diversity_.

== Coverage

Percentuale di copertura dei costrutti del linguaggio

$"Coverage" = ("numero di produzioni esercitate") / ("numero di produzioni totali") * 100%$

_Coverage_ $= (64) / (135) * 100% = 47.41%$

Si veda #raw("tnt-lang/agents/agents_loop_v2/coverage.py") per vedere come è stato fatto il calcolo della _coverage_.

== Cost

L'inferenza è stata fatta in locale mediante Ollama quindi non ci sono stati costi per i token.

= Conclusioni

Questa seconda versione, come la prima, ci ha permesso di trovare alcuni bug di codegen e di introdurre alcuni costrutti comuni che non erano ancora stati inseriti nel nostro linguaggio.

Il numero di programmi validi (_validity_) è più alto (62%) rispetto a quello della prima versione ($55%$) ma ha una _diversity_ inferiore ($1135$ vs $1861$) e
una coverage inferiore ($47.41%$ vs $50.37%$).

Quindi possiamo dire che la prima versione dell'agents loop ha delle statistiche più equilibrate. I motivi principali di tali differenze nelle statistiche sono:
- l'uso di due modelli diversi: #link("https://ollama.com/library/qwen3-coder")[qwen3-coder:30b] e #link("https://ollama.com/library/devstral")[devstral:24b]
- cambiamenti ai prompt
- cambiamenti al programma d'esempio
