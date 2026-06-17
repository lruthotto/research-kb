---
type: schema
tags:
  - schema
---

# AGENTS.md — Knowledge Base Schema for <your-topic>

This file is the **agent-neutral source of truth** for the schema, read protocol, and operations that govern this knowledge base.
Any CLI agent (Claude Code, GitHub Copilot, OpenAI Codex CLI, Google Gemini CLI, Aider, etc.) MUST follow it when reading or writing inside `knowledge/`.

The companion file [`CLAUDE.md`](CLAUDE.md) is a thin pointer that adds Claude-specific ergonomic hooks.
Agent shims at the repo root ([`../AGENTS.md`](../AGENTS.md), [`../CLAUDE.md`](../CLAUDE.md)) also redirect here.

## What This Vault Is

An auditable, LLM-maintained research knowledge base for **<your-topic>** — a navigable wiki of atomic claims, papers, concepts, methods, theorems, and debates in which every substantive statement is traceable to a source read in-session.
This is a content-free starter skeleton; populate it with your own sources via the INGEST operation below.

The vault uses **standard markdown links** (not Obsidian wikilinks) so it works in any editor or viewer without plugins.

## Vault Philosophy

1. **Claims, not summaries.** Knowledge accumulates in atomic `claims/` pages with explicit evidence and status.
   Paper pages link claims; they do not own them.
2. **Contentions are first-class.** Disagreements between sources get `debates/` pages, not hedged summary language.
3. **The graph is navigable everywhere.** Standard markdown with relative paths; no plugin or proprietary viewer required.
4. **Textbooks are sources, not containers.** A book's value materialises in the claim / concept / method / theorem layer.

## READ PROTOCOL (blocking precondition for every body section)

Every substantive claim on a paper page — summary, method details, theorem statements, transcribed equations, limitations — MUST be sourced from the actual PDF **in this session**, not from prior knowledge of the paper.
"I know this paper" is never an acceptable source.

- **PDF must be on disk and readable before any body content is written.** If the PDF is missing, create a stub with `status: to-read` and STOP.
- **Read the PDF directly.** Use whatever PDF reading affordance your agent provides (Claude Code's `Read` tool reads PDFs natively in 20-page slices; other agents typically use `pdftotext -layout <path> -` via shell).
  Always cover at least abstract, introduction, method, theoretical results, and conclusions.
- **Never reconstruct equations, theorem statements, method details, or experimental numbers from memory.** Memory-drafted pages have a high error rate even for famous papers.
- **Record your source trace.** Every paper page's frontmatter MUST include a `source_trace` block:

  ```yaml
  source_trace:
    pages_read: "1-12, 18-20"
    transcription_method: "read-tool"   # enum: read-tool | pdftotext | none
    date_read: 2026-01-01
  ```

  Empty `source_trace` + `status: ingested` is a hard lint failure.

## Standard Page Types

Full templates live in `templates/`.

- **Paper** (`papers/`), **Book** (`books/{slug}/`), **Concept** (`concepts/`), **Method** (`methods/`), **Problem class** (`problem-classes/`), **Benchmark** (`benchmarks/`), **Author** (`authors/`), **Era** (`eras/`), **Theorem** (`theorems/`), **Synthesis** (`synthesis/`), **Code link** (`code-links/`), **Claim** (`claims/`), **Debate** (`debates/`).

Each page carries YAML frontmatter with at least `type` and `tags`; see the corresponding file in `templates/` for required and optional fields per type.

## Operations

### INGEST

1. Classify and file the PDF into `raw/pdfs/<subtopic>/`.
   Naming: `{first-author}-{year}-{short-keyword}.pdf`.
   Update `raw/pdfs/manifest.md` with the source URL so the PDF can be re-obtained after cloning.
2. Verify the PDF is readable in this session.
3. Read abstract, introduction, method, theoretical results, conclusions.
4. Create the paper page from `templates/paper-template.md`.
   Fill `source_trace`.
   Cite the paper's own equation numbers in `Selected Equations` (e.g. `Eq. 3.2`, `Theorem 1`).
5. Run CRITICAL-REVIEW.
6. Update concept / method / benchmark / author / era pages.
7. Update navigation (`index.md`, `timeline.md`, etc.).
8. Add the BibTeX entry to `references.bib`.
9. Log in `log.md`.

### CRITICAL-REVIEW

1. Extract every substantive assertion atomically.
2. Classify by evidence type (`math-proof`, `numerical`, `empirical`, `heuristic`, `conjecture`).
3. Reconcile against `claims/`.
   Add this paper to a matching claim's `supported_by` or `contradicted_by`, or create a new claim.
4. Detect contentions.
   Don't silently downgrade.
   Open or extend a `debates/` page.
5. Append `## Claims Made` to the paper page.
6. Bias-check the paper's characterisation of cited prior work against this vault.

### SYNTHESIZE

Manually triggered.
Drives a synthesis page from the claim graph grouped by status (proven → empirical → conjectured → contested), not from paper chronology.

### QUERY

Read the relevant `index.md`, answer with markdown link citations, save new synthesis as a `synthesis/` page if substantial, log gaps to `open-questions.md`.

### LINT

Run `bash ../scripts/lint-kb.sh` from any agent or shell.
Hard failures must be fixed; soft warnings should be triaged.
The hard checks include: every paper page with `status: ingested` must carry a non-empty `source_trace` block, every page must have `type` and `tags`, and all markdown links must resolve.

## Naming Conventions

- **Files**: lowercase, kebab-case.
  No spaces, no underscores.
- **Tags**: lowercase, kebab-case.
- **BibTeX keys**: `{lastname}{year}{keyword}` in camelCase.

## Linking Conventions

Standard markdown links only, with relative paths from the file containing them. A link is display text in square brackets followed by the relative path in parentheses.

- From the vault root: point to the slug file under `concepts/`, `methods/`, etc.
- From a subdirectory: climb to the vault root first with a `../` prefix.
- Same directory: use just the filename.

Display text: papers as `Author (Year)`; concepts/methods/benchmarks as natural capitalised name; claims as a short descriptive sentence fragment; debates as the question form of the contention.
Frontmatter links use the same markdown form.

## PDFs Are Not Tracked

The repo's root `.gitignore` excludes `*.pdf` and `**/raw/pdfs/**/*.pdf`.
`raw/pdfs/manifest.md` lists URLs / DOIs so any cloned copy can re-fetch the sources.

## Multi-agent Notes

This file is the canonical schema.
Agent-specific shims at the repo root all redirect here.
If you are a CLI agent and you find yourself looking at this file because of a redirect: this is the right place.
Read it in full before making any edits inside `knowledge/`.
