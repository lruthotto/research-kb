# Lessons Learned

This file captures what works and what doesn't when building and maintaining
LLM-maintained academic knowledge bases. It is a distilled, reusable methodology.
When a new durable lesson is discovered, append it to the appropriate section.

## Architecture Decisions

### Use standard markdown links, not wikilinks
Obsidian-style wikilinks (`[[page]]`) don't render in VS Code, GitHub, or most
markdown viewers without plugins. Use standard `[text](relative/path.md)`
everywhere. It is more verbose but universally portable — a reader should never
need a plugin to follow a link.

### Keep the raw source layer immutable and topic-organized
Treat downloaded PDFs and other primary sources as an append-only, human-curated
layer that LLM-generated pages never modify. Organize `raw/pdfs/` by research
topic, not by year: papers in a mature field span decades, so year-based folders
produce many single-file directories, and researchers recall work by topic
("that policy-iteration paper") rather than date. A chronological view belongs in
a generated `timeline.md`, not in the folder structure.

### Only include pages that belong to the domain
Only create a page for something that is genuinely an instance of what the KB
tracks. Tangentially related work — a benchmark borrowed from a neighboring
field, an adjacent method used only as a baseline — should be mentioned in prose
on relevant pages, not given its own page. The test: "Is this an instance of the
thing this KB exists to track?" If not, it dilutes the vault and creates
confusion.

### Domain-specific page types add real value
Generic page types (papers, concepts, methods) are necessary but rarely
sufficient. At scaffolding time, actively ask what domain-specific taxonomies
would help. Examples by field: problem-classes and benchmarks for an
optimization/control KB; datasets and architectures for an ML KB; conjectures and
proof techniques for a pure-math KB. Building the right typed pages early shapes
how everything cross-references later.

### Frontmatter links in YAML are verbose but necessary
YAML frontmatter carrying markdown links is visually noisy
(`"[Author (Year)](../papers/author-year.md)"` versus a bare wikilink). Accept
the verbosity: the alternative breaks outside one specific editor, and
frontmatter is machine-read anyway.

## Ingestion Patterns

### Read the source, don't just extract metadata
Metadata-only ingestion (title, authors, year) produces thin pages. The value of
a KB comes from the summary, the extracted contribution and method, and the
cross-references those enable. Always read the actual source (at minimum the first
several pages) before writing a page body.

### Prior knowledge is never a substitute for reading the source
This is the single highest-impact failure mode. When an agent drafts a page for a
famous paper from its own prior knowledge instead of reading the PDF, the output
*looks* authoritative — formatted, with theorem and equation numbers — but audits
repeatedly find a large fraction of such pages contain substantive errors:
wrong-sign equations, fabricated or misattributed theorems, missing authors, wrong
equivalence-class counts, central namesake equations omitted entirely, and
experimental numbers that contradict the paper. Some pages were even written for
sources that had no file on disk at all — they could not have been read.

Root causes and the controls that fix them:

1. **Vague tool instructions.** A prompt that says "read the PDF" without naming
   the tool lets the agent default to whatever rendering it finds, then silently
   fall back to memory when that fails. Fix: a **READ PROTOCOL** at the top of the
   ingest capability — render the PDF with the `Read` tool first, never
   reconstruct from memory — and when delegating, paste the protocol verbatim
   into the sub-agent prompt.
2. **No audit trail.** Without a provenance record on the page there is no way to
   lint for the failure. Fix: a **`source_trace`** frontmatter block recording
   `pages_read`, `transcription_method`, and `date_read`. An empty `source_trace`
   on a page marked `status: ingested` is a hard lint failure.
3. **No precondition check.** Fix: an **ingest gate** — write a body only after
   the source file is on disk, is a valid file (e.g. a real PDF, validated by
   header and plausible size, not an HTML error page saved with a `.pdf`
   extension), and a `Read` call actually rendered it this session. Otherwise the
   page becomes a `status: to-read` stub with no body, and the agent stops.

