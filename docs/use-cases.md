# Use Cases — When a Knowledge Base Is Worth It

A curated, auditable knowledge base (KB) is not free. You pay an upfront cost:
every paper is read, summarized, cross-referenced, and recorded with a
`source_trace`. That cost buys provenance and a structure that compounds. It is
worth it for some jobs and overkill for others. This page helps you decide, and
shows one strong downstream use: learning the material the KB indexes.

---

## KB vs. retrieval / RAG — the context-window bound

Both a KB and a retrieval-augmented-generation (RAG) setup exist to get more into
an answer than fits in one prompt. They make opposite tradeoffs.

**RAG defers the reading.** It chunks a corpus, embeds it, and at query time pulls
the chunks that look relevant into the model's context. Nothing is curated ahead of
time; nothing is guaranteed to have been read by a human or sourced honestly. RAG
is the right tool when:

- the corpus is **large and you query it occasionally** — you do not want to
  pre-digest thousands of documents you may never revisit;
- the questions are **lookup-shaped** ("where is X mentioned?") rather than
  synthesis-shaped;
- **freshness matters more than provenance** — you would rather re-index than
  maintain hand-checked pages.

Its weaknesses are exactly the things this repo is built around: retrieved chunks
can be stitched into a fluent but wrong synthesis, the provenance is "these chunks
were nearby in embedding space," and there is no mechanical guarantee that any claim
traces to a source someone actually read.

**A KB front-loads the reading.** You pay once, per paper, to produce a sourced,
cross-referenced page — and then every later query reads *curated* pages, not raw
chunks. A KB is worth the upfront cost when:

- you **revisit the same sources repeatedly** (your project's core literature),
  so the read amortizes;
- you need **auditability** — every claim must trace to a specific PDF and read,
  the way `source_trace` + the lint enforce here;
- knowledge must **compound** — each new paper touches and enriches existing pages,
  building structure a flat chunk store never has;
- the **working set exceeds a single context window**, but a curated *index* of it
  fits. The KB is the durable, human-readable index that does fit; the PDFs behind
  it do not have to.

The honest framing of the context-window bound: RAG is how you cope when the corpus
is too big to read; a KB is how you cope when the corpus is too important *not* to
read. They compose — a mature KB can be the retrieval target for RAG, and now your
retrieval hits sourced, checkable pages instead of raw text.

---

## Team and continuity use

A KB's second payoff is organizational, not technical.

- **Onboarding.** A new student or collaborator reads `index.md` and the concept
  pages instead of reverse-engineering a shared mental model from Slack history.
- **Shared vocabulary.** One page per concept, one canonical summary per paper,
  consistent notation — the team argues about ideas, not about which version of a
  result is right.
- **Continuity across turnover.** The person who read the foundational papers
  graduates; their sourced pages stay. The `source_trace` means a successor can
  *verify* the inherited summaries instead of trusting them.
- **Multi-agent, agent-neutral.** The contract lives in `knowledge/AGENTS.md`, not
  in a single tool's config. Claude Code, a CLI coding agent, or a teammate by hand
  all follow the same READ PROTOCOL and produce pages the same lint checks. The KB
  is git-synced, so contributions merge like code.

---

## The experience caveat

Be clear-eyed about what a KB does and does not do for *you*.

**A KB scaffolds your thinking; it does not replace reading.** It indexes,
cross-references, and records provenance — it makes the literature navigable and
checkable. It does not transfer understanding into your head. The understanding is
earned by reading the PDF, working the derivation, arguing with the result. If you
let the summaries stand in for that, you get a navigable map of a territory you have
never walked — fluent recall with no judgment behind it. The KB is most valuable to
someone who *does* read, because it frees attention for the parts that need a human:
deciding what matters, spotting what is wrong, connecting across fields.

This is the experience paradox in miniature: the tools that summarize the work for
you can quietly prevent you from doing the work that builds expertise. The
`source_trace` is there partly so you can always go back and do the reading the page
is standing in for.

---

## Downstream use case: a Socratic tutor over your KB

Once a KB indexes a body of material, you can use it to actually *learn* that
material — not just look it up. This is an optional, downstream use, **not a bundled
dependency**: the KB does not require it and works fully without it.

Point the `socratic-guide` skill at a KB **concept** page (or a theorem/method
page) and ask it to walk you through the derivation the page references. The tutor:

- **reads KB pages read-only** to ground the scaffold in your own sourced material —
  it never writes into the vault, so it cannot pollute the audit trail;
- **makes you generate each step** (typed or as a handwritten screenshot) and never
  hands you the answer, verifying steps with a CAS rather than trusting model
  arithmetic;
- **keeps its own provenance-disciplined learner model** — one file per concept, an
  append-only log of what you got stuck on, what you mastered, and when — stored
  outside the vault, mirroring the same "every record traces to an event"
  discipline the KB uses for papers.

So the KB and the tutor share a philosophy (read-grounded, provenance-first) but
stay decoupled: the KB is the auditable index of *what is known*; the Socratic tutor
is one consumer that helps *you* come to know it. You can adopt the KB without the
tutor, and the tutor reads the KB without changing it.
