# Evaluator results

**Judge:** Claude Sonnet 5 (`anthropic/claude-sonnet-5`), prompt version `f5089f81` (v3), frozen before the test run.
**Golden set:** 109 items (46 final D2 ads, 24 earlier-strategy failures, 39 planted single-change edits), human-labelled, split by product.

## Test split (53 held-out items, run once)

| Check | Catch rate (true fails flagged) raw → adjudicated | Pass rate (true passes kept) raw → adjudicated |
|---|---|---|
| Text | 90% (9/10) → **100% (9/9)** | 97% → **97%** |
| Product | 60% (6/10) → **73% (8/11)** | 89% → **96%** |
| Context (combined) | 86% (12/14) → **86%** | 100% → **100%** |
| ↳ season fit | 60% (3/5) | 100% |
| ↳ market fit | 80% (4/5) | 100% |
| ↳ no cliché | 83% (5/6) | 98% |

Catch rate by planted severity: blatant 100%, moderate 82%, subtle 83%.

**Adjudication:** after the run, the human re-checked 4 judge/label disagreements against the reference images.
- 3 labels were corrected: b23 product → pass (invisible fine print); v2-b44 text → pass ("PANDORA" is brand packaging); b29 product → fail (garbled heart claim, verified).
- 1 was kept: b35, where the judge hallucinated a "mirrored image".

Reviewing only disagreements can only raise agreement, so both raw and adjudicated numbers are reported. The raw labels are kept in `data/golden/ground_truth_raw_pre_adjudication.jsonl`, and every correction is appended with `correction_of`.

## Dev split (tuned on, therefore optimistic)
| Prompt version | Items fully correct | Text catch/pass | Product catch/pass | Context catch/pass |
|---|---|---|---|---|
| v1 baseline | 68% | 91% / 100% | 80% / 92% | 81% / 93% |
| v2 (6 fixes) | 84% | 100% / 92% | 90% / 96% | 88% / 100% |
| v3 (2 precision fixes) | 95% | 100% / 100% | 83% / 100%* | 94% / 100% |

\*After the Kiehl's "SINCE 1691" label correction.

**The gap between dev and test on product (83% → 73%) is the overfitting cost of three tuning rounds.**

## Known judge weaknesses (test-set evidence)
- **Product, staging loophole:** an added chain on a charm was excused as "worn" (b44).
- **Product, notices then forgives:** saw a flannel recolour or button difference but still passed it (v1-b40).
- **Product, micro-text:** inconsistent on garbled dial or label micro-text (b36 missed; Kiehl's caught on one copy, missed on another).
- **Product, hallucination:** claimed a "mirrored image" that isn't there (b35).
- **Context, landmark geography:** the Taj Mahal in Mumbai was accepted as "Indian" (p26).
- **Context, subtle season:** green foliage accepted as early autumn (p38).
- **Context, token props:** a Club-Mate bottle was accepted as "a casual drink" (v4.1-b45).
- **Cross-check bleed:** a headline typo failed the product check (p06); foreign lanterns failed the text check (p35).
- **Circularity guard:** the "independent" rows exclude every label the expert panel (which includes Claude Opus) could have anchored. Their catch rates match the full rows.