Add an **equation-provenance** soft lint rule too: "Selected Equations" should
cite the paper's own equation/theorem numbers so any formula can be traced back
to its source.

**Watch signals** for recognizing this failure in an existing page without
re-reading the source:
- No equation numbers cited in "Selected Equations" (generic `\frac{...}` rather
  than `Eq. 3.2`).
- Generic phrasing in method details ("the paper shows", "as is standard")
  without concrete mechanisms.
- A missing source path, or one pointing to a file not on disk.
- An empty or stub theoretical-results section on a page marked ingested,
  especially for a theory paper.
- Non-specific experimental numbers ("large speedup", "matches full precision")
  with no dataset or exact values.

### Text-extraction fallbacks are not safe substitutes for `Read` on PDFs
Command-line extractors (`pdftotext`, `pypdf`, and similar) are unsafe for
drafting page bodies because they lose column boundaries, table alignment, and
math symbols. Pages drafted from extracted text *look* complete but introduce a
characteristic class of errors: transposed table rows (a result flipped to the
wrong direction), off-by-one exponents and subscripts, baseline comparisons
attributed to the wrong column, and tilde/hat notation dropped. Catching these
requires a `Read`-tool pass against the rendered PDF, which sees columns, symbols,
and table layout correctly.

Controls:
- **Canary the renderer before a batch.** When orchestrating a parallel ingest,
  the orchestrator must run `Read` on a known-good PDF *before* delegating. If it
  fails, fix the environment first. Note that a binary's PDF-availability check
  can cache its first result for the process lifetime, so installing the missing
  tooling mid-session may not recover — restart the session.
- **Restrict extractors to verification, not drafting.** `pdftotext`/`pypdf` are
  acceptable only for verification or lint queries ("does this PDF mention X?"),
  never for writing an ingested body. If `Read` cannot work this session, the page
  becomes a `to-read` stub.
- **Constrain `transcription_method` to a strict enum** (e.g. `read-tool |
  pdftotext | none`). An honest `pdftotext` value triggers a soft lint warning
  (re-verification needed); an invented value (`pdftotext-via-pypdf`) is a hard
  failure. Add a lint rule that flags every `pdftotext`-sourced ingested page for
  follow-up `Read`-tool re-verification.
- **Persist tooling in the environment image** (e.g. the devcontainer/Dockerfile)
  so a rebuild doesn't silently drop the renderer.

Detection heuristics without re-reading: `transcription_method: pdftotext` on a
page with theorems or tables; any out-of-enum value; column-bleed artifacts in
body text (a table caption interrupted mid-sentence by reference numbers from the
neighboring column); equations paraphrased rather than cited by number.

### Stubs must stay empty — no memory-drafted prose
A separate gray zone: an agent correctly refuses to draft a body it cannot verify,
creates a `to-read` stub, then fills "harmless" overview fields (key
contributions, a relevance note) from memory anyway. Protocol compliance is
binary, but page sections are not — agents treat "create a stub and stop" as
license to populate descriptive fields. Anything descriptive of a source's
content belongs behind the read gate. Add a lint rule: substantive content in
content-bearing sections (Selected Equations, Theoretical Results, Method
Details) on a `to-read` page is a hard failure; descriptive prose in
Summary/Key-Contributions on such a page is a soft failure.

### Ingest in batches, but cross-reference one at a time
Parallel agents are efficient for independent sources, but simultaneous ingestion
makes it harder to ensure the new pages cross-reference *each other*. Run a
dedicated cross-reference pass after a batch, and let the lint check catch the
missing links.

### Delegate the READ PROTOCOL verbatim to sub-agents
When delegating ingestion to sub-agents, paste the READ PROTOCOL and the ingest
gate into the prompt verbatim. Sub-agents follow the instructions they are given;
a prompt that merely references a protocol, or that lists an unsafe fallback as
"acceptable if Read fails", will be taken at face value and the safe path
abandoned.

## Cross-Referencing

