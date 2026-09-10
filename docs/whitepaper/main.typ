#set document(
  title: "QuakeGuard - Technical Specification", 
  author: ("GiZano", "riccardo0731")
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 3cm),
  header: context {
    // Utilizes native Typst context syntax
    if counter(page).get().first() > 1 {
      align(right)[_QuakeGuard v2.1.0 - Technical Architecture_]
    }
  },
  numbering: "1",
)

// Typography Settings
#set text(font: "Liberation Serif", size: 11pt, lang: "en")
#set heading(numbering: "1.1.")
#set par(justify: true, leading: 0.65em)

// --- TITLE PAGE ---
#align(center)[
  #v(3cm)
  #text(size: 32pt, weight: "bold")[QuakeGuard]\
  #v(0.5cm)
  #text(size: 16pt)[Distributed Earthquake Early Warning System]\
  #v(0.2cm)
  #text(size: 14pt)[Technical Architecture & Protocol Specification]\
  #v(2cm)
  #text(size: 12pt)[Release: *v2.1.0* (Grafana Observability & System Telemetry)]\
  #v(0.5cm)
  #text(size: 12pt)[Core Maintainers: \@GiZano, \@riccardo0731]\
  #v(2cm)
  #image("assets/logo/png/logo.png", width: 45%)
]

#pagebreak()

// --- TABLE OF CONTENTS ---
#outline(
  title: "Table of Contents",
  depth: 3,
  indent: auto
)

#pagebreak()

// --- EXECUTIVE SUMMARY ---
#include "00-executive-summary.typ"

#pagebreak()

// --- CHAPTERS ---
#include "01-architecture.typ"
#include "02-hardware.typ"
#include "03-security.typ"
#include "04-broker.typ"
#include "05-backend.typ"
#include "06-mobile.typ"
#include "07-deployment.typ"
#include "08-ai.typ"
#include "09-triangulation.typ"
#include "09-devops.typ"
#include "10-benchmarks.typ"
#include "11-limitations.typ"
#include "12-roadmap.typ"
#include "13-threat-model.typ"
#include "14-bibliography.typ"
#include "15-glossary.typ"
#include "16-appendix.typ"