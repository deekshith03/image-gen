# Design: Context-Enriched Ad Generation with a Validated Evaluator

Companion docs:
- [research.md](research.md): prior art and the full decisions log
- [data/briefs.yaml](../data/briefs.yaml): the 46 briefs
- [data/products/manifest.yaml](../data/products/manifest.yaml): the 23 products

## Goal

Generate display ads from a **reference product photo + geography + season + required text**, and **show with numbers how good they are**. The quality claim rests on an evaluator whose accuracy is measured against human labels.

**Principle: strict on content, free on presentation.**

| Strict (the brief) | Free (creativity) |
|---|---|
| The exact words of the required text | Font, colour, size, placement, line breaks, style |
| Product identity: shape, colour, logo, label, proportions, count | Angle, lighting, reflections, scale, staging (snow on the bottle is fine) |
| The ad feels native to the **target market** in that season | Which settings, props, mood, composition, people |

---

## Architecture

```
                    ┌──────────────────────── core package: adgen ────────────────────────┐
                    │                                                                       │
  brief ───────────►│  PROMPT BUILDER ──► GENERATOR ──► EVALUATOR ──► PIPELINE             │
  {product photo,   │  brief → prompt     Gemini 3.1     3 checks      retry ×2 →           │
   geo, season,     │  (text in quotes,   Flash(-Lite)   + size gate   fallback             │
   text}            │   free styling)     Image via                                         │
                    │                     LiteLLM →                                         │
                    │                     Vertex, 1024²                                     │
                    └───────────────────────────┬───────────────────────────────────────────┘
                                                │ used by
              ┌─────────────────────────────────┼──────────────────────────────────┐
              ▼                                 ▼                                  ▼
     Streamlit                            CLI scripts                         promptfoo
     • Page 1: labelling                  • fetch products                    • dev: tune judge
     • Page 2: live demo                  • batch generate                    • test: final exam
                                          • plant failures
                                          • expert panel
```

All logic lives in the `adgen` Python package. Streamlit, the CLI scripts and promptfoo are thin callers.

### Models (all through the LiteLLM proxy)

| Role | Model | Notes |
|---|---|---|
| Planner | `vertex_ai/gemini-3.8-flash` | Art direction (strategy **D2**, locked): reads the brand's typography off the packaging, plans scene/composition/headline placement. ~$0.006 |
| Generator | `vertex_ai/gemini-3.1-flash-image` | 1:1 → 1024×1024 meets the ≤1024 rule. ~$0.068 per image. Picks the headline colour from the final scene. |
| Judge | `anthropic/claude-sonnet-5` | Different family from the Gemini generator (no self-preference) and a different model from the Opus expert panel |
| Expert panel | Claude Opus 5.5 + GPT-5.5 | Used only to make silver labels; never in the live pipeline. Different model families from Gemini, which reduces self-preference bias. |

The direct AI Studio key has an image quota of 0 on the free tier, so generation must go through the proxy.

---

## Generation strategy (locked: D2)

```
product photo + {geo, season, text}
        │
        ▼
PLANNER (gemini-3.8-flash, sees the product photo)
  brand read from packaging → scene · composition · typeface style · placement
  real places welcome when they fit; landmarks never forced; avoid clichés
        │
        ▼
IMAGE PROMPT (code template: product fidelity · exact headline · text colour from final scene
              tones/light · no faces · no other text)
        │
        ▼
gemini-3.1-flash-image → 1024×1024 ad
```

Nine prompt strategies were tried on the same briefs (see the research.md strategy history). D2 was chosen by human visual review: clean, product-led, brand-matched typography that takes its colour from the scene. The lesson was that **short, concrete prompts beat rule lists**; every added rule (no landmarks, local-cue checklists, token tests, hands) was over-applied by the model. Earlier strategies' outputs are kept as natural failure examples for the golden set.

## Evaluator (the judge)

```
ad + brief
   │
   ├─ 0. SIZE GATE        code       long edge ≤1024, valid image            → hard fail
   │
   ├─ 1. TEXT             Claude     "transcribe the headline verbatim" (blind: not told the expected text)
   │                      + code     normalise (case/space/line breaks) → exact word match
   │                                 ignore text that's part of the product label
   │                                 extra garbled text near the headline → fail
   │
   ├─ 2. PRODUCT          Claude     reference vs ad, side by side; identity checklist:
   │                                 shape · colour · logo · label · proportions · count
   │                                 staging is OK (snow, reflections, lighting, angle)
   │
   └─ 3. CONTEXT          Claude     geography = TARGET MARKET, not backdrop. Yes/no questions:
                                     SEASON FIT      weather/light/clothing match <season> in
                                                     <market> (hemisphere-aware)
                                     MARKET FIT      nothing contradicts the market (climate,
                                                     culture, foreign signage, wrong occasion)
                                     NO CLICHÉ       landmark/skyline only if it supports the
                                                     product or message; no stereotypes
                                     LOCAL RELEVANCE ≥1 subtle market signal (lifestyle,
                                                     setting, occasion, people, local goods)
                                     Factual parts are verifiable for any region; cultural
                                     judgement needs lived knowledge (see Labels).

   → per check: pass/fail + reason (reason written before the verdict)
   → overall: ALL checks must pass
```