### The value is in the updates, not the initial page
A single source ingestion should touch many existing pages (a useful rule of
thumb: 5-15). If ingesting one source only creates one new page, the
cross-referencing is too shallow. The compounding value of a KB comes from
updating existing concept, method, and timeline pages to point at the new work.

### Bidirectional links require discipline
It is easy to add `cites: [paper-A]` to paper-B and forget the reciprocal
`cited_by: [paper-B]` on paper-A. Don't rely on memory — let the lint check find
the asymmetry, and run it after every batch ingestion.

### Propagate back-links down to the claim level, not just the paper level
A common structural defect: claim pages are reachable from their paper pages but
no concept or method page links to any claim. The ingest instruction "update
existing concept/method pages with back-links" gets interpreted as paper-level
back-links (`key_papers:`) only. Fix: give concept and method pages a
`## Key Claims` section listing the claims they host, as
`[short sentence](../claims/file.md) — one-line gloss`, and populate it during
ingest rather than deferring to a later lint pass.

## What Doesn't Work

### Don't over-create author pages
Creating a page for every co-author produces many thin pages that add noise
without value. Only create an author page for a researcher with multiple papers
in the KB, or one who is historically foundational to the field.

### Don't include non-domain pages
Tangentially related work dilutes the KB. Mention it in prose on the relevant
page; don't give it a page unless it is genuinely in scope. (Same principle as
the domain-scope architecture decision, restated as an anti-pattern because it is
a recurring temptation during ingest.)

### Don't use the KB for ephemeral project state
It is tempting to track "current experiment results" or "TODO before submission"
in the vault. The KB is for durable knowledge. Use issues, task lists, or project
plans for ephemeral state — otherwise stale status notes accumulate as permanent
noise.

## Patterns from the Scientific Community

