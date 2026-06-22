#set page(paper: "a4", margin: 2.5cm)
#set text(size: 11pt, lang: "it", font: "New Computer Modern")
#set heading(numbering: "1.1.")
#set par(justify: true)

#align(center)[
  #v(3cm)
  #text(size: 22pt, weight: "bold")[Linguaggio TNT] \
  #v(0.6em)
  #text(size: 14pt, style: "italic")[Relazione sull'Utilizzo dell'Intelligenza Artificiale] \
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

= Introduzione

Fin dalle prime fasi del progetto, l'approccio adottato ha escluso l'impiego dell'IA solo come generatore automatico di codice. Gli strumenti di IA sono stati usati come supporto continuo alla convalida e alla generazione di codice, soprattutto quello boilerplate, e come tutor teorico e metodologico.

= Tipologia di Utilizzo

== Supporto Teorico e Comprensione delle Problematiche di Compilazione
L'IA è stata impiegata come supporto nello studio e nell'applicazione pratica dei concetti.
I temi specifici da noi approfonditi sono stati:
- *Gestione dello Scope:* Definizione del ruolo distinto tra la *Symbol Table* (utilizzata come memoria temporanea per la verifica degli scope).
- *Pattern Architetturali:* Implementazione di base del *Visitor Pattern*.

== Sviluppo del Codice e Debugging
L'utilizzo diretto nella scrittura del codice si è concentrato sulla riduzione del carico di lavoro relativo a logiche ripetitive e sulla diagnostica degli errori:
- *Estensione del Linguaggio:* Definizione della sintassi e della logica dei nodi AST per l'introduzione di nuovi operatori, quali, mappandone i requisiti dal Lexer fino al generatore di codice.
- *Risoluzione di Bug Complessi:* Identificazione di errori tra le regole della grammatica e bug nel codice.

= Vantaggi e Inconvenienti

== Vantaggi
- *Incremento della Produttività:* Sensibile riduzione dei tempi legati alla risoluzione di errori sintattici o refusi nella stesura della grammatica.

== Inconvenienti
- *Perdita del Contesto:* Data la segmentazione del progetto su più moduli, ciò induceva l'IA a generare allucinazioni, quali metodi inesistenti o modifiche incoerenti con il resto della codebase e introduzione di nuovi bug.

= Lezioni Apprese
Grazie all'uso dell'AI, abbiamo approfondito le conoscenze per qunato concerne la materia e l'utilizzo mirato di Lark come libreria.

= Conclusioni

In conclusione, l'efficacia di tali strumenti in progetti a elevata complessità è strettamente subordinata alla capacità degli sviluppatori di formulare prompt specifici e focalizzati su singoli passaggi di sviluppo, piuttosto che formulare richieste di risoluzione generiche.