**Design choices and why:**
- **Text: the AI model transcribes, code compares.**
  - If you ask an AI model "is the text correct?", it silently autocorrects typos.
  - Asking it to transcribe character by character, then comparing exactly in code, keeps the decision strict.
  - It also avoids a heavy OCR dependency, and stylised fonts don't fail just because an OCR engine can't read them.
  - If planted typos show the model autocorrects even when transcribing, we add OCR.
- **One judge call per check, binary verdicts.** Research shows AI judges are more reliable on pass/fail than on 1–10 scores (MLLM-as-a-Judge, MJ-Bench).
- **Product identity, not pixel similarity.**
  - Whole-image similarity scores (DINO, CLIP) are skewed by the background and miss logo details.
  - A side-by-side checklist judges whether it's the *same product*, and allows creative staging.
- **Geography means target market, not scenery.** The first prompt ("show this place") produced postcard landmarks (Opera House, Hagia Sophia, Louvre). Prompt v2 asks for an ad that feels native to the market's consumers, and allows a landmark only when it supports the product or message (Rio beach for "FRESH LIKE THE OCEAN" ✅, Opera House behind a face cream ❌). Both prompt versions' ads are kept in the golden set: v1 supplies natural cliché failures, and v1 → v2 is a measured result of the prompt change.
- **Context is split into factual and cultural.**
  - Factual questions can be verified for any region.
  - Cultural judgement needs lived knowledge (see Labels).
- **"Same text as on the product" briefs** (b31, b36, b43) test that the text check finds the *headline*, not the product's own label text.

---

## Stage 1: build and prove the judge (once, offline)

```
23 real products ──► 46 briefs ──► 46 D2 ads + 24 earlier-strategy failures ──► + 39 planted ──► 109 items
(Amazon Reviews 2023,  (coverage grid)   (locked generator)  (v1–D, natural)            (one change each)
 ABO, Open Food Facts)
                                                                      │
                     ┌────────────────────────────────────────────────┘
                     ▼
              LABELS  (gold = human, silver = expert panel)
                     │
                     ▼
              SPLIT BY PRODUCT
              DEV  11 products / 22 briefs  → tune judge prompts (promptfoo, many runs)
              TEST 12 products / 24 briefs  → final exam (promptfoo, one run)
```

### Products (23)
Chosen for the fine detail that image generation is known to break. Real brands with clean packshots.

| Failure mode | Products |
|---|---|
| Text on the product's own label | Kiehl's, Neutrogena, CeraVe, OWN PWR |
| Packaging | 365 BBQ chips, Nutella biscuits |
| Glass / transparency | Versace Eau Fraîche, Jo Malone |
| Watches (dial detail + small text) | Timex Expedition chrono, Casio G-Shock |
| Sneakers (logos + textures) | adidas Grand Court, New Balance 515, Nike Flyknit |
| Patterns | Carhartt plaid, Legendary Whitetails flannel |
| Jewellery | Pandora Family Roots (openwork), Pandora Sister heart (engraving) |
| **Illusion / perception-tricky** | London Fog houndstooth (moiré), Case-Mate Soap Bubble (holographic), Bodum chrome kettle and Ray-Ban mirror lenses (reflections), Duncan Hines (box pictures a mug cake), Quaker (printed face) |

The illusion products stress **both** sides:
- **The generator** may produce moiré, "fix" reflections, or pull printed objects out into the scene.
- **The judge** may mistake reflections for product changes, or printed food for scene content.

Images are brand-copyrighted. They are git-ignored, and only the manifest and the fetch script are committed.

### Briefs (46 = 23 products × 2)
Drafted from a coverage grid and reviewed by a human:

| Coverage tag | Count | Example |
|---|---|---|
| Southern hemisphere (inverted season) | 8 | Sydney summer in December |
| Culture / stereotype risk | 9 | Mumbai monsoon, Lagos, Mexico City |
| Subtle season cue | 9 | monsoon, dry season, Dubai winter |
| Numbers / currency | 9 / 5 | `25% OFF`, `NZ$129`, `€79` |
| Punctuation / accents / non-Latin | 6 / 2 / 2 | `D'AUTUNNO`, `OTOÑO`, `ランニングセール` |
| Required text already on the product | 3 | Casio "WATER RESIST 200M" |
| Product ↔ context conflict | 3 | flannel in a Dubai summer |

### Planted failures (~30)
Each one is a copy of a natural ad with **a single change**, made with Gemini image editing. The change is the only difference, so we know exactly which check should flip.

| Severity | Text | Product | Context |
|---|---|---|---|
| Blatant | word missing | different product | beach in a Tokyo-winter brief |
| Moderate | wrong word ("WRAM") | recoloured | generic city instead of the named one |
| **Subtle** (most of them) | `0FF` vs `OFF`, `€19.99` → `€19.90` | logo slightly off, a stud missing | autumn leaves in a winter brief |

- **Balance target:** 40–60% failures **per check**. If one check is short of failures, plant more of that type. If one has too many, regenerate.

