# Quick Start — Your First Paper, End to End

This walks you through ingesting one paper into your knowledge base under the
READ PROTOCOL: fetch a validated PDF, have an AI coding agent read it from disk and
write a sourced page, watch the `source_trace` get recorded, then prove it with the
deterministic lint.

The whole point of the sequence below is that **nothing gets written from memory.**
A real PDF is on disk, it was actually read, and the lint can confirm both.

---

## Before you start

- **Python deps:** `python3 -m pip install -r scripts/requirements.txt`
  (`PyYAML` for the lint, `pypdf` so `fetch_pdf.py` can report page counts).
- **An AI coding agent** open in this repo's root — Claude Code, or a CLI coding
  agent. It needs filesystem access and a tool that can **render** PDF pages (read
  them as images), not just extract text.
- **PDF rendering works.** The Read-style tool shells out to `pdftoppm`
  (poppler-utils). On a fresh machine this is often missing. Install it
  (`brew install poppler` on macOS, `apt-get install -y poppler-utils` on
  Debian/Ubuntu) and confirm with `pdftoppm -v`. If your agent caches the
  "not installed" result, restart it after installing.

All commands below are run from the repo root.

---

## Step 1 — Fetch a PDF (must print PASS)

Use `scripts/fetch_pdf.py`. It downloads from an arXiv id/URL or a direct PDF URL,
validates the result (real `%PDF` header, plausible size, not an HTML
captcha/landing page), and **fails loudly** instead of silently saving a 404 page
as a `.pdf`. Choose a topic subfolder and an `author-year-keyword` filename:

```bash
python3 scripts/fetch_pdf.py 2009.02994 \
    --out knowledge/raw/pdfs/your-topic/author-2020-keyword.pdf
```

On success it prints one `PASS` line and a ready-to-paste manifest row:

```
PASS path=/.../author-2020-keyword.pdf bytes=842197 sha256=ab12… pages=24 url=https://arxiv.org/pdf/2009.02994
MANIFEST_ROW | author-2020-keyword.pdf | https://arxiv.org/pdf/2009.02994 | fetched 2026-06-17 (arxiv) |
NEXT: canary the Read tool on this exact path before writing ANY body content...
```

**If it prints `FAIL`, you have no PDF.** Do not proceed to a body. Retry later
(arXiv may be rate-limiting), pass a direct PDF URL, or download the file manually
and point `--out` at it. The READ PROTOCOL treats a `FAIL` exactly like "no PDF":
the page stays a `status: to-read` stub.

## Step 2 — Record the PDF in the manifest

PDFs are gitignored, so the manifest is how a teammate re-obtains them after a
clone. Paste the `MANIFEST_ROW` line into `knowledge/raw/pdfs/manifest.md` (create
it if missing, with a table header). The lint cross-checks disk against this file.

## Step 3 — Open your agent and prompt the ingest

With the agent open in the repo root, give it a prompt like:

> Ingest `knowledge/raw/pdfs/your-topic/author-2020-keyword.pdf` into this
> knowledge base following `knowledge/AGENTS.md`. Obey the READ PROTOCOL: canary
> the Read tool on that exact path first; only write a body if the PDF renders;
> transcribe equations and theorem statements directly from the PDF with the
> paper's own numbers; fill the `source_trace` block honestly. If the PDF does not
> render, create a `status: to-read` stub and stop.

The agent should, in order: **(1)** Read the PDF path to confirm it renders (the
"canary"); **(2)** pass the INGEST GATE — file on disk, valid PDF, Read actually
rendered it this session; **(3)** write `knowledge/papers/author-2020.md` with
sourced Summary / Key Contributions / Method / Theoretical Results / Selected
Equations; **(4)** update cross-references, `index.md`, `references.bib`, and `log.md`.

If PDF rendering is broken, the *correct* behavior is a stub with an empty body —
not a confident summary. That refusal is the contract working.

## Step 4 — Watch the `source_trace` get written

Open the new page. Its frontmatter should carry an honest audit trail:

```yaml
---
type: paper
title: "…"
authors: ["…"]
year: 2020
status: ingested
pdf: "raw/pdfs/your-topic/author-2020-keyword.pdf"
source_trace:
  pages_read: "1-10, 18-22"        # the ranges actually read
  transcription_method: read-tool  # read-tool | pdftotext | none
  date_read: 2026-06-17            # the session that read the PDF
  notes: "Transcribed Eq. 3.2 and Theorem 1 from the PDF."
tags: [paper]
---
```

`transcription_method: read-tool` is only honest if a Read call truly rendered this
PDF this session. The lint in the next step is what keeps that honest.

## Step 5 — Run the lint

```bash
bash scripts/lint-kb.sh knowledge
```

For a correctly ingested page you want **0 HARD issues**. Early-stage warnings
(empty page-type directories, an orphan page with no incoming links yet) are
expected and harmless. Re-run after every ingest batch.

---

## What a violation looks like

The lint is designed to catch the exact ways an ingest goes wrong:

- Agent wrote a body but left `source_trace` empty →
  `SOURCE_TRACE MISSING: … status:ingested but source_trace.* is empty`.
- Agent recorded `read-tool` but the PDF is not on disk (or `pdf:` doesn't resolve)
  → `READ-TOOL BUT NO PDF: … the page could not have been read` (the
  memory-reconstruction signature).
- Agent left a `status: to-read` stub but slipped equations into it →
  `STUB WITH BODY: … a page that was never read can only have been drafted from
  memory`.
- A PDF on disk isn't in the manifest → `MANIFEST MISSING: …`.

Any of these is a **HARD** failure (exit code 1). Fix it by re-ingesting from the
PDF or downgrading the page to `status: to-read` — then re-run the lint until it is
clean. That clean run is your auditability guarantee.
