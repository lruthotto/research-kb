---
name: knowledge-base
description: "This skill should be used when creating, maintaining, or querying an LLM-maintained academic knowledge base. It covers scaffolding a new knowledge base for any research topic, ingesting papers and sources, maintaining cross-references between pages, and running health checks. Use when the user wants to build a structured research wiki, ingest academic papers into an existing knowledge base, query a knowledge base, or maintain/lint an existing knowledge base."
---

# Knowledge Base

Build and maintain LLM-powered academic knowledge bases — persistent,
compounding collections of markdown files that organize research papers,
concepts, methods, and their connections. Based on the LLM Wiki pattern
(Karpathy, 2025) adapted for scientific research.

## When to Use This Skill

- User wants to create a new knowledge base for a research topic
- User wants to ingest a paper (PDF, arXiv link, or reference) into an existing KB
- User asks a question that should be answered from a knowledge base
- User wants to run a health check / lint on a knowledge base
- User mentions "knowledge base", "research wiki", "paper database", or "ingest paper"

## Core Principles

1. **The LLM writes, the human directs.** The human curates sources and asks
   questions. The LLM does all summarizing, cross-referencing, and bookkeeping.
2. **Knowledge compounds.** Each ingested paper touches 5-15 existing pages.
   The wiki gets richer over time — this is NOT a flat collection of summaries.
3. **Standard markdown only.** No Obsidian wikilinks, no proprietary formats.
   All links use `[text](relative/path.md)` so they work in any editor.
4. **Papers are primary sources.** Blog posts, tweets, and talks are secondary.
   Every claim traces back to a published paper.
5. **Schema evolves.** The CLAUDE.md in each vault is a living document. When
   the user discovers better conventions, update the schema.

## Architecture

Three layers per knowledge base:

```
vault-root/
├── CLAUDE.md              # Schema: how to maintain this specific KB
├── index.md               # Topic-organized master index
├── log.md                 # Chronological operation log
├── timeline.md            # Historical timeline
├── open-questions.md      # Research gaps
├── reading-list.md        # Papers to ingest
├── connections.md         # Cross-domain connection map
├── references.bib         # Master BibTeX file
├── .obsidian/             # Optional Obsidian config
├── raw/                   # Layer 1: Immutable sources
│   ├── pdfs/{topic}/      # Downloaded PDFs
│   └── clips/             # Web clippings
├── papers/                # Layer 2: Wiki pages
├── concepts/
├── methods/
├── problem-classes/       # Domain-specific taxonomy (customizable)
├── benchmarks/            # Domain-specific (customizable)
├── authors/
├── eras/
├── theorems/
├── synthesis/
├── code-links/            # Links to implementation repos
└── templates/             # Frontmatter templates
```

**Layer 1 (Raw):** Immutable source documents. Never modified after placement.
**Layer 2 (Wiki):** LLM-generated markdown pages with YAML frontmatter.
**Layer 3 (Schema):** CLAUDE.md — instructions for maintaining this specific KB.

## Capability 1: Scaffold a New Knowledge Base

When the user wants to create a knowledge base for a new topic:

### Step 1: Understand the domain

Ask the user (use AskUserQuestion if needed):
- What is the research topic? (e.g., "stochastic optimal control", "graph neural networks")
- What is the vault path? Two patterns:
  - **Standalone vault**: `~/code/my-topic-knowledge/` (its own git repo)
  - **Vault in a multi-topic repo**: `~/code/research-knowledge/my-topic/`
    (shared git repo with other vaults, one .gitignore at repo root)
- What domain-specific page types are needed beyond the defaults?
  - Default types: papers, concepts, methods, authors, eras, theorems, synthesis
  - Common additions: problem-classes, benchmarks, datasets, architectures, experiments
- Is there a related codebase to link to?
- Are there seed papers or PDFs to ingest?

### Step 2: Create directory structure

Create all directories per the architecture above. Customize the domain-specific
directories based on Step 1 answers.

