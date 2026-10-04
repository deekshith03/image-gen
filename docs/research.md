# Research: Context-Enriched Ad Image Generation & Evaluation

Prior-art survey (papers, GitHub, industry) done before designing the pipeline. Compiled 2026-10-04.

**Problem:** reference product image + {geography, season, freeform text} → display ad (Gemini 3.1 Flash / Flash-Lite Image, long edge ≤1024px), plus an evaluator for context adherence, product fidelity, and text fidelity, validated against a golden dataset.

**Decision taken:** Option C (Hybrid). Gemini renders everything, the evaluator acts as a gate, and failures fall back to deterministic fixes (product composite / text overlay). See [Strategy options](#strategy-options).

---

## TL;DR

| Dimension | Best current approach | Avoid |
|---|---|---|
| Context (geo/season) | Turn the context into atomic yes/no questions, each answered by an MLLM/VQA (DSG, TIFA, Gecko) | CLIPScore (a single global similarity score) |
| Product fidelity | MLLM judge comparing reference and output side by side, plus DreamSim/DINO on a **cropped/segmented** product | DINO/CLIP-I on the whole image (background bleed; blind to logo/colour) |
| Text | OCR, then exact match + NED (AnyText / MARIO-Eval / LeX-Bench) | Asking an MLLM "is the text right?" |

**Judge rules:**
- One judge call per dimension, binary pass/fail, rationale written before the verdict.
- Validate against human labels with TPR/TNR and kappa.
- Beware leniency and self-preference bias (Gemini judging Gemini).

**Gaps nobody fills:**
- No open evaluator combines product + geo/season + text.
- No geo/season adherence benchmark.
- No labelled pass/fail dataset for product ads.

These gaps are where this project adds something new.

---

## How production does it

```
ref image → segment product → model generates ONLY background/scene
          → paste ORIGINAL product pixels back (fidelity by construction)
          → overlay text with a real font (spelling by construction)
          → deterministic gates (size, safety) → MLLM judge → human review
```

- **Amazon Ads**:
  - Removes the product background and generates only the scene.
  - Screens with Comprehend and Rekognition, and runs blind A/B human review in Ground Truth.
  - Sources: [AWS blog](https://aws.amazon.com/blogs/machine-learning/learn-how-amazon-ads-created-a-generative-ai-powered-image-generation-capability-using-amazon-sagemaker), [Amazon Ads blog](https://advertising.amazon.com/blog/ai-image-generation)
- **Pinterest Canvas**: pastes the original product cutout back after generation. [arXiv 2603.06453](https://arxiv.org/abs/2603.06453)
- **Meta Advantage+**: background generation; text overlays use a fixed font set. [Meta](https://www.facebook.com/business/news/Introducing-Enhanced-Gen-AI-Features-and-Other-Tools-to-Help-Build-Your-Business)
- **Shopify Magic**: subject cutout plus background replacement. [Docs](https://help.shopify.com/en/manual/shopify-admin/productivity-tools/shopify-magic/media-generation)
- **Google Product Studio**: scene around the product, with seasonal and holiday templates. [Docs](https://support.google.com/merchants/answer/13708167)
- **Google Ads generated images**: blocks logos not supplied as input; advertiser review is required. [Docs](https://support.google.com/google-ads/answer/14150986)
- **Adobe GenStudio**: brand score out of 100, with a reason per attribute, before human approval. [Page](https://business.adobe.com/products/genstudio/performance-marketing/brand-compliance.html)
- **Typeface / AdCreative.ai**: leave negative space for the text overlay, or use templates. [Typeface](https://www.typeface.ai/blog/ai-image-prompts-for-marketing-campaigns), [AdCreative](https://www.adcreative.ai/custom-templates)

---

## Gemini facts (verified 2026-10-04)

- **Models:**
  - `gemini-3.1-flash-image` (Nano Banana 2): [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)
  - `gemini-3.1-flash-lite-image` (1K only, <2s latency): [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-image)
- **Sizes:** `image_size` is one of `512px` / `1K` / `2K` / `4K`. At 1K, **only 1:1 (1024×1024) meets the ≤1024 rule**; other ratios need a deterministic downscale (or 512px on Flash). [Image gen docs](https://ai.google.dev/gemini-api/docs/image-generation)
- **Reference images:** Flash-Lite takes up to 14 object images; Flash takes 10 objects + 4 characters.
- **No structured output on the image models**, so the judge must be a separate Gemini text model using a JSON schema. [Structured output](https://ai.google.dev/gemini-api/docs/structured-output)
  - ⚠ Verify the text-model ID before hard-coding it.
- **⚠ Free tier:** the pricing page says image generation is "Not available" on the free tier. Verify with the actual key. [Pricing](https://ai.google.dev/gemini-api/docs/pricing): Flash 1K $0.067, 0.5K $0.045; Flash-Lite 1K $0.0336.
- **Rate limits** include images per minute. [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- **Prompting:**
  - Follow subject → action → location → composition → style.
  - Put exact text in quotes and name the font style.
  - Describe what you want ("empty street"), not what you don't ("no cars").
  - Source: [Nano Banana prompting guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana)
- **Provenance:** SynthID + C2PA on every output. [Launch post](https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/)
- **API shape:**
  - The docs show the Interactions API (`response_format`, `previous_interaction_id`).
  - Older SDKs use `image_config`. Check which one the installed SDK expects.

---

## Papers (ranked by relevance)

Area key: **A** context adherence · **S** subject/product fidelity · **T** text rendering · **Ad** ad creative · **J** judge reliability · **R** generate→evaluate→refine loops.

| # | Area | Paper | Takeaway | Code/data |
|---|---|---|---|---|
| 1 | S | [DreamBench++](https://arxiv.org/abs/2406.16855) (2024) | GPT-4o judge with structured prompts beats DINO/CLIP-I on human agreement for subject fidelity. **Template for our product judge.** | Public |
| 2 | S, Ad | [RefAdGen](https://arxiv.org/abs/2508.11695) (2025) | Same task as ours: reference product + scene description → ad. AdProd-100K dataset. | Public |
| 3 | A | [VQAScore](https://arxiv.org/abs/2404.01291) (2024) | P("Yes") for "Does this figure show '{text}'?". SOTA on alignment benchmarks. | Public |
| 4 | A | [DSG](https://arxiv.org/abs/2310.18235) (ICLR'24) | Atomic, dependency-aware question generation + VQA. **Template for geo/season checks.** | Public |
| 5 | A | [TIFA](https://arxiv.org/abs/2303.11897) (ICCV'23) | Original QG + VQA metric; interpretable. | Public |
| 6 | A, J | [Gecko](https://arxiv.org/abs/2404.16820) (2024, DeepMind) | 100K+ human ratings. **How you phrase the rating question changes the conclusions**, so label design matters. | Partly |
| 7 | A | [VIEScore](https://arxiv.org/abs/2312.14867) (ACL'24) | Explainable MLLM judge. Spearman 0.4 vs human–human 0.45. | Public |
| 8 | J | [MJ-Bench](https://arxiv.org/abs/2407.04842) (2024) | VLM judges are more stable with natural-language Likert scales than numeric scales. Validate per criterion. | Public |
| 9 | J | [MLLM-as-a-Judge](https://arxiv.org/abs/2402.04788) (ICML'24) | MLLM judges match humans on pairwise comparison but diverge on absolute scoring; biases and hallucination. | Public |
| 10 | T | [AnyText](https://arxiv.org/abs/2311.03054) (ICLR'24) | OCR Sentence Accuracy + NED metrics. | Public |
| 11 | T | [TextDiffuser](https://arxiv.org/abs/2305.10855) (NeurIPS'23) | MARIO-Eval: OCR precision/recall/F1. | Public |
| 12 | T | [LeX-Art](https://arxiv.org/abs/2503.21749) (2025) | PNED for multiple or out-of-order text spans; also font, colour and position accuracy. | Public |
| 13 | T | [STRICT](https://arxiv.org/abs/2505.18985) (2025) | Legibility and how often text instructions are not followed. | Public |
| 14 | T | [Glyph-ByT5](https://arxiv.org/abs/2403.09622) (ECCV'24) | Text spelling in design images (posters/ads). | Unclear |
| 15 | Ad | [CTR-Driven Ad Image Gen](https://arxiv.org/abs/2502.06823) (2025) | CTR reward model + product-centric preference optimisation. | Public |
| 16 | Ad, J | [RFNet](https://arxiv.org/abs/2408.00418) (2024) | **Industrial precedent:** learned "is this ad usable?" inspector trained on 1M human labels, with regenerate-until-pass. | Unclear |
| 17 | Ad, R | [MIMO](https://arxiv.org/abs/2507.03326) (2025) | Reflective multi-agent loop fixing typography, layout and branding in banners. | Unknown |
| 18 | R | [Idea2Img](https://arxiv.org/abs/2310.08541) (ECCV'24) | Generate → critique → revise prompt, with memory. | Public |
| 19 | R | [Inference-time scaling for diffusion](https://arxiv.org/abs/2501.09732) (2025) | Verifier-guided best-of-N. **Verifier hacking is a real risk.** | — |
| 20 | A, R | [GenAI-Bench](https://arxiv.org/abs/2406.13743) (2024) | Best-of-N reranking with VQAScore is 2–3× more effective than PickScore/HPS. | Public |
| 21 | A | [GenEval](https://arxiv.org/abs/2310.11513) (NeurIPS'23) | Detector-based object, count and colour checks. Not suited to season or geography. | Public |
| 22 | A, S | [ImagenHub](https://arxiv.org/abs/2310.01596) (ICLR'24) | Human labelling protocol (0 / 0.5 / 1). **Template for golden-set guidelines.** | Public |
| 23 | A | [CUBE](https://arxiv.org/abs/2407.06863) (2024), [DIG In](https://arxiv.org/abs/2308.06198) (2023) | Geo/cultural evaluation: models are weaker and more stereotyped for under-represented regions. | Partly |
| 24 | S | [DreamBooth](https://arxiv.org/abs/2208.12242), [DreamSim](https://arxiv.org/abs/2306.09344) | DINO/CLIP-I definitions; DreamSim is a human-aligned perceptual similarity. | Public |
| 25 | J | [Judging the Judges](https://arxiv.org/abs/2406.12624), [EvalGen](https://arxiv.org/abs/2404.12272) | Judges are lenient, so use chance-corrected agreement. **Criteria drift:** the rubric changes as you label. | — |

Also seen:
- HEIM (2311.04287), T2I-CompBench++ (2307.06350), ImageReward (2304.05977), GenAI-Arena (2406.04485)
- TextDiffuser-2 (2311.16465), GlyphControl (2305.18259), OneIG-Bench (2506.07977), TextAtlas5M (2502.07870)
- Reflect-DiT (2503.12271), AdBooster (2309.11507), product poster planning (2312.08822), accessory ad generation (2404.04828), group-wise CTR ads (2602.02033), OCRGenBench (2507.15085)

### Known weaknesses of DINO / CLIP-I
- **Background bleed:** a similar background or pose inflates the score. Crop or segment the product first.
- **Blind to commercially critical details:** logo, label text, colour shade.
- **Rewards copy-paste** and penalises valid re-staging.

---

## GitHub (verified 2026-10-04)

| Repo | Stars | Reuse for us |
|---|---|---|
| [genmedia-creative-studio / Imagen_Product_Recontext](https://github.com/GoogleCloudPlatform/genmedia-creative-studio/tree/main/experiments/Imagen_Product_Recontext) | 1.2k | **Closest match.** Product scenes at scale, plus a Gemini-judge eval notebook (Product Fidelity, Scene Realism, Brand Integrity). |
| [genmedia-creative-studio / brand_consistency](https://github.com/GoogleCloudPlatform/genmedia-creative-studio/tree/main/experiments/brand_consistency) | — | **Generate → judge → retry loop.** JSON-schema critique fed back into the prompt. |
| [generative-ai / gemini/evaluation](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/evaluation) | 17.8k | Gecko image evals (keyword → QA rubric → VLM). Also `nano-banana/nano_banana_recipes.ipynb`, `use-cases/marketing/creative_content_generation.ipynb`. |
| [linzhiqiu/t2v_metrics](https://github.com/linzhiqiu/t2v_metrics) | 600 | pip-installable VQAScore; also CLIPScore, PickScore, ImageReward, HPSv2. |
| [tyxsspa/AnyText `eval/`](https://github.com/tyxsspa/AnyText/tree/main/eval) | 4.9k | OCR Sentence Accuracy + NED scripts. **Liftable for the text check.** |
| [microsoft/unilm `textdiffuser/`](https://github.com/microsoft/unilm/tree/master/textdiffuser) | 22k | OCR precision/recall/F for target words. |
| [OneIG-Bench](https://github.com/OneIG-Bench/OneIG-Benchmark) | 120 | Text-rendering metric definitions (edit distance, word accuracy). |
| [dreambench_plus](https://github.com/yuangpeng/dreambench_plus) | 140 | Subject-fidelity judge prompts with human agreement data. |
| [VIEScore](https://github.com/TIGER-AI-Lab/VIEScore) | 70 | Explainable VLM-judge prompt templates. |
| [ImagenHub](https://github.com/TIGER-AI-Lab/ImagenHub) | 180 | Eval harness structure for reference-image tasks. |
| [dreamsim](https://github.com/ssundaram21/dreamsim) | 630 | Perceptual similarity for the product crop. |
| [dinov2](https://github.com/facebookresearch/dinov2) | 13k | DINO similarity backbone. |
| [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) | 10.6k | Open-vocabulary detection: locate the product or logo before comparing. |
| [rembg](https://github.com/danielgatis/rembg) / [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | 25k / 4.2k | Background removal before the similarity check, and for compositing. |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) / [EasyOCR](https://github.com/JaidedAI/EasyOCR) / [docTR](https://github.com/mindee/doctr) | 90k / 30k / 6.4k | OCR engines. Paddle is best on stylised text; docTR has the cleanest API. |
| [TIFA](https://github.com/Yushi-Hu/tifa) / [DSG](https://github.com/j-min/DSG) | 190 / 110 | Prompt → QA → VQA checklist design. |
| [GenEval](https://github.com/djghosh13/geneval) / [T2I-CompBench](https://github.com/Karine-Huang/T2I-CompBench) | 480 / 350 | Detector-based sub-checks, e.g. "the product appears exactly once". |
| [ImageReward](https://github.com/zai-org/ImageReward) / [HPSv2](https://github.com/tgxs002/HPSv2) / [PickScore](https://github.com/yuvalkirstain/PickScore) | — | Secondary aesthetic signal, not pass/fail. |
| [deepeval](https://github.com/confident-ai/deepeval) / [promptfoo](https://github.com/promptfoo/promptfoo) | 18.6k / 25.7k | Test harnesses with image judging, pytest/CI integration. |
| [idea2img](https://github.com/zyang-ur/idea2img) / [ReflectionFlow](https://github.com/Diffusion-CoT/ReflectionFlow) | 20 / 220 | Research-grade refine loops. |

Low-maturity ad pipelines (none has a real evaluator):
- google-marketing-solutions/backgroundr
- google-marketing-solutions/banana_milkshake
- google-marketing-solutions/adios
- byextremeai/static-ads
- gquthier/autonomous-ad-creative

---

## Eval practice & localisation

- **[Hamel Husain: LLM-as-a-Judge](https://hamel.dev/blog/posts/llm-judge/index.html):** one domain expert gives pass/fail verdicts with critiques; the critiques become few-shot examples; then measure the judge's agreement with the expert.
- **[Eugene Yan: LLM-evaluators](https://eugeneyan.com/writing/llm-evaluators/):** survey of position, verbosity and self-preference bias. Prefer binary or pairwise over Likert.
- **[Etsy × Patronus](https://www.patronus.ai/case-studies/etsy-leveraging-patronus-ais-multimodal-llm-as-a-judge-to-optimize-image-captionin), [Zalando](https://engineering.zalando.com/posts/2024/11/llm-as-a-judge-relevance-assessment-paper-announcement.html):** production multimodal judges.
- **[Rest of World: AI stereotypes](https://restofworld.org/2023/ai-image-stereotypes/):** country prompts produce caricatures (99/100 "Mexican person" images had a sombrero).
- **[Christmas localisation](https://poeditor.com/blog/christmas-localization/):** Dec–Feb is summer in AU/NZ/ZA/AR. **Season is a function of hemisphere.**

---

## Implications for our design

1. **Text check = deterministic.**
   - OCR, then exact match + NED; a mismatch is a hard fail.
   - Use an MLLM only as a tie-breaker for stylised fonts.
   - Also flag extra or garbled text.
2. **Product check = MLLM judge + embedding backstop.**
   - Side-by-side checklist: shape, colour, logo, label, proportions.
   - DreamSim/DINO on the segmented crop, never on the whole image.
3. **Context check = atomic yes/no questions** derived from geo + season (DSG-style).
   - Resolve season against hemisphere.
   - Add an explicit "stereotype/caricature" fail criterion.
4. **Judge format:**
   - Separate Gemini text model with a JSON schema.
   - One call per dimension, rationale before verdict, binary pass/fail.
5. **Judge validation:**
   - Labelled golden set with known-bad cases per failure mode.
   - Report TPR/TNR + kappa on a held-out split.
   - Expect the rubric to drift while labelling.
6. **Bias guards:**
   - Self-preference: Gemini judging Gemini.
   - Leniency.
   - Position bias: swap the order.
   - Verifier hacking: keep a held-out check outside the retry loop.
7. **Hard gates before the judge:** long edge ≤1024, aspect ratio, file validity.

---

## Strategy options

```
A  Pure Gemini        model renders everything → evaluator catches failures
B  Production-style   composite product + overlay text → near-perfect, little to evaluate
C  Hybrid  ✅ chosen   Gemini renders all; evaluator gates; on text/product
                      failure → fallback to composite/overlay (the "guarantee")
```

## Decisions (2026-10-04)

| Topic | Decision |
|---|---|
| Strategy | **C (hybrid):** Gemini renders everything → evaluator gates → fallback (overlay text / composite product) |
| Principle | **Strict on content, free on presentation.** Words, product identity and the geo/season reading are strict. Font, layout, staging and composition are creative freedom. |
| Text check | Exact word match against the **input** text after normalisation (case, whitespace, line breaks). If OCR fails, an MLLM reads the text before a final fail, so stylised fonts aren't penalised. |
| Ground truth | Each check compares output vs **input** (text string, reference image, geo/season). The golden set holds **human pass/fail labels** used to validate the evaluator, not "correct images". |
| Overall verdict | **All checks must pass.** No weighted score. |
| Retries | Max **2** regenerations (with judge critique), then fallback. |
| Product staging | Environmental integration (snow, reflections, lighting, angle) is **acceptable**. Only identity changes (shape, colour, logo, label) fail. |
| Creativity | Not gated. An optional soft "ad appeal" score may rank passing ads but never fails one. |
| Golden set | ~20 natural ads (1 per brief) + ~25 planted failures (single-attribute edits of a natural ad, spread across briefs) ≈ 45 items, human-labelled, split into dev/test |
| Product photos | Real brands, mainly from Amazon Reviews 2023 (McAuley Lab) hi-res packshots, plus 2 from ABO. **Copyrighted:** git-ignore the images and commit IDs + a download script only. Size of the set isn't a concern; coverage of hard cases matters more. |
| Final product set | 23 products: the 14 below + Pandora Family Roots, Pandora Sister heart, Nike LunarEpic Flyknit (white), London Fog houndstooth luggage, Case-Mate Soap Bubble case, Bodum chrome kettle, Ray-Ban RB3447 green mirror, Duncan Hines Mug Cakes, Quaker Oats. |
| Dataset size | 23 products × 2 briefs = 46 natural + ~30 planted ≈ 75 labelled items |
| Dev/test split | One pool, **split by product** (all of a product's ads and planted variants go to the same side), stratified by category and failure type: ~11 products dev / ~12 test. No separate sourcing for test. |
| Balance | Target 40–60% failures **per check**. Rebalance after generation by planting more failures or regenerating with Flash. |
| Metrics | Per check: **catch rate** (TPR on true fails) and **pass rate** (TNR on true passes). Never a single overall accuracy number. |
| Severity | Planted failures graded blatant / moderate / **subtle** (mostly moderate and subtle). Catch rate reported per severity. |
| Unsure label | Borderline items labelled "unsure" are excluded from scoring and reported separately. |
| Briefs | AI drafts them from a coverage grid (hemisphere, culture/stereotype risk, obvious vs subtle season cues, text length/numbers/non-Latin, product × context fit/conflict); the user reviews them. |
| Context check split | **Factual** checks (landmark location, hemisphere/season, script/language, festival timing) work for any region. **Cultural-judgement** checks (authentic vs caricature) need lived knowledge. |
| Label sources | **Gold** = the user's labels (all text, product and factual-context checks, plus cultural judgement for India only; the user is from India). **Silver** = an expert panel (Claude Opus 5.5 + GPT-5.5 via LiteLLM, different families from the Gemini judge) labels non-India cultural judgement. Panel disagreement → unsure (not scored). The panel is calibrated against the user's India labels. Gold and silver are reported separately. |
| Briefs | Kept as drafted (no India swaps). |
| Geography meaning | **Target market, not backdrop.** Prompt v1 ("show this place") → landmark clichés. Prompt v2 = "feel native to consumers there in that season". A landmark is OK only if it supports the product or message, otherwise it's a cliché fail. |
| **Generator (LOCKED)** | **D2** = art-direction planner (`gemini-3.8-flash`, reads the brand's typography off the packaging; real places welcome when they fit, landmarks never forced) + `gemini-3.1-flash-image`. Text colour is chosen by the image model from the final scene's tones and light. "If people appear, their faces are not visible." ~$0.074/ad. |
| Judge model | **Claude Sonnet 5** (`anthropic/claude-sonnet-5`, user choice). Different family from the Gemini generator (no self-preference) and a different model from the Opus panel. Circularity guard: headline metrics use only labels the panel never influenced (planted, earlier-version, blind, India, flipped); panel-confirmed/silver labels are reported separately. Text check: blind transcription (the judge is not told the expected text) plus a code comparison. |
| Added parts (charm on a bracelet/chain) | **Product fail** (user decision, kept after the pipeline run). The judge excuses this as staging, which is a known judge weakness listed in docs/results.md; labels unchanged. |
| Punctuation | **Strict:** any added, missing or changed punctuation fails the text check, including a trailing full stop (user decision; replaces the earlier lenient proposal). |
| Labelling notes (user) | **Local relevance bar = fits and feels right, nothing contradicts the market**, not "loudly signals the city" (b03 D2 rainy balcony = pass). **Awkward crops / cut-off heads** (b40 D2) are a separate *visual integrity* flag, not a brief check; it's a side effect of the no-faces rule. |
| Strategy history | v1 "show this place" → landmark clichés · v2 "target market" → placeless, faint text · D planner → great typography, colour picked blind · v3 local-cue checklist → token props (chai + chappals) · v4 token test → placeless again · v4.1 + people → unrealistic faces, banner text · v5 lean + hands → hands everywhere · v6 single call → busier, sometimes no image · **D2** → chosen. Lesson: **short, concrete prompts beat rule lists**; each added rule was over-applied. |
| Natural ads | Both v1 and v2 (92) kept for labelling. v1 = natural cliché failures; v1→v2 = before/after evidence for the prompt strategy. Total generation cost so far ≈ $3.1. |
| Product set (initial 14) | Kiehl's Ultra Facial Cream, Neutrogena Hydro Boost, CeraVe lotion, Versace Eau Fraîche, Jo Malone Wood Sage, Timex Expedition chrono, Casio G-Shock MT-G, adidas Grand Court, New Balance 515, Carhartt plaid shirt, Legendary Whitetails flannel, Nutella biscuits (OFF), OWN PWR pre-workout (ABO), 365 BBQ chips (ABO). Pending: fine jewellery, knit sneaker, "illusion" products. |
| UI | Streamlit: Page 1 labelling (Stage 1), Page 2 demo of the generate → judge → retry flow (Stage 2). Core logic lives in a plain Python package. |
| Evals | promptfoo for **both** dev (iterative judge tuning, prompt A/B) and test (one-shot final benchmark): same config, different test files |
| Model access | Generation via LiteLLM proxy → `vertex_ai/gemini-3.1-flash(-lite)-image` (1:1 = 1024×1024). The direct AI Studio key has an image quota of 0. |

**Why C:**
- The evaluator has real failures to catch, and those can be measured.
- The deterministic fallback is what lets us *guarantee* output quality.
- It mirrors production practice while still exercising Gemini's text and product rendering.

---

## Localisation research: how marketers target a geography (2026-10-04)

**Why:**
- Prompt v1 ("show this place") produced tourist-gaze landmarks.
- Prompt v2 + planner produced polished, placeless studio scenes.
- Professionals do neither.

**Industry model: "global idea, local execution."**
- **Keep global:** distinctive brand assets (logo, colours, packaging, product) and the core human insight.
- **Localise:** setting, people, props, occasion, light/climate, language.
- The strongest local cues are **ordinary "insider" details a local recognises instantly and a tourist would miss**, not icons.
- System1/Orlando Wood (*Lemon*): ads with a **sense of place**, people interacting with each other ("betweenness") and depth outperform flat, abstract, placeless ads. That is exactly v2+planner's failure.
- Kantar: only 38% of ads that test strong in one country also test strong in another, which is evidence against one-size execution.

### Localisation levers (non-landmark)
| Lever | Signals the market via | Pitfall |
|---|---|---|
| Vernacular built environment | materials, windows, balconies, shop shutters, signage density, street furniture, traffic side | defaulting to the old town; mixing in neighbouring countries |
| Domestic interiors | room size, kitchen layout, flooring, balconies, shoes-off entry, plugs/switches | aspirational Western-sized homes read as foreign (IKEA edits kitchens per country) |
| Climate & light | sun angle/harshness, humidity haze, vegetation, monsoon, dry-season dust, heating/cooling gear | northern-hemisphere defaults; snow in the tropics |
| People & casting | representative ethnic mix, age, everyday styling, body language | costume clichés; a single token face; treating a multi-ethnic market as one ethnicity |
| Everyday props | food, drinkware, tableware, plants, textiles, vehicles (tuk-tuk, kei car, matatu) | "exotic showcase" food; wrong country's props; third-party logos |
| Occasions & calendar | festival shown through **domestic preparation**, not spectacle | wrong festival; daytime food during Ramadan; trivialising religion |
| Colour symbolism | culturally loaded colours in setting and styling | over-reading colour charts; overriding brand colours |
| Language, script, units | transcreated headline, correct script, currency/units | machine translation; $ in a ₹ market |
| Social framing | group/family vs individual hero | stereotyping every Asian market as collectivist |

Case studies:
- IKEA's 72 country catalogues
- Nike "Nothing Beats a Londoner" (real kids, estates, slang, no Big Ben)
- Apple "Shot on iPhone" Lunar New Year and Diwali (family and craft, not fireworks)
- Share a Coke (local names)
- Spotify Wrapped (local data)

### Seasonality
- **Hemisphere first:** Australia, New Zealand, South Africa, Argentina and Chile have summer in Dec–Feb.
- **Tropical markets have wet and dry seasons, not four seasons.** In equatorial cities (Singapore, Jakarta, Lagos), the season comes through occasions, not weather.
- **Moments calendars:** Ramadan/Eid (lunar), Diwali, Lunar New Year / Seollal / Tết, 11.11, Golden Week, local back-to-school.

### Minimum signal set for one still ad (synthesis, not an industry standard)
At least 4 local cues across at least 3 categories:
1. Setting: vernacular, **required**
2. Climate/light/season, consistent with hemisphere and climate zone: **required**
3. People or a human trace: strongly recommended
4. One prop or occasion cue
5. Language/units, in the copy layer

Constraints:
- At least 1 **insider cue**.
- At most 1 iconic element (0 preferred).
- Brand and product intact.
- **Swap test:** relabel the geography and the image should have to change.

### Anti-patterns
- Tourist gaze / Orientalism, including in gen-AI travel imagery.
- Stereotype and mockery (D&G #DGLovesChina).
- "One Asia" (Chinese symbols for Seollal or Tết).
- Mismatched cues.
- **Over-localisation** (cue pile-up becomes caricature).
- **Placeless "safe" scenes.**

### Evidence (strength-ordered)
- Kantar 38% cross-country (above).
- Meta's 25 brand-lift studies: diverse/inclusive representation wins recall in >90% of simulations.
- Kantar/Unstereotype Alliance: progressive portrayals +28% purchase intent.
- CSA Research: 76% prefer their own language.
- WARC × TikTok: 56% are more likely to buy if an ad is culturally relevant.
- **Not citable:** vendor "+86% CTR" claims, Airbnb +30%.

### Evaluation practice
- In-market review by locals is the norm.
- No public, standardised "cultural relevance score" exists.
- The closest public rubric is the Unstereotype Alliance **3Ps** (Presence, Perspective, Personality) plus the WFA D&R guide.

Key sources:
- [Kantar ads that travel](https://www.bizcommunity.com/Article/196/12/152470.html)
- [Lemon summary](https://www.alexmurrell.co.uk/summaries/orlando-wood-lemon)
- [Nothing Beats a Londoner](https://www.campaignlive.co.uk/article/wieden-kennedy-nike-win-social-influencer-grand-prix-cannes-nothing-beats-londoner/1485727)
- [IKEA catalogue localisation](https://www.yankodesign.com/2018/08/10/ikea-subtly-redesigns-its-products-for-each-countryculture/)
- [Unstereotype 3Ps](https://www.unstereotypealliance.org/en/news-and-events/in-the-news/how-to-avoid-stereotypes-in-ads)
- [CSA Research](https://csa-research.com/l/media/Consumers-Prefer-their-Own-Language)
- [Meta representation](https://www.marketingdive.com/news/54-of-people-dont-feel-culturally-represented-in-online-ads-facebook-fin/596357/)
- [Kantar inclusion](https://www.kantar.com/north-america/inspiration/advertising-media/the-power-of-inclusion-and-diversity-in-advertising)
- [Christmas in Australia](https://en.wikipedia.org/wiki/Christmas_in_Australia)
- [D&G case](https://www.npr.org/sections/goatsandsoda/2018/12/01/671891818/dolce-gabbana-ad-with-chopsticks-provokes-public-outrage-in-china)
