#!/usr/bin/env python3
"""Lint a knowledge base vault for consistency issues.

Usage:
    python lint_kb.py /path/to/vault

Checks:
    1. Orphan pages (no incoming links)
    2. Dead links (point to non-existent files)
    3. Missing frontmatter (no type or tags)
    4. BibTeX sync (paper pages vs references.bib)
    5. Missing from index.md
    6. Empty directories
"""

import os
import re
import sys
import yaml
from pathlib import Path
from collections import defaultdict


def extract_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        if content.startswith('---'):
            end = content.find('---', 3)
            if end != -1:
                fm_text = content[3:end].strip()
                return yaml.safe_load(fm_text) or {}, content
        return {}, content
    except Exception as e:
        return {'_error': str(e)}, ''


def extract_md_links(content, source_file, vault_root):
    """Extract all markdown links [text](path.md) and resolve them."""
    pattern = r'\[([^\]]*)\]\(([^)]+\.md)\)'
    links = []
    for match in re.finditer(pattern, content):
        text, rel_path = match.group(1), match.group(2)
        # Resolve relative to source file's directory
        source_dir = os.path.dirname(source_file)
        abs_path = os.path.normpath(os.path.join(source_dir, rel_path))
        links.append((text, rel_path, abs_path))
    return links


def find_bibtex_keys(bib_path):
    """Extract all bibtex keys from a .bib file."""
    keys = set()
    if os.path.exists(bib_path):
        with open(bib_path, 'r') as f:
            for line in f:
                m = re.match(r'@\w+\{(\w+)', line)
                if m:
                    keys.add(m.group(1))
    return keys


