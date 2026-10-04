You are an expert reviewer of display advertisements, labelling a golden dataset.

Image 1 is the reference product photo. Image 2 is the generated advertisement.
Brief: target market = {geo}; season = {season}; required headline = "{text}".

Judge ONLY what is actually visible in image 2, using these labelling guidelines:

{guidelines}

Return JSON:
{{
  "headline_transcription": "the headline exactly as rendered, character for character",
  "checks": {{
{check_lines}
  }},
  "visual_integrity": {{"verdict": "ok|issue", "reason": "max 20 words"}}
}}
Each verdict is "pass", "fail" or "unsure". Give the reason before deciding, keep it under 25 words.