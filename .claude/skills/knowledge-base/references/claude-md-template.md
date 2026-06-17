# CLAUDE.md Template for Knowledge Bases

Copy and customize this template for each new knowledge base vault.
Replace `{{placeholders}}` with domain-specific content.

---

```markdown
# CLAUDE.md — {{DOMAIN_NAME}} Knowledge Base Schema

This file instructs an LLM on how to maintain this academic research
knowledge base. The domain is {{DOMAIN_DESCRIPTION}}.
The vault uses **standard markdown links** (not Obsidian wikilinks)
so it works in any editor or markdown viewer without plugins.

## Vault Overview

Three-layer architecture adapted from the LLM Wiki pattern:

1. **Raw sources** (`raw/`): Immutable PDFs and web clips. Never modified.
2. **Wiki pages** ({{PAGE_DIRECTORIES}}): LLM-generated and human-edited
   markdown with YAML frontmatter.
3. **Schema** (this file): Instructions for maintenance.

Navigation files: `index.md`, `timeline.md`, `open-questions.md`,
`reading-list.md`, `connections.md`.

Master bibliography: `references.bib` (BibTeX format).

{{#if RELATED_CODEBASE}}
Related codebase: `{{RELATED_CODEBASE}}`.
{{/if}}

## Operations

### INGEST — Adding a new paper

**READ PROTOCOL (blocking precondition).**
Every substantive claim on a paper page — summary, method details,
theorems, transcribed equations, limitations — must be sourced from
the actual PDF in this session, not from prior knowledge of the
paper. "I know this paper" is never acceptable as a source.

- **PDF-first, no PDF → no body.** Verify the PDF exists on disk and
  is readable via the `Read` tool (or `pdftotext -layout <path> -` as
  a fallback) **before** writing any body section. If the PDF cannot
  be obtained, create a stub with `status: to-read` and STOP.
- **Use `Read` on the PDF path.** `Read` supports PDFs natively. For
  papers over 10 pages, pass the `pages` parameter (max 20 per call)
  and make multiple calls to cover abstract, intro, method, theory,
  and conclusions at minimum.
- **Never reconstruct from memory**, even for famous papers. Famous
  papers are exactly where silent errors accumulate.
- **Delegating to sub-agents:** paste this READ PROTOCOL verbatim
  into the sub-agent's prompt. Do not assume the sub-agent will
  infer it.
- **Record the source trace.** Every ingested paper page's frontmatter
  must have a populated `source_trace` block (`pages_read`,
  `transcription_method`, `date_read`). Empty `source_trace` +
  `status: ingested` is a hard LINT failure.

**Workflow.**

1. **Classify and file the PDF**
   - Place in `raw/pdfs/{topic}/` where topic is one of:
     {{PDF_TOPICS}}
   - Naming: `{first-author}-{year}-{short-keyword}.pdf`
   - Update `raw/pdfs/manifest.md` with the source URL so the PDF
     can be re-obtained after cloning.

2. **Verify the PDF is readable in this session.** Call `Read` on
   the PDF path. If `Read` fails, run `pdftotext -layout <path> -`
   via Bash. If both fail, create a `status: to-read` stub and
   STOP — do not write body content.

3. **Read the paper.** Cover abstract, introduction, method,
   theoretical results, and conclusions at minimum. Record the
   exact page ranges — they go in `source_trace.pages_read`.

4. **Create the paper page** in `papers/`
   - Filename: `{first-author-lastname}-{year}.md`
   - Fill complete YAML frontmatter including the `source_trace`
     block
   - Write body sections: Summary, Key Contributions, Method
     Details, Theoretical Results (with theorem numbers cited, e.g.
     "Theorem 3.1"), Relation to Our Work, Limitations, Selected
     Equations (with the paper's own equation numbers cited inline,
     e.g. `Eq. 3.2`)

5. **Update existing pages**
   - Add links to relevant concept/method/{{DOMAIN_PAGES}} pages
   - Create new pages if the paper introduces new ideas
   - All links must use standard markdown with relative paths

6. **Update navigation files**
   - Add to `index.md`, `timeline.md`, `reading-list.md`
   - Add BibTeX entry to `references.bib`

7. **Log the operation** in `log.md`

### QUERY — Answering questions

1. Read `index.md` to find relevant pages
2. Synthesize answer with standard markdown link citations
3. Save substantial syntheses as new pages in `synthesis/`

### LINT — Health check

1. Orphan pages (no incoming links)
2. Frontmatter validation (every page has `type` and `tags`)
3. BibTeX sync (paper pages match `references.bib`)
4. Bidirectional links
5. Dead link check (all markdown links resolve)
6. Navigation coverage (all pages in `index.md` and `timeline.md`)
7. Tag consistency (kebab-case)
8. **Source trace (HARD)**: every paper page with `status: ingested`
   must have a non-empty `source_trace` block. Empty source_trace on
   an ingested page is a hard failure — the body was not verifiably
   sourced from the PDF and must be rewritten or the page downgraded
   to `status: to-read`.
9. **Equation provenance**: Selected Equations on ingested paper
   pages should cite the paper's own equation / theorem numbers
   (e.g. `Eq. 3.2`, `Theorem 1`). Pages without such citations get
   a soft warning.

## Page Type Definitions

### Paper (`papers/`)
Required: `type`, `title`, `authors`, `year`, `venue`, `venue_type`,
`bibtex_key`, `status`, `topics`, `tags`

Optional: `doi`, `arxiv`, `pdf`, `date_ingested`, `methods`,
{{DOMAIN_FRONTMATTER_FIELDS}}, `cites`, `cited_by`, `era`,
`relevance`, `relevance_note`

### Concept (`concepts/`)
Required: `type`, `title`, `category`, `tags`

Optional: `aliases`, `first_appearance`, `key_equation`,
`parent_concepts`, `child_concepts`, `related_concepts`, `key_papers`

### Method (`methods/`)
Required: `type`, `title`, `tags`

Optional: `aliases`, `category`, `introduced_in`, `parent_methods`,
`child_methods`, `key_papers`, `convergence_rate`

{{DOMAIN_SPECIFIC_PAGE_TYPES}}

### Author (`authors/`)
Required: `type`, `name`, `tags`

Optional: `affiliation`, `homepage`, `scholar`, `research_areas`,
`key_contributions`, `papers_in_wiki`

### Era (`eras/`)
Required: `type`, `title`, `decade`, `tags`

Optional: `theme`, `predecessor`, `successor`, `key_developments`

### Theorem (`theorems/`)
Required: `type`, `title`, `statement_type`, `tags`

Optional: `formal_statement`, `assumptions`, `conclusion`,
`convergence_rate`, `proved_in`, `extends`, `extended_by`

### Synthesis (`synthesis/`)
Required: `type`, `title`, `scope`, `tags`

Optional: `subjects`, `key_papers`, `date_created`, `date_updated`

## Naming Conventions

- **Files**: lowercase, kebab-case. `kleinman-1968.md`, `hjb-equation.md`
- **Tags**: kebab-case. `paper`, `concept`, `neural-soc`
- **BibTeX keys**: `{lastname}{year}{keyword}` camelCase.

## Linking Conventions

Standard markdown links only. Relative paths from the file containing them.

From root: `[Name](concepts/name.md)`
From subdirectory: `[Name](../concepts/name.md)`
Same directory: `[Name](name.md)`

Papers use Author (Year): `[Kleinman (1967)](../papers/kleinman-1967.md)`

Frontmatter links use same format:
\```yaml
key_papers:
  - "[Kleinman (1967)](../papers/kleinman-1967.md)"
\```

## Graph and Navigation

Navigable via `index.md` (topic-organized), `timeline.md` (chronological),
`connections.md` (cross-domain). If opened in Obsidian, `.obsidian/graph.json`
configures color groups by folder.

## Seed Priority

### Tier 1 — Core (build first)
{{TIER_1_TOPICS}}

### Tier 2 — Context
{{TIER_2_TOPICS}}

### Tier 3 — Connections
{{TIER_3_TOPICS}}

### Tier 4 — Horizon
{{TIER_4_TOPICS}}
```