def lint_vault(vault_root):
    vault = Path(vault_root)
    issues = []
    warnings = []

    # Collect all markdown files (excluding templates, .obsidian)
    skip_dirs = {'templates', '.obsidian', '.git', 'raw'}
    all_files = {}
    for md_file in vault.rglob('*.md'):
        rel = md_file.relative_to(vault)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if md_file.name == 'CLAUDE.md':
            continue
        all_files[str(md_file)] = rel

    # Parse all files
    file_data = {}
    all_links = defaultdict(list)  # target -> [(source, text)]
    outgoing = defaultdict(list)   # source -> [target]

    for abs_path, rel_path in all_files.items():
        fm, content = extract_frontmatter(abs_path)
        links = extract_md_links(content, abs_path, str(vault))
        # Also extract links from frontmatter strings
        fm_str = yaml.dump(fm) if fm else ''
        fm_links = extract_md_links(fm_str, abs_path, str(vault))
        all_extracted = links + fm_links

        file_data[abs_path] = {'fm': fm, 'content': content, 'rel': rel_path}

        for text, rel_link, resolved in all_extracted:
            all_links[resolved].append((abs_path, text))
            outgoing[abs_path].append(resolved)

    # === Check 1: Missing frontmatter ===
    for abs_path, data in file_data.items():
        fm = data['fm']
        if '_error' in fm:
            issues.append(f"PARSE ERROR: {data['rel']} — {fm['_error']}")
            continue
        if 'type' not in fm:
            issues.append(f"MISSING TYPE: {data['rel']} has no 'type' in frontmatter")
        if 'tags' not in fm:
            warnings.append(f"MISSING TAGS: {data['rel']} has no 'tags' in frontmatter")

    # === Check 2: Dead links ===
    for abs_path, data in file_data.items():
        for text, rel_link, resolved in extract_md_links(
            data['content'], abs_path, str(vault)
        ):
            if not os.path.exists(resolved):
                issues.append(
                    f"DEAD LINK: {data['rel']} -> {rel_link} (file not found)"
                )

    # === Check 3: Orphan pages ===
    linked_targets = set()
    for targets in all_links:
        linked_targets.add(targets)

    for abs_path, data in file_data.items():
        rel = data['rel']
        # Navigation files are entry points, not orphans
        if rel.parent == Path('.'):
            continue
        if abs_path not in linked_targets:
            warnings.append(f"ORPHAN: {rel} has no incoming links")

    # === Check 4: BibTeX sync ===
    bib_keys = find_bibtex_keys(vault / 'references.bib')
    for abs_path, data in file_data.items():
        fm = data['fm']
        if fm.get('type') == 'paper' and 'bibtex_key' in fm:
            key = fm['bibtex_key']
            if key and key not in bib_keys:
                issues.append(
                    f"BIBTEX MISSING: {data['rel']} has key '{key}' "
                    f"but it's not in references.bib"
                )

    # === Check 5: Papers without PDF ===
    # Resolve the pdf: field robustly — it may be vault-root-relative
    # (raw/pdfs/...) OR page-relative (../raw/pdfs/...). A path that does
    # not resolve either way is treated as missing.
    def resolve_pdf(abs_path, pdf_field):
        for cand in (vault / pdf_field, Path(abs_path).parent / pdf_field):
            try:
                if cand.resolve().exists():
                    return cand.resolve()
            except OSError:
                pass
        return None

    for abs_path, data in file_data.items():
        fm = data['fm']
        if fm.get('type') == 'paper' and fm.get('pdf'):
            if resolve_pdf(abs_path, fm['pdf']) is None:
                warnings.append(
                    f"MISSING PDF: {data['rel']} references {fm['pdf']} "
                    f"but file not found (tried vault-root- and "
                    f"page-relative resolution)"
                )

    # === Check 6: Manifest sync ===
    manifest_path = vault / 'raw' / 'pdfs' / 'manifest.md'
    manifest_filenames = set()
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest_content = f.read()
        # Extract filenames from manifest table rows (backtick-wrapped).
        # Manifests may list paths relative to raw/pdfs/ (e.g.
        # `foundational/smith-1990.pdf`); compare by basename.
        for m in re.finditer(r'`([^`]+\.pdf)`', manifest_content):
            manifest_filenames.add(os.path.basename(m.group(1)))

    # Check: PDFs on disk but not in manifest
    for pdf_file in (vault / 'raw' / 'pdfs').rglob('*.pdf'):
        if pdf_file.name not in manifest_filenames:
            issues.append(
                f"MANIFEST MISSING: {pdf_file.relative_to(vault)} "
                f"exists on disk but not listed in raw/pdfs/manifest.md"
            )

    # Check: paper pages reference PDFs not in manifest
    for abs_path, data in file_data.items():
        fm = data['fm']
        if fm.get('type') == 'paper' and fm.get('pdf'):
            pdf_basename = os.path.basename(fm['pdf'])
            if pdf_basename and manifest_filenames and pdf_basename not in manifest_filenames:
                warnings.append(
                    f"MANIFEST INCOMPLETE: {data['rel']} references "
                    f"{pdf_basename} which is not in manifest.md"
                )

    # === Check 6.5: source_trace presence and transcription_method enum ===
    # Required for any paper page with status: ingested. Empty source_trace
    # is a hard fail (rule 11 in SKILL.md). transcription_method is a strict
    # enum: read-tool | pdftotext | none. Anything else is a hard fail
    # (rule 14). pdftotext + ingested is a soft warning (rule 13) — those
    # pages should be re-verified once Read works on PDFs.
    valid_tm = {'read-tool', 'pdftotext', 'none'}
    for abs_path, data in file_data.items():
        fm = data['fm']
        if fm.get('type') != 'paper':
            continue
        if fm.get('status') != 'ingested':
            continue
        st = fm.get('source_trace') or {}
        if not isinstance(st, dict):
            issues.append(
                f"SOURCE_TRACE MALFORMED: {data['rel']} source_trace "
                f"is not a mapping"
            )
            continue
        # Required subfields
        for field in ('pages_read', 'transcription_method', 'date_read'):
            if not st.get(field):
                issues.append(
                    f"SOURCE_TRACE MISSING: {data['rel']} status:ingested "
                    f"but source_trace.{field} is empty/missing"
                )
        # transcription_method enum
        tm = st.get('transcription_method')
        if tm and tm not in valid_tm:
            issues.append(
                f"SOURCE_TRACE BAD ENUM: {data['rel']} "
                f"transcription_method='{tm}' is not in "
                f"{{read-tool, pdftotext, none}}"
            )
        # Soft: pdftotext-sourced ingested pages should be re-verified
        if tm == 'pdftotext':
            warnings.append(
                f"PDFTOTEXT SOURCED: {data['rel']} drafted from "
                f"pdftotext/pypdf fallback — schedule a Read-tool "
                f"re-verification pass (text-extraction errors found "
                f"~30/16 papers in the 2026-04-29 batch)"
            )
        # HARD: the 2026-06-08 fabrication signature — a page claims it
        # was read with the Read tool, yet its PDF does not exist on disk
        # (so it could not possibly have been read). Almost always means
        # the body was reconstructed from memory. Re-ingest from the PDF
        # or downgrade to status: to-read.
        if tm == 'read-tool' and fm.get('pdf') and resolve_pdf(abs_path, fm['pdf']) is None:
            issues.append(
                f"READ-TOOL BUT NO PDF: {data['rel']} claims "
                f"transcription_method: read-tool with status: ingested, "
                f"but its pdf ({fm['pdf']}) is not on disk — the page could "
                f"not have been read. Re-ingest from the PDF (see "
                f"scripts/fetch_pdf.py) or set status: to-read. This is the "
                f"2026-06-08 memory-reconstruction signature."
            )

    # === Check 6.6: to-read stub with substantive body ===
    # A status: to-read page has, by definition, NOT been read in any
    # session — so any substantive body content on it is memory-drafted.
    # This is the gray-zone leak observed in the 2026-06-11 Antigravity
    # fitness test: the agent correctly refused a full no-PDF ingest and
    # produced a stub, but still wrote "Key Contributions" bullets and a
    # descriptive summary from memory. Equation/theorem-grade sections
    # are a HARD failure; overview prose is a soft warning.
    hard_sections = ('Selected Equations', 'Theoretical Results',
                     'Method Details')
    soft_sections = ('Summary', 'Key Contributions')
    placeholder_re = re.compile(
        r'to be filled|to-be-filled|tbd\b|stub page|placeholder|'
        r'not (?:yet )?(?:available|read|ingested)', re.IGNORECASE)

    def section_bodies(md_text):
        """Yield (section_title, body_text) for each ## section."""
        parts = re.split(r'^##\s+(.+?)\s*$', md_text, flags=re.MULTILINE)
        # parts: [pre, title1, body1, title2, body2, ...]
        for i in range(1, len(parts) - 1, 2):
            yield parts[i].strip(), parts[i + 1]

    def substantive(body):
        """True if a section body has content beyond placeholders."""
        kept = []
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            if s.startswith('>'):          # callout/quote (stub notes)
                continue
            if placeholder_re.search(s):
                continue
            if re.fullmatch(r'[*_(\[\]).\s-]+', s):  # bare markup
                continue
            kept.append(s)
        return len(' '.join(kept)) > 40    # tolerate a one-line pointer

    for abs_path, data in file_data.items():
        fm = data['fm']
        if fm.get('type') != 'paper' or fm.get('status') != 'to-read':
            continue
        for title, body in section_bodies(data['content']):
            if title in hard_sections and substantive(body):
                issues.append(
                    f"STUB WITH BODY: {data['rel']} is status: to-read but "
                    f"'{title}' has substantive content — a page that was "
                    f"never read can only have been drafted from memory. "
                    f"Empty the section or ingest the PDF properly."
                )
            elif title in soft_sections and substantive(body):
                warnings.append(
                    f"STUB WITH PROSE: {data['rel']} is status: to-read but "
                    f"'{title}' contains descriptive prose — likely "
                    f"memory-drafted. Move anything worth keeping to a "
                    f"sourced page or empty the section."
                )

    # === Check 7: Empty directories ===
    content_dirs = [
        'papers', 'concepts', 'methods', 'authors', 'eras',
        'theorems', 'synthesis', 'code-links'
    ]
    for d in content_dirs:
        dir_path = vault / d
        if dir_path.exists():
            md_files = list(dir_path.glob('*.md'))
            if not md_files:
                warnings.append(f"EMPTY DIR: {d}/ has no markdown files")

    # === Report ===
    print(f"Knowledge Base Lint: {vault}")
    print(f"Files scanned: {len(all_files)}")
    print()

    if issues:
        print(f"ISSUES ({len(issues)}):")
        for issue in sorted(issues):
            print(f"  - {issue}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for warning in sorted(warnings):
            print(f"  - {warning}")
        print()

    if not issues and not warnings:
        print("All checks passed.")

    print(f"Summary: {len(issues)} issues, {len(warnings)} warnings")
    return len(issues)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/vault")
        sys.exit(1)
    exit_code = lint_vault(sys.argv[1])
    sys.exit(min(exit_code, 1))
