# Project naming convention

The `project:` field of a dot is a stable identifier. The viewer keys node colour and
roadmap lane off the **exact string**, so keep spelling and case consistent across a
work stream — renaming splits its history into two colours/lanes.

## The pattern: `Scope:Subject`

Group a dot under a **Scope** (a top-level bucket that means something to you) and a
**Subject** (the specific thread inside it):

```
<Scope>:<Subject>
```

- **Canonical case.** Write it the way you'd write it on a slide; keep it identical
  everywhere. `Reco` ≠ `reco` ≠ `RECO` to the viewer.
- **One string = one colour = one lane.** Pick the split that gives you useful lanes.
- **Plain string.** A colon separates Scope from Subject; the frontmatter parser splits
  only on the first `: `, so `/`, digits, and extra words inside the Subject are fine.
- **Bare `<Subject>`** is allowed when the Scope is obvious (e.g. a single-project vault).
- Need a third level? Just extend the Subject (`Scope:Subject-Detail`) — the viewer
  treats the whole string as the key; only the leading `:` is structurally meaningful
  (a future "group lanes by Scope" view would split on it).

## Choose Scope to fit your work — examples across domains

| domain          | example `project:` values                          |
|-----------------|----------------------------------------------------|
| research (exp.) | `Experiment:Calib`, `Experiment:Reco`, `Lit:Review` |
| research (area) | `Methods:Fitters`, `Stats:Unfolding`               |
| software        | `WebApp:Auth`, `WebApp:Billing`, `Infra:CI`        |
| writing         | `Thesis:Ch3`, `Paper:Revisions`                    |
| teaching / life | `Teaching:Grading`, `Mneme:Meta`             |

Scope can be an experiment, a product, a course, a research area, a client — whatever
gives you legible lanes. Mix experiment-scopes and topic-scopes freely.

## Keep your own vocabulary

The specific Scopes and Subjects you use are **yours to maintain** — record your
canonical list wherever you keep project notes (e.g. your own `CLAUDE.md`), so you and
your agents spell them the same way every time. This repo only defines the *pattern*,
not anyone's particular vocabulary.
