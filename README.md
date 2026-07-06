# Mneme — a knowledge graph of "dots" distilled from AI coding sessions

Every AI coding session produces reasoning that dies with the session: a
motivation, a guess, the method tried, the result, and what's still open.
**Mneme** keeps that structure. It distills sessions into atomic, linked
**dots** — plain markdown notes — and gives you a browser to grow, link, and
roadmap them.

This repo is the **reproducible pipeline**, not anyone's notes:

```
viewer/            zero-build web viewer (Cytoscape) + stdlib server
examples/          synthetic demo dots so the viewer renders on a fresh clone
docs/              design spec + prior art (org-roam, Zettelkasten, Cytoscape)
dots/              YOUR notes — gitignored, never committed (see below)
```

The **distill** step (session → dots) is an AI-agent skill kept in your own
agent config (`~/.claude/skills/distill-session`), not bundled here — so nobody
ships their notes or setup with the tool.

> **Privacy.** Your real dots live in `dots/` and are **gitignored**. This repo
> only ever tracks the tooling and the synthetic `examples/`. Keep your `dots/`
> local (and sync them yourself, e.g. Syncthing / a private repo).

## Quick start

```bash
git clone <this-repo> Mneme && cd Mneme
python3 viewer/serve.py            # -> http://127.0.0.1:8899  (shows examples/)
```

No build step, no pip install — `serve.py` is Python-3 stdlib only. When
`dots/` is empty it renders `examples/`; once you add real dots they take over.

**Remote box without X forwarding:**

```bash
python3 viewer/serve.py            # on the remote
ssh -L 8899:127.0.0.1:8899 <host>  # on your laptop, then open localhost:8899
```

## Make dots

- **With an AI agent:** give it the `distill-session` skill (a small prompt that
  reads a session and emits dots in the schema below), then ask it to *"distill
  this session into the Mneme"*. The skill lives in your agent config, not here.
- **By hand:** create a `dots/<id>.md` following the schema below.
- **In the viewer:** the **+ dot** button.

## The dot format

YAML frontmatter + fixed body headers + typed wikilinks — portable, git-friendly,
Obsidian/Foam/Logseq-compatible. Markdown is the source of truth; `INDEX.md` is
regenerable (`python3 viewer/serve.py --reindex`). Full schema in `docs/`.

```markdown
---
id: 20240112-retry-with-backoff
title: Exponential backoff on the flaky test client
type: method          # insight | method | result | question | milestone | project
project: demo
date: 2024-01-12
status: done          # open | done | parked
milestone: false
keywords: [retry, backoff, jitter]
---
## Motivation
## Guess -> Method -> Result
- Guess: … / Method: … / Result: …
## On-going
- [ ] …
## Links
- next:: [[20240115-ci-green-1000-runs]]
- motivates:: [[20240110-flaky-ci-timeouts]]
```

## Viewer

**graph** view = force-directed link graph (color = project, shape = type,
★ = milestone). **roadmap** view = dots on a date axis with `next::` arrows.
Click a node to edit; **save** writes back to the markdown file and reindexes.

## Prior art

Design borrows org-roam (plain files are the source of truth, any index is a
rebuildable cache), the Zettelkasten atomic-note method, the Obsidian/Foam
markdown+wikilink format, Breadcrumbs-style typed edges for roadmaps, and
Cytoscape.js for a single-file no-build graph. See `docs/`.

## License

MIT for the tooling. `viewer/cytoscape.min.js` is vendored (MIT, © the Cytoscape
Consortium).
