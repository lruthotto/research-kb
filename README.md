# Auditable Research Knowledge Base — Starter

A skeleton for building your **own** auditable academic knowledge base (KB) for a
project or team. Clone it, point an AI coding agent at it, and start turning PDFs
into a cross-referenced research wiki where **every substantive claim traces back
to a source you actually read.**

This repo is the **generic skeleton**. A filled-in project vault — real papers,
real cross-references — is the worked example you build on top of it.

---

## Why auditability, not "a smarter model"

An LLM answering from its training weights is fluent and fast — and
**unverifiable.** Worse, it is *confidently wrong exactly where you can least
afford it*: on well-known material. The famous theorem, the canonical equation,
the landmark paper everyone cites — these are where a model reconstructs from a
blurry memory of a thousand paraphrases and hands you a wrong sign, a fabricated
"convergence theorem," a flipped benchmark result, a dropped second author. It
sounds authoritative because it has seen the topic a million times. That is the
trap.

A knowledge base does not fix this by being perfect. **It earns trust by being
auditable.** Every page on it can be traced to a specific PDF, specific pages, a
specific read, on a specific date — or it is flagged as unsourced. You do not have
to believe the summary; you can check it.

Three mechanisms, working together, enforce that:

1. **A plain-text CONTRACT — the READ PROTOCOL.** *No PDF, no body.* The rule, in
   `knowledge/AGENTS.md`, is non-negotiable: an agent may write a paper's Summary,
   equations, or theorem statements **only after** a real PDF is on disk and was
   actually rendered and read this session. If there is no readable PDF, the agent
   writes a `status: to-read` stub and stops. Reconstructing a body from memory is
   never allowed, however famous the paper.

2. **A `source_trace` record on every page.** Each ingested paper page carries a
   `source_trace` block in its frontmatter: which `pages_read`, what
   `transcription_method` (`read-tool | pdftotext | none`), what `date_read`. This
   is the audit trail. It turns "trust me" into "here is exactly how this page was
   produced."

3. **A DETERMINISTIC lint check — plain Python, zero LLM calls.** `scripts/lint_kb.py`
   reads the frontmatter and the filesystem and mechanically catches the failures
   the prose contract is meant to prevent: an ingested page with an empty
   `source_trace`, a page that *claims* it was read with the Read tool but whose
   PDF is not on disk (it could not have been read), a "to-read" stub that
   nonetheless contains equation- or theorem-grade prose. **No LLM grades another
   LLM here.** The checks are arithmetic on files — reproducible, fast, CI-able.

Together: the contract sets the rule, `source_trace` records compliance, and the
lint enforces it without trusting anyone's word — including the model's.

---

## What is in this repo

```
research-kb/
├── README.md                     # this file — the integrity pitch + quick start
├── docs/
│   ├── QUICK-START.md            # first paper, end to end (fetch → ingest → lint)
│   └── use-cases.md              # when a KB beats RAG; team use; learning with it
├── knowledge/                    # the skeleton vault (you fill this in)
│   ├── AGENTS.md                 # THE CONTRACT — the READ PROTOCOL, agent-neutral
│   ├── papers/ concepts/ methods/ theorems/ authors/ ...   # page-type dirs
│   ├── templates/                # frontmatter templates per page type
│   └── raw/pdfs/                 # downloaded PDFs (gitignored) + manifest.md
├── scripts/
│   ├── lint-kb.sh                # wrapper → runs lint_kb.py on knowledge/
│   ├── lint_kb.py                # the deterministic checker (plain Python)
│   ├── fetch_pdf.py             # download + VALIDATE a PDF (no silent failures)
│   └── requirements.txt          # PyYAML, pypdf
└── .claude/skills/knowledge-base/  # the vendored knowledge-base skill
    ├── SKILL.md                  # scaffold / ingest / query / lint capabilities
    └── references/               # frontmatter schemas, delegation prompt, lessons
```

The `knowledge/` tree ships empty (just the directory skeleton and the contract).
You populate it — either by hand from `knowledge/templates/`, or by running the
vendored skill's SCAFFOLD step to generate a domain-tailored schema first.

---

## Quick Start

1. **Clone and install the two Python deps.**
   ```bash
   git clone https://github.com/lruthotto/research-kb.git
   cd research-kb
   python3 -m pip install -r scripts/requirements.txt
   ```

2. **Read the contract.** Open `knowledge/AGENTS.md`. This is the READ PROTOCOL —
   *no PDF, no body* — and the page schema your agent must follow. Everything else
   is downstream of it.

3. **Pick how to start filling `knowledge/`:**
   - **Scaffold (recommended for a new topic).** Open an AI coding agent in this
     repo and invoke the vendored `knowledge-base` skill's **SCAFFOLD** capability
     (Capability 1 in `.claude/skills/knowledge-base/SKILL.md`). It interviews you
     for the topic and page types, then writes a domain-tailored schema and
     navigation files into `knowledge/`.
   - **Or by hand.** Copy a template from `knowledge/templates/` into the right
     page-type directory and fill it in.

4. **Ingest your first paper with an AI coding agent** (Claude Code, or a CLI
   agent) **under the READ PROTOCOL.** Fetch a PDF, then have the agent read it
   from disk and write a sourced page with a `source_trace`. Step-by-step:
   [`docs/QUICK-START.md`](docs/QUICK-START.md).

5. **Run the lint.**
   ```bash
   bash scripts/lint-kb.sh knowledge
   ```
   It must be clean of **HARD** issues. Warnings (empty dirs, orphan pages on a
   fresh vault) are expected early on.

---

## How the lint works (and why it's mechanical)

`scripts/lint-kb.sh` is a thin wrapper around `scripts/lint_kb.py`. The checker
is **plain Python with zero LLM calls** — it never asks a model to judge whether a
page is "good." It parses each page's YAML frontmatter (via PyYAML) and walks the
filesystem, then applies fixed rules. The ones that enforce auditability:

- **`source_trace` present.** Any paper page with `status: ingested` must have a
  non-empty `source_trace` (`pages_read`, `transcription_method`, `date_read`).
  Empty → **HARD** failure: the body was not verifiably sourced.
- **`transcription_method` is a strict enum.** `read-tool | pdftotext | none`.
  Anything else (`read-tool-with-fallback`, `pymupdf`, …) → **HARD** failure.
- **The fabrication signature.** A page claiming `transcription_method: read-tool`
  whose `pdf:` does **not** resolve on disk → **HARD** failure: it could not have
  been read, so the body was almost certainly reconstructed from memory.
- **No body on an unread stub.** A `status: to-read` page with substantive content
  in equation/theorem-grade sections → **HARD** failure (descriptive prose →
  warning): a page never read can only have been drafted from memory.
- Plus structural hygiene: dead links, missing frontmatter `type`, PDF-on-disk vs.
  `raw/pdfs/manifest.md` drift, BibTeX sync, orphan pages, empty directories.

Because the rules are arithmetic on files and frontmatter — not a model's opinion —
they are deterministic and reproducible. The same vault lints the same way on any
machine, in CI, today and next year. That is the whole point: **the thing checking
the model is not another model.**

For the full set of capabilities (scaffold, ingest, query, evolve, connect) and the
complete READ PROTOCOL with its documented failure history, see
[`.claude/skills/knowledge-base/SKILL.md`](.claude/skills/knowledge-base/SKILL.md).
