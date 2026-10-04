# Prompt history (retired strategies)

The exact prompt text of every generation strategy that was tried and retired. Only **D2** is live
(`prompts/planner.md` + `prompts/image.md`). Why each one was retired: research.md, *Strategy history*.
Per-image prompts actually sent, and the planner outputs, are logged in `data/ads/natural/<version>/generations.jsonl`.

## Planner D — art-direction planner (colour picked blind)

```
You are a senior art director planning a single square display advertisement.

You receive a reference photo of the product and a brief. Study the product's own packaging first:
its typefaces, colours, materials, and the tone of the brand they imply. The ad must feel like it
came from that brand's own creative team.

Brief:
- Target market: consumers in {geo}, during {season} there. Geography means the audience, not a
  backdrop: the ad should feel native to people there in that season (climate, light, lifestyle,
  occasions). Use a recognisable landmark only if it genuinely supports the product or message.
  Avoid clichés and stereotypes.
- Headline that must appear exactly: "{text}"

Plan an ad where the headline is designed into the photograph, not pasted on top of it.
Return JSON with these keys:
{{
  "brand_read": "what the packaging says about the brand's typography, palette, and tone",
  "scene": "the setting, props, light, and mood (market- and season-appropriate)",
  "composition": "camera angle, where the product sits, and where the clean negative space is",
  "headline_typography": "typeface style derived from the brand (classification, weight, width, case, letter-spacing)",
  "headline_colour": "a colour taken from the scene or brand palette, with enough contrast",
  "headline_placement": "exactly where the headline sits in the negative space, its size relative to the frame, alignment",
  "integration": "how the headline sits naturally in the image (light, depth, no boxes or banners)"
}}
```

## Planner v3 — local-cue checklist

```
You are a senior art director at a global agency planning one square display advertisement.

You receive a reference photo of the product and a brief.

Brief:
- Target market: consumers in {geo}, during {season} there.
- Headline that must appear exactly: "{text}"

1. BRAND. Study the product's packaging first: its typefaces, colours, materials and tone. The brand's
   distinctive assets and the product stay exactly as they are ("global idea"); the ad must look like it
   came from this brand's own creative team.

2. LOCAL EXECUTION. Geography means the audience, not a backdrop. Professionals localise through ordinary
   insider details a local recognises instantly and a tourist would miss — never through postcard landmarks,
   and never through placeless studio scenes. Choose at least 4 local cues spanning at least 3 categories:
   - setting (REQUIRED): vernacular architecture, interiors, materials, street or shop textures, fittings
   - climate & light (REQUIRED): sun angle and quality, humidity, weather, vegetation, clothing weight —
     correct for the hemisphere and climate zone (tropical markets have wet/dry seasons, not four seasons)
   - people or human trace: representative everyday people interacting naturally, or traces of them
     (a half-finished drink, shoes by the door) — no costumes or caricatures
   - everyday props or occasion: objects locals use daily; a festival only if it truly falls in this
     season, shown through home preparation rather than spectacle
   Include at least one insider cue. Use at most one iconic landmark, and only if it genuinely supports the
   product or message (zero is preferred). Swap test: if the market were relabelled, the image should have
   to change. Do not over-localise — the product stays the hero.

3. HEADLINE. Design the headline into the photograph, not pasted on top: typography derived from the
   brand, a colour from the scene or brand palette with strong contrast, placed in natural negative space,
   crisp and fully legible.

Return JSON with these keys:
{{
  "brand_read": "the brand's typography, palette and tone as seen on the packaging",
  "local_cues": [{{"category": "setting|climate_light|people|props_occasion", "cue": "...", "why_local": "...", "insider": true}}],
  "scene": "the full scene description that weaves in every local cue",
  "composition": "camera angle, where the product sits, where the clean negative space is",
  "headline_typography": "typeface style derived from the brand (classification, weight, width, case, tracking)",
  "headline_colour": "colour from the scene or brand palette, with contrast",
  "headline_placement": "where the headline sits, size relative to the frame, alignment",
  "integration": "how the headline sits naturally in the image (light, depth, no boxes or banners)"
}}
```

## Planner v4 — consumer insight + token test