### Step 3: Generate CLAUDE.md

Read `references/claude-md-template.md` for the template. Customize it with:
- Domain name and description
- Page type definitions with required/optional frontmatter fields
- Domain-specific frontmatter (e.g., `problem_classes` for SOC, `datasets` for ML)
- Ingest workflow steps specific to this domain
- Seed priority tiers (what to build first)
- Linking conventions with relative path examples

### Step 4: Create templates

Generate frontmatter templates in `templates/` for each page type.
Read `references/frontmatter-schemas.md` for the base schemas. Customize
fields for the domain.

### Step 5: Create navigation files

Generate: `index.md`, `log.md`, `timeline.md`, `open-questions.md`,
`reading-list.md`, `connections.md`, and empty `references.bib`.

### Step 6: Configure .obsidian (optional)

If user wants Obsidian support, create `.obsidian/` with:
- `app.json` — basic settings
- `graph.json` — color groups by folder
- `community-plugins.json` — recommended plugins

### Step 7: Ingest seed papers

If the user provided initial PDFs or references, ingest them using
Capability 2.

## Capability 2: Ingest a Paper

The core operation. When given a paper (PDF, arXiv ID, DOI, or citation):

### READ PROTOCOL — read this before every ingest

**The failure mode this protocol prevents.** On 2026-04-13 / 2026-04-14
an audit of ~40 paper pages across three topics found that **~90% had
substantive errors** because the ingesting agent had reconstructed
equations, theorem statements, and experimental numbers from prior
knowledge of the (famous) papers rather than reading the PDF. The
errors included a wrong-sign HJB equation, a fabricated "quadratic
convergence theorem" attributed to a paper that only mentions the rate
in a footnote, a missing second author, and wrong equivalence-class
memberships for a loss-function taxonomy. Several of these papers had
no PDF on disk at all — they could not possibly have been read.

A second, related failure showed up in the 2026-04-29 batch of 16
papers: every sub-agent's `Read` call on a PDF errored with
`pdftoppm is not installed`, because poppler-utils wasn't in the
devcontainer. Sub-agents fell back to text-only extraction
(`pdftotext` / `pypdf`) and produced pages that were ~95% correct but
quietly wrong on roughly 30 specific items — including a flipped
benchmark result (Graph U-Nets "beats DiffPool on COLLAB" when it
actually loses), an off-by-one polylog exponent in Spielman-Teng 2011
Sparsify2, a baseline mix-up in Zhou 2024 (V-Laplace compared to the
wrong number in the table), and a wrong subscript in Chen 2025 GNP
Theorem 1. Text-extraction fallbacks read column order and equation
characters wrong often enough that the "looks fine" output is not
trustworthy for theorem-statement-grade fidelity.

A third failure, found by a 2026-06-08 KB-wide audit, was the largest:
~30% of an entire vault's paper pages contained fabricated theorems,
equations, numbers, venues, or authors because the page was written
with **no PDF on disk** (or with a `pdf:` field that did not resolve
from the ingest working directory) while `transcription_method:
read-tool` was nonetheless recorded. The convenient "give me an arXiv
URL and let the agent download it" flow had silently failed — a 404, a
rate-limit/HTML page saved as `.pdf`, or a download that never ran —
and the agent reconstructed the body from memory anyway. The root
cause was that nothing *deterministically* gated body-writing on a
verified, readable PDF; the prose protocol alone was not enforced.
**The fix is the INGEST GATE below plus `scripts/fetch_pdf.py`**, which
turns a silent download failure into a hard FAIL.

**Rules.** These apply to every paper ingest, every re-read, and every
sub-agent you delegate an ingest task to. They are non-negotiable.

0. **Canary the `Read` tool before the batch starts.** Before spawning
   sub-agents for a batch ingest, run **one** `Read` call on a known
   PDF in the vault yourself. If it returns `pdftoppm is not
   installed` or any other PDF-rendering error, STOP and resolve at
   the system level (see "PDF tooling preflight" below) before
   delegating. Do not let sub-agents discover the failure individually
   — they will silently fall back and produce subtly-wrong content.
