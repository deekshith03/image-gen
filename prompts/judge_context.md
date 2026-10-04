You are reviewing whether a display advertisement fits its target market and season.

Brief: target market = consumers in {geo}; season = {season} there.

The geography is the target audience, not a required backdrop. The product and its packaging are global:
their language or text never counts against the market. Answer three questions, giving your reason before
each verdict. Each problem belongs to exactly ONE question — never fail a second question for the same problem.

1. season_fit — Does anything clearly contradict {season} as it is actually experienced in {geo}? Use that
   place's real climate, not a generic one (e.g. December in Australia is summer; tropical markets have
   wet/dry seasons; Mexico City's autumn follows the rainy season and stays green). Missing seasonal cues
   are not a failure. All weather and season problems belong here only.
2. market_fit — Does anything contradict this market: another country's landmark, festival, script or
   culture, or a neighbouring culture standing in for this one? A subtle, believable scene passes; it does
   not need to show the city's name or famous sights. Wrong-country and wrong-festival problems belong here only.
3. no_cliche — Is the ad free of clichés about THIS market: its own famous landmark forced in as the location
   signal; stereotypes; stereotyped colour filters over a whole street or city scene (drab dusty yellow/orange haze, sepia) — warm lamp,
   candle or golden-hour light that fits the moment is not a filter;
   or token props — signature foods, drinks, flags, souvenirs or everyday objects placed next to an unrelated
   product only to say "this is <country>" (e.g. a chai glass and flip-flops beside a moisturiser). Real places,
   landmarks and objects are fine when they genuinely fit the product or the moment.

Return JSON:
{{
  "season_fit": {{"reason": "max 30 words", "verdict": "pass | fail"}},
  "market_fit": {{"reason": "max 30 words", "verdict": "pass | fail"}},
  "no_cliche": {{"reason": "max 30 words", "verdict": "pass | fail"}}
}}