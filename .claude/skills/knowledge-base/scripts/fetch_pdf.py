#!/usr/bin/env python3
"""
fetch_pdf.py — reliably download and VALIDATE a paper PDF for the knowledge-base skill.

The whole point of this script is to make the "give me an arXiv URL and let the
agent grab the PDF" flow *safe*: it turns a silent download failure (HTML captcha
page saved as .pdf, a truncated file, a 404, a rate-limit page) into a hard,
machine-readable FAIL so the ingest cannot fall through to writing a paper body
from memory.

Usage:
  python3 fetch_pdf.py <source> --out <target.pdf>

  <source> may be:
    - an arXiv id:   2009.02994 | arXiv:2009.02994 | 2009.02994v2
    - an arXiv URL:  https://arxiv.org/abs/2009.02994  or  .../pdf/2009.02994
    - a direct URL to a PDF (publisher / institutional / author page)

Output (stdout):
  On success:  one line  'PASS path=<abs> bytes=<n> sha256=<hex> pages=<n|?> url=<used>'  (exit 0)
  On failure:  one or more 'FAIL ...' lines with the reason for each candidate URL  (exit 1)

A PASS guarantees the file exists on disk, begins with the %PDF magic header, is a
plausible size, and is NOT an HTML error/landing/captcha page. It does NOT guarantee
the Read tool can render it (that depends on poppler/pdftoppm). The caller MUST still
canary the `Read` tool on the returned path before writing any body content, and MUST
NOT set transcription_method: read-tool unless a Read actually rendered the PDF.

Also prints a ready-to-paste PDF-manifest row on success.
"""
import sys, os, re, argparse, hashlib, urllib.request, urllib.error, datetime

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
MIN_BYTES = 11000          # arXiv PDFs are tens of KB+; smaller is almost always an error page
TIMEOUT = 90
ATTEMPTS = 3

ARXIV_NEW = re.compile(r"(?<!\d)(\d{4}\.\d{4,5})(v\d+)?", re.I)
ARXIV_OLD = re.compile(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?", re.I)


def candidate_urls(source: str):
    """Return an ordered list of (url, label) candidates to try for `source`."""
    s = source.strip()
    # Direct PDF / http(s) URL that is not an arxiv abs/pdf page → use as-is.
    if s.lower().startswith("http") and "arxiv.org" not in s.lower():
        return [(s, "direct-url")]
    # An arxiv.org URL — normalise /abs/ to /pdf/ and add the export mirror.
    if "arxiv.org" in s.lower():
        m = ARXIV_NEW.search(s) or ARXIV_OLD.search(s)
        if m:
            aid = m.group(0)
            return [
                (f"https://arxiv.org/pdf/{aid}", "arxiv"),
                (f"https://export.arxiv.org/pdf/{aid}", "arxiv-export"),
            ]
        # arxiv url but no id parsed: try the url itself as pdf
        return [(s if "/pdf/" in s else s.replace("/abs/", "/pdf/"), "arxiv-url")]
    # Bare arXiv id (possibly prefixed "arXiv:")
    m = ARXIV_NEW.search(s) or ARXIV_OLD.search(s)
    if m:
        aid = m.group(0)
        return [
            (f"https://arxiv.org/pdf/{aid}", "arxiv"),
            (f"https://export.arxiv.org/pdf/{aid}", "arxiv-export"),
        ]
    return []


def looks_like_pdf(blob: bytes):
    """Return (ok, reason). ok=True only for a plausible PDF payload."""
    if len(blob) < MIN_BYTES:
        return False, f"too-small ({len(blob)} bytes < {MIN_BYTES}; likely an error/landing page)"
    head = blob[:2048].lstrip()
    if head[:4] == b"%PDF":
        return True, "ok"
    low = head[:1024].lower()
    if head[:1] in (b"<",) or b"<html" in low or b"<!doctype" in low:
        return False, "got HTML, not a PDF (rate-limited / captcha / landing page)"
    return False, "no %PDF magic header (not a PDF)"


def fetch(url: str):
    """Return (blob, None) or (None, error_str)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
    last = None
    for _ in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read(), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (404, 403):
                break  # don't retry hard 404/403
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__ + ": " + str(e)
    return None, last or "unknown download error"


def page_count(path: str):
    try:
        import pypdf  # type: ignore
        return str(len(pypdf.PdfReader(path).pages))
    except Exception:
        return "?"


def main():
    ap = argparse.ArgumentParser(description="Download + validate a paper PDF (no silent failures).")
    ap.add_argument("source", help="arXiv id/URL or a direct PDF URL")
    ap.add_argument("--out", required=True, help="target .pdf path (parents created)")
    args = ap.parse_args()

    cands = candidate_urls(args.source)
    if not cands:
        print(f"FAIL reason=unrecognized-source source={args.source!r} "
              "(expected an arXiv id/URL or a direct PDF URL)")
        return 1

    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(os.path.dirname(out), exist_ok=True)

    for url, label in cands:
        blob, err = fetch(url)
        if err:
            print(f"FAIL url={url} reason=download-failed detail={err}")
            continue
        ok, reason = looks_like_pdf(blob)
        if not ok:
            print(f"FAIL url={url} reason=not-a-valid-pdf detail={reason}")
            continue
        with open(out, "wb") as f:
            f.write(blob)
        sha = hashlib.sha256(blob).hexdigest()[:16]
        pages = page_count(out)
        today = datetime.date.today().isoformat()
        print(f"PASS path={out} bytes={len(blob)} sha256={sha} pages={pages} url={url}")
        print(f"MANIFEST_ROW | {os.path.basename(out)} | {url} | fetched {today} ({label}) |")
        print("NEXT: canary the Read tool on this exact path before writing ANY body content. "
              "If Read errors (e.g. 'pdftoppm is not installed'), do NOT fall back to pdftotext — "
              "keep status: to-read and STOP.")
        return 0

    print("FAIL reason=all-candidates-failed "
          "(try a direct PDF URL, or download the PDF manually and pass the file path to the skill)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