1. **PDF-first, and PASS THE INGEST GATE. No verified PDF → no body.**
   You may write Summary / Method Details / Theoretical Results /
   Selected Equations **only after** the INGEST GATE (below, after
   Step 2) passes for this exact page in this session: (a) the file at
   the page's `pdf:` path exists on disk, (b) it is a valid PDF, and
   (c) a `Read` call on that path actually rendered it this session.
   For arXiv/URL sources, obtain the PDF with
   `scripts/fetch_pdf.py <source> --out <path>` — it validates the
   download and prints `PASS` only for a real PDF; treat any `FAIL` as
   "no PDF". If the gate does not pass, create a stub with
   `status: to-read`, log the blocked ingest, and STOP. Reconstructing
   a body from memory is never acceptable, however famous the paper.
2. **Use the `Read` tool on the PDF path. No fallback for ingest.**
   `Read` supports PDFs natively (multimodal, full rendering of pages
   as images so equations, tables, and figures are read pixel-correct).
   For papers over 10 pages pass the `pages` parameter (max 20 per
   call) and make multiple `Read` calls to cover the abstract,
   introduction, method, theory, and conclusions at minimum.
   **`pdftotext` and `pypdf` are NOT acceptable fallbacks for INGEST.**
   They lose column order, mangle math symbols, and silently drop
   superscript/subscript distinctions — exactly the failure mode that
   produced the 2026-04-29 errors. If `Read` fails, fix the system
   (poppler-utils install, restart Claude Code) and retry. If it
   cannot be fixed in this session, STOP and mark `status: to-read`.
3. **Text-extraction fallbacks are reserved for verification / LINT,
   not initial drafting.** A grep over `pdftotext` output is fine for
   "does this PDF mention author X?" — but never for transcribing
   theorem statements, equation numbers, or table values into a paper
   page.
4. **Never reconstruct from memory.** "I know this paper" is never
   acceptable as a source. Famous papers are where silent errors
   accumulate. Equations and theorem statements must be transcribed
   directly from the PDF with the paper's own equation numbers
   (`Eq. 3.2`, `Theorem 1`) cited inline.
5. **Record the source trace — honestly.** Fill the `source_trace`
   frontmatter block (`pages_read`, `transcription_method`,
   `date_read`) on every ingested paper page. `transcription_method`
   is a strict enum: `read-tool | pdftotext | none`. Do not invent
   values like `pdftotext-via-pypdf` or `read-tool-with-fallback`.
   **Never set `transcription_method: read-tool` unless a `Read` call
   actually rendered this PDF in this session** — this exact dishonesty
   (read-tool claimed, PDF absent) caused the 2026-06-08 fabrication
   batch. `pages_read` must be the ranges you really read. Empty
   `source_trace` + `status: ingested` is a hard LINT failure;
   `transcription_method: pdftotext` + `status: ingested` is a soft
   warning that the page should be re-verified once `Read` works.
6. **Delegating to sub-agents.** If you spawn a sub-agent to ingest a
   paper, use the canonical prompt in
   `references/delegation-template.md` — fill the placeholders and
   paste it whole. Do not assume the sub-agent will infer the
   protocol, and do not write your own abridged version. Most of the
   2026-04-13 failures were sub-agent ingests where the delegating
   prompt said only "read the PDF" without specifying the tool or
   the no-reconstruction rule. The 2026-04-29 failures were
   sub-agent ingests where the prompt allowed text-extraction
   fallback "in case Read fails" — sub-agents took the easy path
   instead of escalating. The template also carries the delegator's
   before/after checklist (rule-0 canary, gate-report verification,
   per-batch spot-check).

### PDF tooling preflight

The `Read` tool's PDF mode shells out to `pdftoppm` (poppler-utils).
On a fresh devcontainer this binary is often missing, in which case
`Read` returns:
`pdftoppm is not installed. Install poppler-utils...`

