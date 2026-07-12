---
name: fpf
description: >-
  Apply the First Principles Framework (FPF) — a domain-agnostic pattern language
  for rigorous conceptual work on systems and knowledge (epistemes). Use when the
  user invokes "FPF" / "First Principles Framework" or a pattern ID (e.g. A.1,
  A.6.B, C.2.P, G.5), or asks to analyze, classify, structure, or check
  conceptual work the FPF way: classifying boundary or claim statements (L/A/D/E),
  restoring precision to overloaded/load-bearing terms, modeling roles–methods–work,
  evidence and assurance (F–G–R), aggregation and emergence, comparison/selection
  without hidden scalarization, language-state and abductive reasoning, or simply
  navigating to the right FPF pattern for a question.
---

# First Principles Framework (FPF)

FPF is a **pattern language for thinking** — a small, domain-agnostic kernel plus
extension patterns for **publishing, checking, and evolving conceptual work**
about *systems* and *epistemes* (knowledge claims). In FPF everything is a
**holon** (a thing treatable both as a whole and as a part). A pattern is a
reusable **action-guidance form**: *Problem frame → Problem → Forces → Solution*,
ending with a **Conformance Checklist** of normative checks.

The full specification (`FPF-Spec.md`) is ~8.7 MB / 86 k lines. **You never load
it whole.** This skill is the progressive-disclosure interface: route a question
to one or a few pattern IDs, then load only those bodies.

## Layout (progressive disclosure)

- **`reference/index.md`** — the router. The spec's Table of Content: every
  pattern's `ID · Title · Status · Keywords & Search Queries · Dependencies`.
  This is your map from a question to a pattern ID. **Read it whenever you need
  to find a pattern** and the quick map below doesn't already pin one.
- **`patterns/<ID>.md`** — 280 self-contained pattern bodies, named by ID
  (`A.1.md`, `C.2.P.md`, `A.19.SOURCE-SET-SPACE-SUBSTRATE.md`, …). Load on demand.
- **`scripts/build_skill.py`** — regenerates `patterns/` + `reference/index.md`
  from `FPF-Spec.md`. Re-run after the spec changes (see Maintenance).
- **`FPF-Spec.md`** (source-repo root) — the source of truth; the split copy
  mirrors it. In a standalone deployment of this skill the spec may be absent —
  the skill is fully usable without it.

## The navigation protocol

1. **Frame the live question.** What are you actually trying to *decide,
   publish, classify, or stabilize*? Pick by the decision, not by chapter order.
2. **Route to a pattern.** Use the quick map below; if it doesn't pin one, open
   `reference/index.md` and match your question's wording against the **Keywords
   & Search Queries** column. The row's first column is the ID.
3. **Load the body.** Read `patterns/<ID>.md`. (Four patterns are large —
   `E.10`, `C.29`, `C.27`, `E.19` — read them by section; see Anatomy.)
4. **Apply it.** Check the **Problem frame** (does your case fit?), use the
   **Solution** (the actual construct/discipline), and run the **Conformance
   Checklist** (the `CC-*` MUST/SHALL items) against the case. Follow the
   **Relations** / `Builds on` / `Coordinates with` to pull in neighbours.
5. **Answer in FPF terms, and cite IDs.** Name the governing pattern(s) and the
   specific `CC-*` items you relied on. Do not invent semantics the patterns
   don't carry. If a word is overloaded or load-bearing, *restore precision*
   (route to `A.6.P` / `C.2.P` / `C.16.Q` / `A.6.A`) before reasoning on it.

## Quick map: situation → entry pattern(s)