### Labels

| Label | Who | Covers |
|---|---|---|
| **Gold** | Human (the user) in Streamlit | Text, product, and factual context for every item. Cultural judgement for **India only** (the labeller's lived knowledge). |
| **Silver** | Expert panel (Claude Opus 5.5 + GPT-5.5) | Cultural judgement for non-India regions. Both models agree → label; they disagree → `unsure`. |
| **Unsure** | Either | Borderline items, excluded from scoring and reported separately |

- **Calibration:** the panel also labels the India items. Its agreement with the human there is our evidence (not proof) that silver labels are reliable elsewhere.
- **Labelling guideline:** cultural cues are judged as *specific and contemporary* (pass) vs *landmark shortcut, exotic clichés, sepia "filter", poverty backdrop, costume default, culture mixing* (fail).
  - Traditional elements pass when the brief calls for them (a sari at Diwali) and fail when they're standing in for the country.
  - Per-region cliché lists live in data, not in prompts.

### Dev / test split
- **Split by product.** All ads and planted copies of a product stay on one side, so the test set never contains near-duplicates of what we tuned on.
- **Stratified:** every category and failure type appears on both sides.
- The human labels the whole pool **before** seeing the split.
- **Dev:** iterate judge prompts freely (promptfoo side-by-side comparisons, viewer).
- **Test:** run once. We never inspect test failures while tuning.

---

## Stage 2: the pipeline in use (every request)

```
brief → Gemini → ad → judge
                       ├─ all ✅ → deliver
                       └─ any ❌ → retry with the judge's critique (max 2)
                                    └─ still ❌ → fallback
                                         text ❌    → overlay headline with a real font
                                         product ❌ → composite the real product photo
                                         context ❌ → deliver best attempt, flagged
```

This is **Strategy C (hybrid)**:
- Gemini renders everything, so the evaluator has real work to do.
- Deterministic fallbacks (used in production by Amazon, Meta and Pinterest) back up the quality guarantee.
- A held-out check outside the retry loop guards against "verifier hacking", i.e. optimising the generator to pass the judge rather than to be good.

---

## Success criteria and reporting

| Metric | Reported per | Purpose |
|---|---|---|
| **Catch rate** (TPR on true fails) | check × severity | Do subtle errors slip through? |
| **Pass rate** (TNR on true passes) | check | Is the judge over-strict? |
| Gold vs silver agreement | context-cultural | Human-verified vs expert-panel claims, kept separate |
| Panel ↔ human agreement (India) | n/a | How much to trust silver labels |
| Unsure items | listed | Visible, not scored |
| Pipeline outcomes | brief | First-try pass %, pass after retry %, fallback % |

We never use a single overall accuracy number. With lopsided data, a judge that always says ✅ (or always ❌) can still score high.

Targets: catch rate ≥ 0.9 on blatant and moderate failures, reported honestly on subtle ones; pass rate ≥ 0.85.
**Achieved on the held-out test split** (docs/results.md): text 100% / 97%, context 86% / 100%, product 73% / 96% (catch / pass, adjudicated). Product misses the catch target.

---

## Known limitations
- **One human labeller.** Cultural ground truth exists only for India. Other regions rely on silver labels, which inherit the documented AI-model bias against under-represented regions.
- **Small dataset (109 items, ~10–16 failures per check per split).** Rates come with wide confidence intervals and should be read as indicative.
- **Planted failures are AI edits.** An edit may change more than intended, which is why every planted item is human-labelled.
- **Product photos are copyrighted.** They're fine for private research, but can't be redistributed.
- **The judge (Claude Sonnet 5) shares a vendor with one panel model (Claude Opus).** Headline metrics use only labels the panel never influenced; panel-confirmed labels are reported separately.
- **Judge weaknesses on the test set:** product fine detail (added parts excused as staging, micro-text, one hallucination). See docs/results.md.

---

## Tooling
- **mise:** python 3.12, node 22, uv
- **uv:** env and packaging
- **Streamlit:** UI
- **promptfoo:** evals
- **LiteLLM proxy:** to Vertex Gemini / Claude / GPT. Secrets live in `.env` (git-ignored).

## Code map
```
prompts/          every LLM prompt as a plain-text template (planner, image, judge ×3, panel, edits, retry critique)
src/adgen/
  core/           config · llm (LiteLLM client) · briefs · checks (check names, Verdict) · prompts (template loader)
  generation/     planner → prompt → generator (Gemini image) · compositor (real-font overlay, product cutout)
  evaluation/     judge (size, text, product, context) · cache (per-prompt-version runs) · scoring (catch/pass rates)
  golden/         items (tiers, plants) · labels · panel (expert pre-labels) · ground_truth (gold/silver derivation)
  pipeline.py     AdPipeline: generate → judge → retry with critique → fallback; writes run traces
scripts/          thin CLIs, one per workflow step (also exposed as mise tasks)
app/              label.py (labelling UI) · demo.py (pipeline demo)
evals/            promptfoo configs (dev/test) + Python provider + generated test cases
tests/            unit tests for the deterministic logic
assets/fonts/     open-licence fonts used by the fallback overlay
```
