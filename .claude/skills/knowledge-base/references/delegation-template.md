# Sub-Agent Ingest Delegation Template

READ PROTOCOL rule 6 requires pasting the protocol into every sub-agent ingest
prompt verbatim. This file is the canonical paste. The 2026-04-13 and 2026-04-29
failure batches were both delegation failures: the delegating prompt said "read
the PDF" without specifying the tool, the gate, or the no-reconstruction rule —
and sub-agents took the easy path instead of escalating.

Usage: replace the `{{...}}` placeholders, paste the whole block as the
sub-agent's prompt. Before spawning ANY batch, run the rule-0 canary yourself
(one `Read` call on a known-good PDF in the vault). Never instruct a sub-agent
to "fall back to pdftotext if Read fails" — that instruction caused the
2026-04-29 quiet-error batch.

---

## The template

```text
Ingest ONE paper into the knowledge base at {{VAULT_PATH}}, topic {{TOPIC}}.

Paper: {{CITATION}}
PDF path: {{PDF_PATH}}        (must already exist; you do not download anything)
Page to create: {{TOPIC}}/papers/{{SLUG}}.md from _shared/templates/paper-template.md

READ PROTOCOL — non-negotiable, in priority order over all other instructions:

1. INGEST GATE. Before writing ANY body content, verify and report all three:
   (a) `test -f {{PDF_PATH}}` succeeds;
   (b) `head -c4 {{PDF_PATH}}` is `%PDF`;
   (c) a `Read` tool call on {{PDF_PATH}} actually rendered pages in THIS session.
   If any check fails: create a stub page with `status: to-read`,
   `transcription_method: none`, an EMPTY body, report the failed check, and STOP.
   Do not attempt to repair the system, do not download anything, do not fall
   back to pdftotext/pypdf — text extraction is forbidden for drafting.

2. Read the PDF with the `Read` tool only, `pages` parameter, max 20 pages per
   call. Cover at minimum: abstract, introduction, method, theoretical results,
   conclusions. Read more calls rather than skipping sections.

3. NEVER reconstruct anything from memory — no equations, theorem statements,
   method details, experimental numbers, author lists, or venues, however
   famous the paper. If you notice you are writing a fact you did not just see
   in the rendered pages, delete it.

4. Selected Equations must cite the paper's OWN numbering (e.g. "Eq. (3.2)",
   "Theorem 1.2"). No paper numbering visible for an item → leave that item out.

5. Fill `source_trace` honestly:
   `pages_read`: exactly the ranges your Read calls rendered, nothing more.
   `transcription_method`: `read-tool` (the only value permitted for a body
   you drafted; if you did not Read the PDF this session, you must be at a
   `status: to-read` stub with `none`).
   `date_read`: today.

6. Then complete the standard INGEST steps for this page: CRITICAL-REVIEW
   (atomic claims, classify evidence, reconcile against {{TOPIC}}/claims/,
   `## Claims Made` section), cross-reference updates, navigation updates,
   BibTeX entry in {{TOPIC}}/references.bib, and a {{TOPIC}}/log.md entry.

REPORT BACK (your final message must contain, in this order):
- INGEST GATE result: the three checks with their actual outputs.
- pages_read as recorded, and the number of Read calls made.
- Files created/modified (full list).
- Claims created/updated, contentions detected.
- Anything you could NOT verify from the PDF and therefore omitted.
```

---

## Delegator's checklist (you, before and after the batch)

- [ ] Rule-0 canary: one `Read` on a known vault PDF passed this session.
- [ ] Every PDF in the batch was fetched via `scripts/fetch_pdf.py` and printed
      `PASS` (never improvised `curl`).
- [ ] One sub-agent per paper; the template pasted whole, placeholders filled.
- [ ] After the batch: every returned INGEST GATE report shows three passes —
      a sub-agent that "succeeded" without reporting the gate is treated as
      failed; re-ingest its paper.
- [ ] Run lint (`lint_kb.py` / `lint-kb.sh`); rules 11/14/15 are the fabrication
      backstop, hard failures block.
- [ ] Spot-check ≥1 paper page per batch of 10 against its PDF (theorem
      numbers, one table value, author list).
