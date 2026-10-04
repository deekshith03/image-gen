You are checking product fidelity in a display advertisement.

Image 1 is the reference product photo: {brand} {name}. Image 2 is the advertisement.

Compare the product in image 2 against image 1. Staging is allowed: angle, lighting, reflections, scale,
water, snow or steam on the product, and the product being held or worn. Identity is not allowed to change.

Check each and note what you see:
- presence — the actual product or its package is shown. If only something pictured ON the package appears
  (e.g. the food from the box, without the box), the product is missing.
- shape and proportions
- colours and materials
- logo and brand name (spelling, form, placement)
- prominent product text — brand name, product name, dial markings and numerals, large label words — must be
  correct; garbled or nonsense characters there count as a change. Tiny fine print (ingredients,
  certifications, net weight) that is unreadable at this size is ignored.
- counts — count the repeated design elements in BOTH images and compare the numbers (stripes, stones,
  sub-dials, buttons, lenses, items in a set)
- parts — nothing missing, nothing added (e.g. a charm suddenly on a chain)

Return JSON:
{{
  "observations": {{"presence": "...", "shape": "...", "colour": "...", "logo": "...", "prominent_text": "...", "counts": "reference: … / ad: …", "parts": "..."}},
  "reason": "max 30 words",
  "verdict": "pass | fail"
}}
Verdict is "fail" if any identity change is visible.