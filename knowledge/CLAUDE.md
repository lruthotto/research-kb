# CLAUDE.md — Knowledge Base (Claude-specific shim)

The schema lives in [`AGENTS.md`](AGENTS.md) in this directory.
Read it in full before editing anything under `knowledge/`.

Claude-specific ergonomics:

- The `Read` tool reads PDFs natively in up-to-20-page slices — pass the `pages` parameter (e.g. `1-20`, then `21-40`) and make multiple calls to satisfy the READ PROTOCOL's coverage requirement.
- If `Read` fails on a PDF, fall back to `pdftotext -layout <path> -` via Bash, and record `transcription_method: pdftotext` in the page's `source_trace`.
- When delegating ingestion to sub-agents, paste the READ PROTOCOL from `AGENTS.md` verbatim into the sub-agent's prompt; do not assume it will be inferred.