| The live question is about… | Start at |
| --- | --- |
| Why FPF / its principles | `E.1`, `E.2` (the 11 Pillars) |
| What a thing *is*: boundaries, parts, holons | `A.1`, `A.1.1` (BoundedContext), `A.14` |
| Roles vs methods vs plan vs run (project alignment) | `A.2`, `A.15`, `A.15.2`, `A.15.3`, `B.5.1` |
| Boundary statements: API / contract / SLO·SLA / policy / interface | `A.6`, `A.6.B` (L/A/D/E), `A.6.C`; `A.6.RSIG` if "what description is this?" |
| An overloaded / load-bearing word needs precision | `A.6.P` (relations), `C.2.P` (source/epistemic), `C.16.Q` (quality), `C.16.P` (characteristic/scale), `A.6.A` (action), `A.6.F` (function), `A.6.H` (wholeness) |
| Evidence, trust, assurance (F–G–R) | `B.3`, `C.2`, `A.10` |
| Aggregation / composition / emergence | `B.1`, `B.2` |
| Partly-said cue / language-state discovery | `C.2.2a`, `C.2.LS`, `A.16`, `A.16.1`, `A.16.2`, `B.4.1` |
| Hypothesis generation / reasoning cycle | `B.5`, `B.5.2`, `B.5.2.1` |
| Comparison / selection / candidate pool (no hidden scalarization) | `A.17`–`A.19`, `A.19.CN`, `A.19.CPM`, `A.19.SelectorMechanism`, `G.0`, `C.18`, `C.19`, `G.5` |
| One local decision among options | `C.11` |
| Measurement / metrics; quality "-ilities" | `C.16`; `C.25` |
| Causal claims; temporal/rate claims; math lens | `C.28`; `C.27`; `C.29` |
| Architecture description | `C.30` (+ `C.30.ASV`, `C.30.LCA`, …) |
| Agentic tool-use / call planning; autonomy budget | `C.24`; `E.16` |
| Reusable generator / SoTA / portfolio kit; shipping; refresh | `A.0`, `G.0`, `G.1`, `G.2`, `G.5`; `G.10`; `G.11` |
| Same-entity rewrite / explanation / representation change / comparison | `A.6.3.CR`, `A.6.3.RT`, `E.17.EFP`, `E.17.ID.CR` |
| Multi-view publication; dashboards | `E.17`, `E.17.0`; `G.12` |
| Ethics / conflict / bias audit | `D.1` (entry), `D.2`–`D.4` (multilevel conflict & mediation), `D.5` (bias audit) |
| Writing or reviewing a pattern | `E.8`, `E.19` (and `E.9` DRR for normative change) |

For anything not listed, search `reference/index.md`.

## Anatomy of a pattern (what to read for *applying*)

Each body follows the template, with `### <ID>:N - Section` subheadings:

- **`:1 Problem frame`** — the situation it governs. Read first to confirm fit.
- **`:2 Problem` · `:3 Forces`** — the tension being resolved.
- **`:4 Solution`** — the construct, types (`U.*`), and discipline. The core.
- **`:5 Archetypal Grounding`** — worked System/Episteme examples.
- **`:7 Conformance Checklist`** — the normative `CC-*` MUST/SHALL items. Apply
  these to the case; cite the ones you used.
- **`:N Relations` / `:End`** — neighbouring patterns to chain to.

The middle sections (Bias-Annotation, Anti-Patterns, Consequences, Rationale,
SoTA-Echoing) are informative support. For a large pattern, grep its `### `
subheadings first, then read just `:1`, `:4`, and the Conformance Checklist with
`offset`/`limit`.

## FPF discipline (carry these into every answer)

- **One claim → one governing pattern** (`E.11`). Name it. Leave only thin echoes
  elsewhere; don't restate a pattern's semantics in your own words as if new.
- **Strict Distinction** (`A.7`): Object ≠ Description ≠ Carrier; Role ≠ Method ≠
  Work (`A.15`). Most modeling errors are a collapsed one of these.
- **Don't smuggle semantics.** Overloaded relation/quality/action/function words
  get *precision restoration* (`A.6.P` family) before they bear weight.
- **No hidden scalarization or thresholds** in comparison/selection — comparison
  is set-valued and stays distinct from selection (`A.19.*`, `G.5`).
- **Evidence is referred, not asserted** (`A.10`, `B.3`); claims carry F–G–R.
- **Pillars bind everything** (`E.2`): cognitive elegance, didactic primacy,
  scalable formality, open-ended kernel, layering, lexical stratification,
  pragmatic utility, cross-scale consistency, state explicitness, open-ended
  evolution, SoTA alignment.
- **Stubs:** if `patterns/<ID>.md` is absent, that TOC row is a stub — reason
  from its index reminder + named dependencies and say so.

## Maintenance (source repo only)

This section applies only where the skill lives next to its source
(`FPF-Spec.md` and the sibling `fpf-updater` skill in the FPF repo). In a
standalone/packaged deployment those files are absent — skip this section.

The split copy is frozen until regenerated. After editing `FPF-Spec.md`:

```
python3 .claude/skills/fpf/scripts/build_skill.py
```

This rebuilds all 280 `patterns/*.md` (removing stale files), refreshes
`reference/index.md` from the spec's Table of Content, and syncs the pattern
count stated in this file. Add `--zip` to also produce a clean distributable
archive.

To rebuild **and validate** in one step (split integrity + the navigation loop),
use the `fpf-updater` skill's driver instead:

```
python3 .claude/skills/fpf-updater/verify.py
```