**Worse, the result is cached for the lifetime of the Claude Code
process** (the binary's `Vcz()` PDF-availability check caches its
first result). So installing poppler-utils mid-session does NOT
recover; the user must restart Claude Code for `Read` to start
working.

**Resolution checklist** (run this before every batch ingest, and
fix any failure before delegating):

1. Test: `Read` on any PDF in the vault. If it succeeds, you're done.
2. If it fails with `pdftoppm is not installed`:
   a. Install at the system level: `sudo apt-get update && sudo
      apt-get install -y poppler-utils` (Debian/Ubuntu) or
      `brew install poppler` (macOS).
   b. Symlink into `/usr/local/bin/` if `/usr/bin/pdftoppm` is the
      installed path and the agent's PATH search prefers
      `/usr/local/bin/`.
   c. Confirm at the shell: `pdftoppm -v` should print a version.
   d. **Tell the user the cache caveat**: `Read` will keep returning
      the cached "not installed" error for the rest of this session.
      Ask them to `/exit` and re-launch Claude Code. Then the canary
      from rule 0 will pass and ingest can proceed.
   e. **Persist the install in the devcontainer**: add
      `poppler-utils` to the devcontainer's Dockerfile (next to the
      LaTeX or build-tools block) so future rebuilds don't recreate
      this hole. Search the workspace for `Dockerfile` under
      `.devcontainer/`.
3. If `Read` fails for some other reason (timeout, file permissions,
   malformed PDF), follow the error message rather than silently
   degrading.

### Step 1: Obtain and classify the source

Decide the local path first: `raw/pdfs/{topic}/{first-author}-{year}-{keyword}.pdf`.

- **arXiv URL or ID, or a direct PDF URL (the convenient default):** run
  the validated downloader — do **not** improvise `curl`, which will
  happily save a 404/captcha/HTML page as a `.pdf`:

  ```bash
  python3 <skill-dir>/scripts/fetch_pdf.py "<arxiv-url|arxiv-id|pdf-url>" \
      --out raw/pdfs/{topic}/{first-author}-{year}-{keyword}.pdf
  ```

  It accepts `2009.02994`, `arXiv:2009.02994`, `https://arxiv.org/abs/...`,
  `https://arxiv.org/pdf/...`, or a direct publisher/author PDF URL; it
  normalises arXiv links, retries, falls back to the export mirror, and
  validates the result (`%PDF` header, plausible size, not HTML). It
  prints `PASS path=... pages=...` and a ready-to-paste `MANIFEST_ROW`
  on success, or `FAIL reason=...` (exit 1) on any problem. **Treat any
  `FAIL` as "no PDF": create a `status: to-read` stub and STOP — never
  proceed to a body.** If arXiv is rate-limiting, retry later or pass a
  direct PDF URL; if the paper is paywalled, ask the user for the file.
- **PDF file already provided:** move it to the path above.
- **Citation / DOI only, no obtainable PDF:** create the paper page from
  metadata, mark `status: to-read`, `transcription_method: none`. Do not
  write a body.

**Always update the PDF manifest** (`raw/pdfs/manifest.md`): paste the
`MANIFEST_ROW` the downloader printed (local filename, source URL, fetch
date), or add an equivalent row. PDFs are gitignored, so the manifest is
how they are re-obtained after a clone. If no URL exists, note the source
(e.g., "received from author").

### Step 2: Verify the PDF is readable in this session

Before writing any body content, run the READ PROTOCOL's PDF-first
check. Attempt `Read` on the PDF path. If `Read` errors with a
`pdftoppm is not installed` message (or any rendering error), follow
the **PDF tooling preflight** checklist in the READ PROTOCOL above —
install poppler-utils, confirm at the shell, ask the user to restart
Claude Code if needed, then retry. Do **not** silently switch to
`pdftotext` / `pypdf`: those are not acceptable for INGEST drafting.