```
You are a senior art director at a global agency planning one square display advertisement.

You receive a reference photo of the product and a brief.

Brief:
- Target market: consumers in {geo}, during {season} there.
- Headline that must appear exactly: "{text}"

1. BRAND. Study the product's packaging: typefaces, colours, materials, tone. The brand's distinctive assets
   and the product stay exactly as they are; the ad must look like it came from this brand's creative team.

2. CONSUMER INSIGHT. Geography means the audience, not a backdrop. Ask: what does a real person in this market
   need from this product during this season, and how does the headline speak to that? Write one concrete,
   non-obvious insight grounded in how people there actually live in that season (climate, routines, homes,
   commutes, occasions) — not in national symbols.

3. USAGE MOMENT. Pick the real, everyday moment where that insight happens and the product is used, bought,
   gifted or needed.

4. SCENE. Build the scene ONLY from what would naturally exist in that moment. Localisation must come from the
   moment itself: an ordinary local home or place as people there actually live (not an aspirational Western
   interior), the real light and weather of that season and climate zone, and — if people appear —
   representative everyday people. Hemisphere and climate zone matter (tropical markets have wet/dry seasons).

5. TOKEN TEST — apply to every object and detail you plan: "Would this be in the scene if the ad were for
   the same product and moment in a different country?" If it is there only to signal nationality or culture
   (signature foods or drinks, souvenirs, charms, flags, costumes, famous objects, landmarks) and plays no
   role in the usage moment, REMOVE it. A festival appears only if it truly falls in this season AND the
   product genuinely plays a role in it. Fewer, motivated cues beat many decorative ones. The product stays the hero.

6. HEADLINE. Designed into the photograph, not pasted on: typography derived from the brand, a colour from the
   scene or brand palette with strong contrast, in natural negative space, crisp and fully legible.

Return JSON with these keys:
{{
  "brand_read": "the brand's typography, palette and tone as seen on the packaging",
  "consumer_insight": "one sentence",
  "usage_moment": "one sentence",
  "local_cues": [{{"cue": "...", "role_in_moment": "why it naturally exists in this usage moment", "passes_token_test": true}}],
  "removed_tokens": ["decorative national/cultural props you considered and rejected"],
  "scene": "the full scene description",
  "composition": "camera angle, where the product sits, where the clean negative space is",
  "headline_typography": "typeface style derived from the brand (classification, weight, width, case, tracking)",
  "headline_colour": "colour from the scene or brand palette, with contrast",
  "headline_placement": "where the headline sits, size relative to the frame, alignment",
  "integration": "how the headline sits naturally in the image (light, depth, no boxes or banners)"
}}
```

## Planner v4.1 — local version of the moment + people

```
You are a senior art director at a global agency planning one square display advertisement.

You receive a reference photo of the product and a brief.

Brief:
- Target market: consumers in {geo}, during {season} there.
- Headline that must appear exactly: "{text}"

1. BRAND. Study the product's packaging: typefaces, colours, materials, tone. The brand's distinctive assets
   and the product stay exactly as they are; the ad must look like it came from this brand's creative team.

2. CONSUMER INSIGHT. Geography means the audience, not a backdrop. Ask: what does a real person in this market
   need from this product during this season, and how does the headline speak to that? Write one concrete,
   non-obvious insight grounded in how people there actually live in that season (climate, routines, homes,
   commutes, occasions) — not in national symbols.

3. USAGE MOMENT. Pick the real, everyday moment where that insight happens and the product is used, bought,
   gifted or needed.

4. LOCAL VERSION OF THE MOMENT. The moment may be universal, but show exactly how it looks in THIS market:
   the specific fixtures, fittings, objects, clothing and spaces that are part of this moment in an ordinary
   home, workplace, commute or street there — as locals actually have it, not an aspirational Western interior.
   Include at least 3 such details. Each one must pass BOTH tests:
   - motivated: it is genuinely part of the usage moment (passes the token test below), and
   - market-specific (swap test): if the market were relabelled to another country, this detail would have to change.
   Also use the real light and weather of that season and climate zone (tropical markets have wet/dry seasons).

5. PEOPLE. Representative casting is the strongest localisation lever. When the moment involves using, wearing,
   carrying, eating or gifting the product, show a person (or at least their hands and arms) from the target
   audience, in everyday styling, mid-action and natural — not posing to camera, no costumes. Keep the product
   clearly visible and unaltered.

6. TOKEN TEST — apply to every object and detail you plan: "Would this be in the scene if the ad were for
   the same product and moment in a different country?" If it is there only to signal nationality or culture
   (signature foods or drinks, souvenirs, charms, flags, costumes, famous objects, landmarks) and plays no
   role in the usage moment, REMOVE it. A festival appears only if it truly falls in this season AND the
   product genuinely plays a role in it. Fewer, motivated cues beat many decorative ones. The product stays the hero.

7. HEADLINE. Designed into the photograph, not pasted on: typography derived from the brand, a colour from the
   scene or brand palette with strong contrast, in natural negative space, crisp and fully legible.

Return JSON with these keys:
{{
  "brand_read": "the brand's typography, palette and tone as seen on the packaging",
  "consumer_insight": "one sentence",
  "usage_moment": "one sentence",
  "local_cues": [{{"cue": "...", "role_in_moment": "why it is part of this usage moment", "why_specific_to_market": "why it would change in another country"}}],
  "people": "who appears (or hands), styling and action — or why no person",
  "removed_tokens": ["decorative national/cultural props you considered and rejected"],
  "scene": "the full scene description",
  "composition": "camera angle, where the product sits, where the clean negative space is",
  "headline_typography": "typeface style derived from the brand (classification, weight, width, case, tracking)",
  "headline_colour": "colour from the scene or brand palette, with contrast",
  "headline_placement": "where the headline sits, size relative to the frame, alignment",
  "integration": "how the headline sits naturally in the image (light, depth, no boxes or banners)"
}}
```

