# Knowledge Dots ("palace") — Design

Date: 2026-07-05
Status: approved (delegated), building

## Motivation

Every Claude Code session produces reasoning that dies with the session: a
motivation, a guess, the method tried, the result, and what is still open. The
`my-slides` skill already mines sessions — but only to feed a deck, then discards
the structure. This project keeps that structure as a durable, linked knowledge
base: atomic **dots** distilled from sessions, aggregated into a graph you can
browse, edit, and grow across projects and machines.

Goal: a personal, local-first, git-managed knowledge/memory graph. Each dot is
one idea (a Zettelkasten *atomic note*). Dots link into roadmaps and milestones.
A web viewer is the visual entry point — read on a laptop with a browser, edited
headlessly on a remote box over an SSH tunnel.

## Prior art (informing the design)

- **org-roam**: plain-text org files are the *source of truth*; SQLite is a
  *derived, rebuildable cache*. We copy this: markdown dots are canonical, any
  index/cache is regenerable. (orgroam.com/manual.html)
- **Zettelkasten / Foam / Obsidian**: markdown + YAML frontmatter + `[[wikilinks]]`
  is the portable, git-friendly, tool-agnostic atomic-note standard.
- **Cytoscape.js**: MIT, single `<script>`, no build step, force-directed +
  graph algorithms, comfortable to ~3–5k nodes — the viewer's graph engine.
- **Breadcrumbs / ExcaliBrain**: typed edges (`up/down/next/prev`) turn a flat
  link graph into roadmaps. We adopt typed edges via `type:: [[id]]`.

## Architecture

Four decoupled units, all under `~/Sync/claude-config` (= `~/.claude`,
synced across your machines, e.g. by Syncthing):

```
~/.claude/
  skills/distill-session/     UNIT 1 — the skill (session -> dots)
    SKILL.md
    extract-session.sh        (session jsonl -> conversation text)
    dot-template.md
  palace/                     UNITS 2-4 — the DB (its own git repo)
    dots/*.md                 canonical atomic notes (source of truth)
    INDEX.md                  regenerable table of contents
    viewer/
      index.html              Cytoscape graph + roadmap + edit panel
      cytoscape.min.js        vendored (offline)
      serve.py                stdlib-only server: GET /api/dots, POST /api/dot
    docs/                     this spec
    README.md
```

### Unit 1 — `distill-session` skill

**Interface:** invoked when the user says "distill this session", "save what I
learned", "add to palace", or after finishing a work session.
**Depends on:** `extract-session.sh` (bundled), the palace `dots/` dir.
**Does:** run extractor on target session(s) → analyze the conversation for
motivation / guess→method→result / on-going items / keywords → emit one or more
dots in the schema below → write to `palace/dots/` → propose `next::`/`motivates::`
links to existing dots (grep existing ids) → regenerate `INDEX.md`.
**Does NOT:** read raw jsonl into context (uses the extractor), invent figure
paths (uses real ones from the session), or touch the viewer.

The `my-slides` skill's "Sourcing Content from Session History" section is
reduced to a pointer to this skill (single source of truth for the method).

### Unit 2 — the dot schema

One atomic `.md` per node. The skill and the viewer's edit-form write the
frontmatter; the user is never required to hand-author YAML.

```markdown
---
id: 20240112-retry-with-backoff       # date-prefix + slug, unique, stable
title: Exponential backoff on the flaky test client
type: method                           # insight|method|result|question|milestone|project
project: demo
date: 2024-01-12
status: done                           # open|done|parked  (drives "on-going")
milestone: false
keywords: [retry, backoff, jitter]
---
## Motivation
Why this mattered.
## Guess -> Method -> Result
- Guess: ...
- Method: ...
- Result: ... (numbers, artifact paths)
## On-going
- [ ] open item
## Links
- motivates:: [[20240110-flaky-ci-timeouts]]
- next:: [[20240115-ci-green-1000-runs]]
```

- **Fixed headers** (`## Motivation`, `## Guess -> Method -> Result`,
  `## On-going`, `## Links`) give humans and scripts the same slots.
- **Typed edges**: lines `- <reltype>:: [[<id>]]` in `## Links`. Reltypes:
  `next` (roadmap forward), `motivates` (why), `method` (how), `part-of`
  (belongs to a project/milestone), `related` (loose). Regex-parseable;
  Dataview-inline-field compatible for future Obsidian use.
- **id** is the filename stem (`<id>.md`), so wikilinks resolve to files.

### Unit 3 — the DB (git repo)

`palace/` is its own git repo. Syncthing moves the files across machines; git
gives history, diffs, rollback, and `git tag` for real milestones. Caveat:
Syncthing also mirrors `.git` — fine for one-machine-at-a-time use; commit often.

`INDEX.md` is regenerated from the dots (never hand-maintained): a table of
id / title / project / type / status / date, grouped by project.

### Unit 4 — the viewer

`serve.py` (Python 3 stdlib only — `http.server`; a hand-rolled frontmatter
parser so no PyYAML dependency, which matters on minimal/locked-down installs):

- `GET /` → `index.html`
- `GET /api/dots` → `{nodes:[...], edges:[...]}` parsed live from `dots/*.md`
- `POST /api/dot` → write an edited dot back to `dots/<id>.md`

`index.html` (Cytoscape.js, vendored):

- **Graph view**: force-directed; node color by `project` (or `type`), size by
  degree; milestones drawn as stars; edges labelled by reltype.
- **Roadmap view**: nodes positioned on an x-axis by `date`; `next::` edges as
  arrows; milestones pinned and emphasized.
- **Edit panel**: click a node → form (title, type, project, status, milestone,
  keywords, body sections, links) → `POST /api/dot` writes markdown.
- **Filters**: by project, type, status; search by keyword.

Remote use: `python3 serve.py` on the box, `ssh -L 8000:localhost:8000 host`,
open `http://localhost:8000` in the local browser. No X forwarding needed.

## Non-goals (YAGNI)

- No SQLite in v1 (few-hundred dots parse fast from markdown; add a cache only
  if load time hurts).
- No cloud sync service (Syncthing already does it).
- No auth on `serve.py` (localhost / SSH-tunnel only; never bind public).
- No Obsidian dependency (stay compatible, don't require the app).

## Build order

1. Skill + extractor + template.
2. palace git repo + README + .gitignore.
3. Seed dots by dogfooding the skill on a real recent session.
4. serve.py + index.html; verify it renders the seed dots.
5. Point my-slides at the new skill; update MEMORY.md.
