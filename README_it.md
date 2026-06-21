# tnt-lang

Lingue disponibili: [en](https://github.com/utox39/tnt-lang/blob/main/README.md), [it](https://github.com/utox39/tnt-lang/blob/main/README_it.md)

Progetto per il corso di "Elementi di Ingegneria dei Linguaggi di Programmazione" (2025/2026) presso [Università degli Studi di Salerno](https://www.unisa.it/)

Autori: [Domenico Iorio](https://github.com/Blade990), [Vittorio Landi](https://github.com/toyo54), [Francesco Moccaldi](https://github.com/utox39)

- [Descrizione](#descrizione)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [Agents](#agents)
- [Docs](#docs)

## Descrizione

TNT è un linguaggio di programmazione imperativo a tipizzazione statica che viene transpilato in C.
La sintassi si ispira a linguaggi moderni come Rust, Swift e Zig, mantenendo un modello di esecuzione e un sistema di tipi compatibili con C.
Il compilatore (transpiler) traduce il codice sorgente `.tnt` in C valido pronto per essere compilato con qualsiasi toolchain C standard.

Caratteristiche principali:

- Tipizzazione statica forte, senza conversioni implicite.
- Gestione esplicita dei puntatori tramite le keyword `ref`, `addr` e `->`.
- Accesso ai campi delle struct sempre tramite l'operatore `.` (il transpiler produce `->` quando necessario).
- Costrutto `defer` per la gestione garantita delle risorse.
- Costrutto `tnt` per la terminazione immediata del programma (panic).
- Interoperabilità con funzioni C esterne tramite il prefisso `c.`.

## Requisiti

- [Python](https://www.python.org/)
- [GCC](https://gcc.gnu.org/)

## Installazione

```bash
# 0. Entrare nella directory della repo
cd path/to/tnt-lang

# 1. Creare un virtual environment per python
python3 -m venv venv

# 2. Attivare il virtual environment
source ./venv/bin/activate

# 3. Installare i requirements
pip3 install -r requirements.txt
```

## Utilizzo

```bash
# 0. Entrare nella directory della repo
cd path/to/tnt-lang

# 00. Attivare il virtual environment (se non attivo)
source ./venv/bin/activate

# 1. Entrare nella directory del transpiler
cd transpiler

# 2. Invocare il transpiler per compilare un programma scritto in TNT
python3 transpiler.py example.tnt
```

## Agents

```mermaid
flowchart LR
    GP[Generate Program]
    C[Compiler]
    RP[Repair Program]

    GP -->|programma candidato| C
    C -->|ok| GP
    C -->|errori| RP
    RP -->|programma candidato| C
```

Report Agents Loop v1: [report.pdf]()
Report Agents Loop v2: [report.pdf]()

L'agents loop è stato eseguito in locale mediante [Ollama](https://ollama.com/)

```bash
# 0. Entrare nella directory della repo
cd path/to/tnt-lang

# 00. Attivare il virtual environment (se non attivo)
source ./venv/bin/activate

# 1. Entrare nella directory agents
cd agents

# 2. Installare i requirements
pip3 install -r requirements.txt

# 3. Esportare le variabile d'ambiente necessarie
export TNT_OLLAMA_HOST="HOST:PORT" # Indirizzo e porta del sever Ollama
export TNT_OLLAMA_MODEL="MODEL_NAME" # Nome del modello che si vuole usare (deve essere già presente sul server Ollama)

# 4. Avviare l'agents loop
python3 agents.py
```

## Docs

- Language reference manual: [reference.pdf](https://github.com/utox39/tnt-lang/blob/main/docs/reference.pdf)
- Agents Loop v1 Report: [report.pdf](https://github.com/utox39/tnt-lang/blob/main/agents/agents_loop_v1/report.pdf)
- Agents Loop v2 Report: [report.pdf](https://github.com/utox39/tnt-lang/blob/main/agents/agents_loop_v2/report.pdf)
