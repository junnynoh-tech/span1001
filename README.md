# SPAN 1001 site

Live at **https://junnynoh-tech.github.io/span1001/**. Class pages and tools for the current term, plus an archive of past terms.

## What's where

```
index.html            course home (generated: current term + links to past terms)
404.html              shown for any missing page (generated)
site.json             THE list of what's on the site; edit this, then build
current/              the active term; D2L links point here
  index.html          term page (generated)
  oral-final/
    topic-draw.html   the page itself, self-contained (own CSS/JS)
archive/
  fall-2026-tr/       a finished term, moved here by the rollover (same layout as current/)
assets/
  kit/kit.css         the one design kit for generated pages: tokens, fonts, dark mode, print
  kit/kit.js          theme + full-screen buttons
  img/panorama/       Panorama photos, shared by every term (hot-linked by the decks)
images/               LEGACY: old URLs of the Panorama photos, kept only so this term's decks
                      keep working. Delete after Fall 2026 (decks now use assets/img/panorama/).
tools/site.py         build · check · rollover
```

Term folders are named `season-year-schedule`: `fall-2026-tr`, `spring-2027-mwf`.

## Add a page

1. Put the file in `current/<section>/name.html`. Pages are **self-contained** (inline CSS/JS), so they keep working when the term moves to `archive/`.
2. Add it to `site.json` under `current.sections` (`title`, `path`, `kind`, `desc`, and `"audience": "instructor"` for instructor-only tools).
3. `python3 tools/site.py build` (rebuilds the index pages and runs the check).
4. Commit and push. Pages updates in about a minute.

## End of term

```
python3 tools/site.py rollover spring-2027-mwf "Spring 2027" MWF "Monday, Wednesday & Friday"
```
This moves `current/` to `archive/fall-2026-tr/`, starts an empty `current/`, and rebuilds every index. D2L links into `current/` then show the new term after the course copy, and old links can be repointed to `archive/…`.

## Never on this site (it's public)

Student names, IDs, emails, scores or work · exams, answer keys, correction keys · grading tools · rosters · scanned textbook pages. `tools/site.py check` refuses file names like `*grading*`, `*key*`, `*roster*`, `.tex/.csv/.xlsx/.zip`, and text with `@ung.edu` addresses or 9-digit IDs. It's a safety net, not permission: data-free class pages only.

## History

Before the November 2026 cleanup the site held Spring 2026 pages (IRA readings, video rubric, pronunciation reference, Lección 1, vocabulary photos). They're all preserved in the git tag `spring-2026-snapshot`:
`git checkout spring-2026-snapshot -- <file>` brings any of them back.
