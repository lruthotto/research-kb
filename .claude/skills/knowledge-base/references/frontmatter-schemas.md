# Frontmatter Schemas for Knowledge Base Pages

Base schemas for all page types. Domain-specific fields should be added
to the CLAUDE.md of each vault.

## Paper Page

```yaml
---
type: paper
title: ""
authors:
  - ""
year:
venue: ""
venue_type:   # conference | journal | preprint | book | thesis
doi: ""
arxiv: ""
pdf: ""
bibtex_key:
status: to-read  # to-read | reading | ingested | annotated
date_ingested:
# source_trace is REQUIRED when status: ingested. It records how the
# body of this page was produced. Empty source_trace + status:ingested
# is a hard LINT failure. See root CLAUDE.md INGEST "READ PROTOCOL".
source_trace:
  pages_read: ""          # e.g. "1-20, 45-52" — PDF pages actually read
  transcription_method:   # read-tool | pdftotext | none
  date_read:              # YYYY-MM-DD of the session that read the PDF
  notes: ""               # optional: which sections / equations transcribed
topics: []
methods: []
cites: []
cited_by: []
era: ""
relevance:    # high | medium | low | tangential
relevance_note: ""
tags:
  - paper
---
```

Body sections: Summary, Key Contributions, Method Details, Theoretical
Results, Relation to Our Work, Limitations / Open Questions, Selected
Equations (with the paper's own equation numbers cited inline, e.g.,
`Eq. 3.2`, so every formula is traceable to its source).

**READ PROTOCOL reminder**: Every substantive claim on a paper page
must be sourced from the actual PDF — never reconstructed from prior
knowledge. Use `Read` on the PDF first; fall back to
`pdftotext -layout` only if `Read` fails. If no PDF is available,
keep `status: to-read` and leave body sections empty. See
SKILL.md Capability 2 for the full protocol.

## Concept Page

```yaml
---
type: concept
title: ""
aliases: []
category:     # Customize per domain. Examples: pde, sde, control-theory,
              # optimization, numerical-method, ml-method, algebra, topology
first_appearance:
key_equation: ""
parent_concepts: []
child_concepts: []
related_concepts: []
key_papers: []
tags:
  - concept
---
```

Body sections: Definition, Mathematical Formulation, Key Properties,
Historical Context, Connections.

## Method Page

```yaml
---
type: method
title: ""
aliases: []
category:     # iterative | neural | classical | hybrid | monte-carlo
introduced_in: ""
parent_methods: []
child_methods: []
related_methods: []
key_papers: []
complexity: ""
convergence_rate: ""
tags:
  - method
---
```

Body sections: Overview, Algorithm (with pseudocode), Convergence Properties,
Advantages / Limitations, Implementations.

## Author Page

```yaml
---
type: author
name: ""
affiliation: ""
homepage: ""
scholar: ""
research_areas: []
key_contributions: []
papers_in_wiki: []
era_active: []
tags:
  - author
---
```

Body sections: Overview, Key Contributions, Papers in This Knowledge Base.

## Era Page

```yaml
---
type: era
title: ""
decade:
theme: ""
predecessor: ""
successor: ""
key_developments: []
key_figures: []
tags:
  - era
---
```

Body sections: Overview, Key Contributions, Connection to Our Work.

## Theorem Page

```yaml
---
type: theorem
title: ""
statement_type:   # theorem | lemma | proposition | conjecture | observation
formal_statement: ""
assumptions: []
conclusion: ""
convergence_rate: ""
proved_in: ""
extends: []
extended_by: []
open_questions: []
tags:
  - theorem
---
```

Body sections: Statement, Assumptions, Proof Sketch, Implications,
Extensions and Open Questions.

## Synthesis Page

```yaml
---
type: synthesis
title: ""
scope:        # comparison | survey | lineage | bridge
subjects: []
key_papers: []
related_concepts: []
date_created:
date_updated:
tags:
  - synthesis
---
```

Body: Free-form. Typically includes tables, timelines, or structured
comparisons connecting multiple concepts/methods/papers.

## Domain-Specific Pages (Examples)

### Problem Class (for SOC, PDEs, optimization)

```yaml
---
type: problem-class
title: ""
aliases: []
dynamics_structure: ""
cost_structure: ""
special_properties: []
assumptions: []
child_of: ""
parent_of: []
applicable_methods: []
convergence_known: ""
example_benchmarks: []
key_papers: []
tags:
  - problem-class
---
```

### Benchmark (for computational science)

```yaml
---
type: benchmark
title: ""
aliases: []
dimension:
problem_class: ""
dynamics_type:
has_analytic_solution:
difficulty:       # easy | medium | hard
introduced_in: ""
used_in: []
methods_tested: []
key_features: []
tags:
  - benchmark
---
```

### Dataset (for ML/AI)

```yaml
---
type: dataset
title: ""
aliases: []
domain: ""
size: ""
num_classes:
modality:     # image | text | graph | tabular | multimodal
source: ""
license: ""
introduced_in: ""
used_in: []
tags:
  - dataset
---
```

### Architecture (for deep learning)

```yaml
---
type: architecture
title: ""
aliases: []
category:     # cnn | rnn | transformer | gnn | diffusion | hybrid
introduced_in: ""
num_params: ""
key_innovation: ""
parent_architectures: []
child_architectures: []
key_papers: []
tags:
  - architecture
---
```