### Citation-graph tools discover; an LLM KB synthesizes
Citation-graph and academic-graph services are powerful for discovery but do not
synthesize. The LLM KB adds the synthesis layer ("what does this mean for our
work?") on top of citation structure. Consider integrating an academic-graph API
for automated, accurate metadata extraction during ingestion.

### Zettelkasten with maintained links
The typed concept-page structure (parent/child/related) is essentially a
Zettelkasten with enforced types. The decisive difference: the LLM maintains the
links, not the human. This removes the maintenance burden that causes people to
abandon hand-maintained note systems.

### Coverage indicators solve the trust problem
Marking sections with `[coverage: high/medium/low]` based on source count tells a
reader whether to trust a summary or go to the raw source, and tells the maintainer
where the gaps are.

### Error accumulation is the biggest long-term risk
Once wrong information enters the wiki, future updates build on it. Mitigations:
always link back to raw sources, transcribe theorems and equations directly from
the source (never from memory), and use coverage indicators so low-confidence
content is visibly low-confidence.

### Keep the raw layer strictly separate from generated content
Keep human-curated sources (`raw/`) strictly separated from LLM-generated wiki
pages, and never let generated content contaminate the raw layer. The `status`
field distinguishes ingestion quality. Because the vault is just markdown plus
source files, it is data-source-agnostic and survives any single tool's demise —
a deliberate design goal.

### LLM notes are a navigation layer, not a replacement for personal notes
A reasonable counter-argument holds that the point of taking notes is to write
them in your own words, so an LLM should not write them for you. That is valid for
personal learning. The LLM-KB use case is different: a navigational and synthesis
layer over a research corpus, not a substitute for personal comprehension. Both
can coexist.

## Parallel Audit Patterns

### Structure audits as iterative waves of <=3 parallel sub-agents
Running more than ~3 sub-agents in parallel makes behavior-monitoring and
prompt-iteration impractical; running strictly sequentially forfeits a large
speedup on non-overlapping vaults. The pattern that works: dispatch 2-3 agents on
non-overlapping vaults per wave; between waves, read the reports and fold their
findings into the next wave's prompt; recycle any auto-fix template that proved
successful into the next wave's standing task.

### A fixed structured-report template is load-bearing
Require every sub-agent to return its findings in one exact template (lint summary
line-per-rule, auto-fixes applied, flagged issues by category, claim-overlap
clusters, missing-synthesis candidates, potential debates, cross-topic hooks,
coverage gaps, summary statistics). A fixed schema is scannable across many
reports, lets you compare the same field across vaults, and makes the next wave's
prompt trivial to write. Without it, reports drift into prose and post-run
synthesis becomes painful.

### State auto-fix vs report-only scope explicitly in every prompt
Enumerate what a sub-agent may and may not edit; do not rely on it inferring the
boundary. A working split: **auto-fix** navigation coverage, missing
bidirectional links, manifest entries for already-filed sources, tag-case
normalization, trivial frontmatter gaps, and dead links to near-matching
filenames; **report-only** empty `source_trace`, missing equation provenance,
orphan claims, suspected factual errors in bodies, and cross-topic duplicates
(these need source re-reads or judgment that exceed an auto-fix's scope).

### Promote a cheap KB-wide fix to a first-class operation
When a sub-agent discovers a cheap, mechanical fix for a pattern that recurs
across the vault (for instance, deorphaning claims by adding `## Key Claims`
sections to hub pages), promote it from an incidental auto-fix to the explicit
primary task of the next wave, rather than rediscovering it one vault at a time.

### Precompute counts before dispatching
Before sending a sub-agent to audit a vault, run a few grep passes in the main
agent to precompute paper count, claim count, orphan-claim count, and
empty-`source_trace` count, and include them in the prompt. This saves the
sub-agent several exploration queries and gives you a consistency check: its stat
summary should match your precomputed numbers.

### Delegate editing, keep the overview
The orchestrating agent should write very little content. It coordinates, makes
cheap cross-vault edits (connection indexes, the root log), and receives
structured reports; all vault-internal edits — synthesis pages, hub pages, lint
auto-fixes — are better done by scoped sub-agents with explicit boundaries, so the
orchestrator's context stays clean for cross-vault synthesis. End each wave with a
short (<=10 line) status summary to the user: what completed, key numbers, what's
next — results, not deliberation.

## KB Architectural Patterns (Discovered via Audit)

### Hub-page absence drives orphan and dead-link patterns
Many orphan claims and dead links exist not because a hub page failed to link
them, but because the hub page does not exist. Frontmatter and inline links point
at concept/method hubs that were named in the topic's CLAUDE.md as "build later"
but never created. Creating one hub page can deorphan a dozen claims in a single
edit because it consolidates what was scattered across many paper pages.
Scaffolding implication: at topic-creation time, pre-create empty
frontmatter-only stubs for every hub page the topic spec lists — a one-line
description and an empty `## Key Claims` section ready to fill during ingest. This
prevents both the claim-in-limbo pattern and ad-hoc hub creation that drifts from
the intended ontology.

### Cross-topic duplicate papers are non-obvious
The same paper independently ingested under two topics can hide behind different
filenames and different bibtex keys, making it invisible to filename-based and
bibtex-based lint. Only a content-level comparison catches it. Detection
heuristic: grep other topics' paper frontmatter for the same `arxiv:` or `doi:`
identifier — both are short, unique strings, so this is cheap. Non-destructive
resolution: keep both pages if the policy allows a paper to live in two topics via
mutual linking, but unify the bibtex key, add a `cross_listing:` field pointing at
the primary home, and copy the better-populated `source_trace` to both.

### Duplicate claim pairs from re-ingestion
Re-ingesting a partially-ingested paper in a later session can create
near-duplicate claim pages that differ only by a hyphen or a synonym in the slug.
Detection: grep claim filenames for hyphen/synonym variants. Resolution: count
inbound references to each, keep the one referenced from the index, paper pages,
and unrelated claims (not just its duplicate sibling), rewire external references
to the winner, and delete the loser. Prevention: before creating new claim files
for a paper that may have been ingested before, list the claims directory and grep
for title-stem matches first.

### `source_trace` backfill: distinguish log-documented from no-history
An empty `source_trace` on an ingested paper can mean two very different things,
and they are distinguishable cheaply by grepping the topic log for the paper:
1. **Log-documented re-read** — the log records a re-read on a date but the
   frontmatter block was never written. Remedy: copy the log details (pages read,
   what was verified) into the frontmatter; no source access needed. Batchable.
2. **No re-read history** — the page was drafted from memory and the log has no
   re-read entry. Remedy: a fresh read per the READ PROTOCOL. Space these out.

Triage on this distinction: the log-documented cases can be batch-backfilled in
one session; the no-history cases need real re-reads.

### Don't fabricate per-paper detail from a batch-only log entry
Some log entries describe a re-read *batch* without per-paper enumeration. When
backfilling `source_trace` from these, do not invent per-paper details. Note
explicitly in a `notes:` field that the log entry is batch-only and page-level
details were not logged. This preserves provenance integrity — a future auditor
knows to re-read the source if they need specifics.

### bibtex_key casing drifts without enforcement
If the bibtex-key convention is not enforced at write time, topics accumulate a
mix of camelCase, PascalCase, and snake_case keys, and the drift is progressive.
Either add a lint rule that enforces one casing, or pick the convention many
bibtex managers produce by default (PascalCase is the more human-readable choice),
state it explicitly in the spec, and allow it uniformly. Decide once and write it
down; ambiguity guarantees drift.

### Guard schema-invariant files against global ignore rules
A user-global gitignore can silently break a KB invariant — for example a global
`*.bib` rule prevents `references.bib` from ever being committed, so every fresh
clone fails lint. Add an explicit negation (`!references.bib`) to the repo
`.gitignore` and commit the file. Worth checking in any new KB repo.

### Port fixes between vendored and skill copies in the same change
When a lint script or protocol is both vendored into a project repo and held in a
reusable skill, a fix applied to one copy drifts from the other. When you fix a
vendored copy, port the change to the skill copy (and vice versa) in the same
change, so the two never diverge.

## Deep-Analysis Task Patterns

### Bundle lint with deep analysis in one sub-agent pass
Mechanical lint (correctness) and deep analysis (claim clusters, synthesis
proposals, debates, coverage gaps) reinforce each other: lint gives the agent a
full inventory before it analyzes, and the analysis retroactively justifies the
lint work (knowing a claim cluster is under-synthesized makes an orphan finding
actionable). Keep them in one pass per vault unless a vault is so large the
combined run would exceed the agent's context.

### Claim-overlap clusters reveal synthesis pages organically
Asking "which claim pages describe the same or closely-related facts?" is the
highest-leverage deep-analysis question: every cluster of >=3 claims is a synthesis-
page candidate, and every cluster of >=5 is nearly certain to warrant one. This
outperforms asking for "missing synthesis pages" directly, because from-scratch
synthesis proposals tend to invent plausible but unsupported themes, whereas
clusters are evidence-driven.

### Rank coverage gaps by inbound citation edges
"What is the most blocking missing paper?" is vague. "Which to-read paper has the
most inbound `cites:` edges from already-ingested papers?" gives a numerically
rankable list computable by grep with no LLM synthesis: papers with many inbound
edges are clear top priorities; papers with zero or one are lower tiers.

## Agent-Neutrality Patterns

### An agent-neutral contract can work across agents — verify it
A KB whose conventions live in an agent-neutral contract (a root instructions file
plus thin per-agent shims) can be operated by agents other than the one it was
built for: a non-native agent can preload the contract, read the KB-local
instructions before editing, execute a faithful ingest, and — under explicit
pressure to memory-draft a paywalled paper — refuse and produce a `to-read` stub,
citing the READ PROTOCOL. Don't assume portability; run a hands-on fitness test
against each new agent, spot-checking ingested items against the source and
probing the refusal path directly. Such a test is also how the
stub-with-memory-prose gray zone above was first found.