## Planner v5 — lean planner + shot types

```
You are a senior art director planning one square display advertisement.
You receive a reference photo of the product and a brief.

Brief: target market = consumers in {geo}, during {season} there. Headline that must appear exactly: "{text}"

Think it through, then return a SHORT, sharp art direction — the image model performs best with few, precise instructions.

1. Brand: read the packaging's typefaces, colours and tone; the ad must look like the brand's own creative team made it.
2. Insight and moment: what does a person in this market need from this product in this season? Pick the real
   everyday moment where that happens.
3. Local version of that moment: choose at most 2–3 details that are BOTH part of the moment AND specific to how
   that moment looks in this market (they would have to change if the market changed), plus the real light and
   weather of that season and climate zone. No decorative national props, signature foods/drinks, souvenirs,
   landmarks or costumes that play no role in the moment.
4. Shot type — pick ONE that best carries the insight:
   - "still_life" (the default): the product in place, with the moment implied by traces (steam, a used towel,
     rain on glass, an open bag) — no people.
   - "hands_in_action": only when the product's benefit IS a physical action that a still life cannot show
     (applying, sharing, fastening). Hands or forearms only — never faces.
   - "environment": a wider view when the place or light itself carries the insight — no people, or only a
     distant cropped figure without a face.
   Most ads should be still_life; do not add hands by default.
5. Headline: designed into the photograph as one composition with the scene — typography derived from the brand,
   placed in negative space that the composition deliberately leaves for it, never in a separate band or banner.

Return JSON (keep every value brief):
{{
  "brand_read": "max 25 words",
  "consumer_insight": "max 25 words",
  "usage_moment": "max 20 words",
  "local_cues": [{{"cue": "max 12 words", "role_in_moment": "max 12 words", "why_specific_to_market": "max 12 words"}}],
  "shot_type": "still_life | hands_in_action | environment",
  "shot_type_reason": "max 15 words",
  "scene": "max 50 words: setting, light, weather, the 2–3 local details (hands only if hands_in_action)",
  "composition": "max 30 words: camera, product position, where the headline's negative space is",
  "headline_typography": "max 20 words",
  "headline_colour": "max 12 words",
  "headline_placement": "max 20 words",
  "integration": "max 20 words"
}}
```

## Image prompt v1/v2 — single prompt, no planner (v2 text shown; v1 said "show this place")

```python
def build_generation_prompt(brief: Brief) -> str:
    product = brief.product
    return "\n".join(
        [
            f"The attached image is the reference product: {product.brand} {product.name}.",
            "Create a square display advertisement that features this exact product.",
            "",
            "Product fidelity: keep the product identical to the reference — same shape, proportions, "
            "colours, materials, logo, and label text. You may change its angle, lighting, reflections, "
            "and how it sits in the scene, but never redesign it.",
            "",
            f"Target market: consumers in {brief.geo}, during {brief.season} there. Make the ad feel native "
            "and relevant to that audience — the climate, light, lifestyle, setting, and occasions that "
            "people in that market actually experience in that season. Do not add famous landmarks, "
            "skylines, or tourist imagery just to signal the location; include a recognisable place only "
            "if it genuinely supports the product or the message. Avoid clichés and stereotypes.",
            "",
            f'Headline: the ad must display this text exactly, character for character: "{brief.text}". '
            "Choose the typography, placement, and style that suit the design. Do not add any other "
            "slogans, captions, or words beyond the headline and the product's own packaging.",
            "",
            "Style: polished, professional advertising photography with clear space for the headline.",
        ]
    )
```

## Image prompt v3/v4/v4.1 — planned prompt template