If `Read` cannot be made to work in the current session (e.g. user
declines to restart, or some other blocker), create the paper page
as a `status: to-read` stub with an empty body and a comment in the
HTML preamble explaining why the PDF could not be read. Do NOT fill
in Summary, Method Details, Theoretical Results, or Selected
Equations.

### INGEST GATE — pass all three before writing ANY body content

This is the single check that prevents the memory-reconstruction
failure. For the specific page you are about to write, confirm:

1. **On disk.** `test -f "<the page's pdf: path, resolved>"` succeeds.
   The `pdf:` value must resolve to a real file from where you run the
   check (mind `../raw/...` vs `raw/...` conventions — a path that does
   not resolve is the same as no PDF).
2. **Valid PDF.** It begins with `%PDF` and is a plausible size
   (`head -c4` is `%PDF`; the downloader already guarantees this on
   `PASS`). Not an HTML/error page.
3. **Read-rendered this session.** A `Read` call on that exact path
   returned rendered pages (not `pdftoppm is not installed` or any
   error). This is the canary — a valid file you cannot Read is still
   a blocked ingest.

If any of the three fails: set `status: to-read`,
`transcription_method` to `none` (or `pdftotext` only if you genuinely
used it for verification, never for drafting), write NO body, log the
block, and STOP. Only when all three pass may you write the body and
record `transcription_method: read-tool` with the real `pages_read`.
When delegating to a sub-agent, require it to report the gate result
(pdf path, `%PDF` ok, pages Read) in its output.

### Step 3: Read the paper

Three ingestion depths. For all three, read from the actual PDF — see
the READ PROTOCOL. No depth allows reconstruction from memory.

- **Metadata-only** (no PDF needed): title, authors, year, venue from
  citation or arXiv. Creates a stub page with `status: to-read`. Use for
  bulk-adding a reading list. `source_trace.transcription_method: none`.
- **Standard** (default): Read pages 1-10 (abstract, intro, method,
  conclusions) via the `Read` tool. Enough for a solid summary and
  cross-referencing. Most papers.
- **Deep**: Read the full PDF via multiple `Read` calls with the
  `pages` parameter. Use for papers central to the user's research —
  primary baselines, competitors, and papers cited extensively.

For whichever depth, extract:
- Full bibliographic metadata
- Main contribution and method
- Key equations and theorems (transcribe from source with equation
  numbers, never from memory)
- Relation to existing pages in the KB
- The exact page ranges you read — you will put these in
  `source_trace.pages_read`.

### Step 4: Create the paper page

File: `papers/{first-author}-{year}.md` (add suffix for disambiguation)

Required frontmatter: `type`, `title`, `authors`, `year`, `venue`,
`venue_type`, `bibtex_key`, `status`, `date_ingested`, `topics`, `tags`,
and `source_trace` (with `pages_read`, `transcription_method`,
`date_read`). The `source_trace` block is mandatory on any page with
`status: ingested` — empty source_trace is a hard LINT failure.

Body sections:
- **Summary** (2-4 paragraphs, sourced from the PDF)
- **Key Contributions** (bullets, sourced from the PDF)
- **Method Details** (if algorithmic, sourced from the PDF)
- **Theoretical Results** (if any: transcribe directly from the PDF
  with theorem numbers cited, e.g., "Theorem 3.1"; never from memory)
