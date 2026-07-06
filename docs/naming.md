# Project naming convention

The `project:` field of a dot is a stable identifier in **canonical case**. The viewer
keys node colour and roadmap lane off its exact string, so keep spelling *and* case
consistent across a work stream — renaming splits its history into two colours/lanes.

## Rules

- **Format:** `<Experiment>:<Topic>`, preserving the physics capitalisation you'd write
  on a slide. The value is a plain string (a colon and `/` are fine — the frontmatter
  parser splits only on the first `: `). One string = one colour = one lane.
- **Experiment prefix** (optional; use when the same topic recurs across detectors):
  `TAO`, `OSIRIS`, `JUNO`, `JNE` (Jinping / 锦屏). A bare `<Topic>` is fine when the
  experiment is implicit.
- **Non-experiment buckets** (for work that isn't tied to one detector): use a
  descriptive prefix in the same `Prefix:Topic` shape — `Methods:` for reusable
  numerical/analysis tooling (e.g. `Methods:Fitters`), `Teaching:` for course-ops
  (e.g. `Teaching:PhysicsData`). Keep them lane/colour-stable like any project.
- **Canonical topics** (reuse these exact spellings; extend as needed):
  `Calib`, `Reco`, `IBD`, `Li9/He8`, `BiPo214`, `BiPo212`, `Accidental`, `Muon`,
  `PMT`, `Sim`, `Commission`, `Probe`, `DB`, `DQM`, `Fitters`.

## Examples

| project string    | reads as                          |
|-------------------|-----------------------------------|
| `TAO:Reco`        | TAO · reconstruction              |
| `TAO:IBD`         | TAO · IBD selection               |
| `OSIRIS:BiPo214`  | OSIRIS · BiPo-214                 |
| `OSIRIS:BiPo212`  | OSIRIS · BiPo-212                 |
| `JUNO:Li9/He8`    | JUNO · ⁹Li/⁸He background         |
| `JUNO:Calib`      | JUNO · laser/PMT calibration      |
| `JNE:Calib`       | Jinping · PMT gain calibration    |
| `Methods:Fitters` | reusable charge-spectrum fitters  |
| `Teaching:PhysicsData` | Tsinghua physics-data course |

## Notes

- Sorting is case-sensitive, so lanes/legend order by the raw string (`TAO:IBD` before
  `TAO:Reco`). That's fine — it groups by experiment prefix.
- A future "group lanes by experiment" view would split on the `:` prefix, so always
  prefer `TAO:IBD` over `TAO_IBD` or `taoibd`.