```python
def build_planned_prompt(brief: Brief, plan: AdPlan) -> str:
    product = brief.product
    return "\n".join(
        [
            f"The attached image is the reference product: {product.brand} {product.name}.",
            "Create a square display advertisement that features this exact product, following the art direction below.",
            "",
            "Product fidelity: keep the product identical to the reference — same shape, proportions, "
            "colours, materials, logo, and label text. You may change its angle, lighting, reflections, "
            "and how it sits in the scene, but never redesign it or add parts to it.",
            "",
            *([f"Moment: {plan.usage_moment}"] if plan.usage_moment else []),
            *([f"People: {plan.people}"] if plan.people else []),
            f"Scene: {plan.scene}",
            "Local details that must be clearly visible: " + "; ".join(c.get("cue", "") for c in plan.local_cues) + ".",
            *([f"Do not include: {'; '.join(plan.removed_tokens)}."] if plan.removed_tokens else []),
            f"Composition: {plan.composition}",
            "",
            f'Headline: display this text exactly, character for character: "{brief.text}".',
            f"Typography: {plan.headline_typography}",
            f"Colour: {plan.headline_colour}",
            f"Placement: {plan.headline_placement}",
            f"Integration: {plan.integration}",
            "The headline must be crisp, fully legible, and look professionally typeset as part of the photograph. "
            "Do not add any other words beyond the headline and the product's own packaging.",
            "",
            "Style: high-end commercial advertising photography.",
        ]
    )
```

## Image prompt v5 — lean prompt template

```python
def build_lean_prompt(brief: Brief, plan: AdPlan) -> str:
    product = brief.product
    return "\n".join(
        [
            f"Square display advertisement for the attached product ({product.brand} {product.name}). "
            "Keep the product identical to the reference: shape, colours, logo and label text. Do not redesign it.",
            "",
            f"Composition: {plan.composition}",
            f"Scene: {plan.scene}",
            "",
            f'Headline, exactly: "{brief.text}" — {plan.headline_typography}; {plan.headline_colour}; {plan.headline_placement}. {plan.integration}',
            "",
            ("No people in the image." if plan.shot_type != "hands_in_action" else "Hands only, no faces.")
            + " No other text. High-end commercial photography.",
        ]
    )
```

## Image prompt v6 — single call, model plans then renders

```python
def build_single_call_prompt(brief: Brief) -> str:
    product = brief.product
    return "\n".join(
        [
            f"Square display advertisement for the attached product ({product.brand} {product.name}). "
            "Keep the product identical to the reference: shape, colours, logo and label text. Do not redesign it.",
            "",
            f"Target market: consumers in {brief.geo}, during {brief.season} there.",
            "Before creating the image, decide briefly and write it as 3 short lines of text:",
            "1. Insight: what someone there needs from this product in this season.",
            "2. Moment: the everyday moment where that happens, as it looks in this market — 2–3 details that belong "
            "to the moment and are specific to this market. No decorative national props, landmarks or costumes.",
            "3. Shot: the framing that best carries that moment, as long as the product is the hero (sharp, large enough "
            "that its logo and label are readable, roughly a third of the frame or more), the scene is close enough to "
            "read the local details, and the composition deliberately leaves clean negative space for the headline.",
            "Then create the ad: typography derived from the product's own packaging, with the headline set into the "
            "negative space the composition leaves for it — never a separate band or banner.",
            "",
            f'Headline, exactly: "{brief.text}". If people appear, their faces are not visible. No other text. High-end commercial photography.',
        ]
    )
```

## Image prompt D — art-directed template

```python
def build_art_directed_prompt(brief: Brief, plan: AdPlan) -> str:
    product = brief.product
    return "\n".join(
        [
            f"The attached image is the reference product: {product.brand} {product.name}.",
            "Create a square display advertisement that features this exact product, following the art direction below.",
            "",
            "Product fidelity: keep the product identical to the reference — same shape, proportions, "
            "colours, materials, logo, and label text. You may change its angle, lighting, reflections, "
            "and how it sits in the scene, but never redesign it or add parts to it.",
            "",
            f"Scene: {plan.scene}",
            f"Composition: {plan.composition}",
            "",
            f'Headline: display this text exactly, character for character: "{brief.text}".',
            f"Typography: {plan.headline_typography}",
            f"Colour: {plan.headline_colour}",
            f"Placement: {plan.headline_placement}",
            f"Integration: {plan.integration}",
            "The headline must be crisp, fully legible, and look professionally typeset as part of the photograph. "
            "Do not add any other words beyond the headline and the product's own packaging.",
            "",
            "Style: high-end commercial advertising photography.",
        ]
    )
```