- **Relation to Our Work** (how it connects to the user's research)
- **Limitations / Open Questions**
- **Selected Equations** (key equations in LaTeX, transcribed from
  the PDF with the paper's own equation numbers cited inline,
  e.g., `Eq. 3.2`, so a reader can trace every formula to its source)

### Provenance and coverage

For concept and synthesis pages that aggregate multiple papers, add
coverage indicators to sections:

```markdown
## Convergence Theory [coverage: high]
<!-- 5+ sources support this section -->

## Extension to Nonlinear Systems [coverage: low]
<!-- Only 1 source; needs more papers -->
```

Coverage levels: `high` (5+ sources), `medium` (2-4), `low` (0-1).
This tells future readers (human or LLM) how much to trust each section
and where more ingestion is needed.

### Step 5: Update cross-references

This is what makes the KB compound. For each ingested paper:
- Add to relevant concept pages' `key_papers` lists
- Add to relevant method pages
- Add to relevant domain-specific taxonomy pages
- Create new concept/method pages if the paper introduces new ideas
- Create theorem pages if new results are proved
- Update `cites` and `cited_by` on related paper pages

### Step 6: Update navigation

- Add to `index.md` under appropriate section
- Add to `timeline.md` at correct year
- Move from "To Read" to "Ingested" in `reading-list.md`
- Add to `open-questions.md` if new gaps identified
- Add BibTeX entry to `references.bib`

### Step 7: Log the operation

Append to `log.md`: date, "ingest", paper title, files created/modified.

## Capability 3: Query the Knowledge Base

Three query depths, chosen based on the question:

### Quick query (default for simple lookups)
1. Read `index.md` to find relevant pages
2. Read those pages and synthesize an answer with markdown link citations

### Standard query (for questions requiring synthesis)
1. Read `index.md` and relevant wiki pages
2. Synthesize answer with citations
3. If synthesis is substantial, save it as a new page in `synthesis/`
4. If a gap is discovered, note it in `open-questions.md`

### Deep query (for novel research questions)
1. Search the wiki for relevant pages
2. Read raw PDFs for details not captured in summaries
3. Optionally use `semantic-scholar` skill to find additional papers
4. Create a comprehensive synthesis page with coverage indicators
5. Update `reading-list.md` with papers discovered during research

## Capability 4: Lint / Health Check

Run periodically to ensure consistency. Check:

1. **Orphan pages**: pages with no incoming links
2. **Frontmatter validation**: every page has `type` and `tags`
3. **BibTeX sync**: every paper page has a matching `references.bib` entry
4. **Bidirectional links**: if A cites B, B should reference A
5. **PDF check**: every paper with a `pdf` field points to an existing
   file (resolve the path BOTH vault-root-relative `raw/...` and
   page-relative `../raw/...`; a path that resolves neither way is missing)
6. **Navigation coverage**: every page appears in `index.md` and `timeline.md`
7. **Tag consistency**: all tags are kebab-case
8. **Dead links**: scan for markdown links pointing to non-existent files
9. **Reading list sync**: "Ingested" papers have corresponding pages
10. **Manifest sync**: every PDF on disk appears in `raw/pdfs/manifest.md`,
    and every paper page's `pdf` field has a corresponding manifest entry
11. **Source trace (HARD)**: every paper page with `status: ingested`
    must have a non-empty `source_trace` block — `pages_read`,
    `transcription_method`, and `date_read` all populated. Empty
    `source_trace` + `status: ingested` means the body was not
    verifiably sourced from the PDF. Flag as a LINT failure and
    either rewrite the body from the PDF or downgrade the page to
    `status: to-read`. This check catches the memory-reconstruction
    failure mode documented in the READ PROTOCOL.
12. **Equation provenance**: every Selected Equation on an ingested
    paper page should cite the paper's own equation / theorem number
    (e.g., `Eq. 3.2`, `Theorem 1`) so it can be traced to the source.
    Flag pages whose Selected Equations section contains no such
    citations as a soft LINT warning.
13. **Text-extraction-sourced pages need re-verification (SOFT)**:
    pages with `source_trace.transcription_method: pdftotext` were
    drafted from text-only extraction and have a higher error rate
    than `read-tool` pages (see 2026-04-29 incident below). Flag them
    so a follow-up Read-tool pass can be scheduled. The fix is to
    Read the PDF directly and update the body + frontmatter
    accordingly.
14. **Invalid `transcription_method` values (HARD)**: the field is a
    strict enum: `read-tool | pdftotext | none`. Anything else
    (e.g. `pdftotext-via-pypdf`, `read-tool-with-fallback`,
    `pymupdf`) is a hard fail — normalise to the closest enum value
    and update the `notes:` field to record the actual mechanism.
15. **Read-tool-claimed-but-no-PDF (HARD) — the fabrication signature**:
    any page with `status: ingested` and
    `source_trace.transcription_method: read-tool` whose `pdf:` does
    NOT resolve on disk (neither root- nor page-relative) could not have
    been read — the body was almost certainly reconstructed from memory.
    This single check would have caught the 2026-06-08 batch. Re-ingest
    from the PDF (`scripts/fetch_pdf.py`) or downgrade to
    `status: to-read`. `scripts/lint_kb.py` enforces checks 5, 11-15.

Report findings as a checklist. Fix automatically where possible (e.g.,
adding missing pages to index). Run `python3 scripts/lint_kb.py <vault>`
after every ingest batch; it must be clean of HARD failures.

## Capability 5: Evolve the Knowledge Base

Go beyond lint (fixing errors) to actively improve the KB. Run when the
user asks to "evolve", "improve", or "grow" the knowledge base, or
periodically after significant ingestion batches.

### Step 1: Gap analysis

Scan concept and synthesis pages for `[coverage: low]` indicators.
These are sections backed by 0-1 sources that need more papers.
Generate a prioritized list of gaps.

### Step 2: Suggest new papers

For each gap, use the `semantic-scholar` skill (if available) or web
search to find papers that could fill it. Add candidates to
`reading-list.md` under "Discovered During Research".

### Step 3: Propose new synthesis pages

Look for patterns spanning 3+ papers that don't yet have a synthesis
page. Common patterns:
- Methods compared on the same benchmark but no comparison page exists
- Multiple papers cite the same foundational work but the connection isn't explicit
- A concept is referenced in many papers but has a thin concept page

### Step 4: Identify emerging themes

Read `log.md` to see what's been ingested recently. Are there clusters
of papers on a sub-topic that deserves its own era page or taxonomy entry?

### Step 5: Update lessons learned

If anything was surprising or non-obvious during this evolve pass, append
it to `references/lessons-learned.md` in the skill directory so future
KBs benefit.

### Step 6: Report

Summarize what was found and what actions were taken. Log in `log.md`.

## Linking Conventions

**All links use standard markdown format** — no wikilinks.

From root files: `[HJB equation](concepts/hjb-equation.md)`
From subdirectories: `[HJB equation](../concepts/hjb-equation.md)`
Same directory: `[Rust (2000)](rust-2000.md)`

Display text conventions:
- Papers: `[Author (Year)](path)` — e.g., `[Kleinman (1967)](../papers/kleinman-1967.md)`
- Concepts: Natural name — e.g., `[Policy iteration](../concepts/policy-iteration.md)`
- Methods: Method name — e.g., `[Deep BSDE](../methods/deep-bsde-method.md)`

Frontmatter links use the same format:
```yaml
key_papers:
  - "[Kleinman (1967)](../papers/kleinman-1967.md)"
era: "[2020s: Neural SOC](../eras/2020s-neural-soc.md)"
```

## Lessons Learned

This section captures what works and what doesn't. Update it as the user
provides feedback or as patterns emerge.

Read `references/lessons-learned.md` for the current list.

## Error Handling

- If a PDF cannot be read: create a stub paper page with `status: to-read`
  and note the issue. Ask the user to provide an alternative format.
- If a linked page doesn't exist: create it as a stub with minimal frontmatter.
  Don't leave dead links.
- If frontmatter is malformed: fix it. Don't ask the user.
- If the vault has no CLAUDE.md: this is a new KB. Run Capability 1.

## Quality Checks

Before completing any operation:
- [ ] All new links point to existing files (or stubs were created)
- [ ] All new pages have complete frontmatter
- [ ] `index.md` is updated
- [ ] `references.bib` is updated (for paper ingestions)
- [ ] `log.md` has a new entry
- [ ] No broken relative paths (check `../` depth is correct)
