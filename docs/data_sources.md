# Data sources and licences

This repository publishes **code, prompts, labels, judge outputs and logs** for every golden item, but **images only where their licence allows**.
Everything else is linked to its source and can be re-fetched (reference photos) or regenerated (ads).

## Reference product photos

| Product id | Product | Source | Link | Licence / status | Golden items |
|---|---|---|---|---|---|
| `kiehls_ultra_facial_cream` | Kiehl's — Ultra Facial Cream | Amazon Reviews 2023 | [amazon.com/dp/B000VE9E7A](https://www.amazon.com/dp/B000VE9E7A) | © brand / Amazon — not redistributed | 6 |
| `neutrogena_hydro_boost` | Neutrogena — Hydro Boost Whipped Body Balm | Amazon Reviews 2023 | [amazon.com/dp/B0B3PHXRY6](https://www.amazon.com/dp/B0B3PHXRY6) | © brand / Amazon — not redistributed | 3 |
| `cerave_moisturising_lotion` | CeraVe — Moisturising Lotion 473ml | Amazon Reviews 2023 | [amazon.com/dp/B0947NS7V9](https://www.amazon.com/dp/B0947NS7V9) | © brand / Amazon — not redistributed | 4 |
| `ownpwr_preworkout` | OWN PWR — Elite Series Pre Workout | Amazon Berkeley Objects | ABO item `B07CR9K6ZC` · [image](https://amazon-berkeley-objects.s3.amazonaws.com/images/original/f3/f3c7796c.jpg) | **CC BY 4.0** — committed | 5 |
| `bbq_chips_365` | 365 Everyday Value — Organic Barbeque Potato Chips | Amazon Berkeley Objects | ABO item `B07FW8NV5R` · [image](https://amazon-berkeley-objects.s3.amazonaws.com/images/original/0b/0b8887e2.jpg) | **CC BY 4.0** — committed | 5 |
| `nutella_biscuits` | Nutella — Biscuits x22 | Open Food Facts | [product page](https://world.openfoodfacts.org/product/8000500310427) | **CC BY-SA 3.0** — committed | 5 |
| `duncanhines_mugcake` | Duncan Hines — Mug Cakes Chocolate Chip Cookie | Amazon Reviews 2023 | [amazon.com/dp/B0994Z334P](https://www.amazon.com/dp/B0994Z334P) | © brand / Amazon — not redistributed | 6 |
| `quaker_oats` | Quaker — Old Fashioned Oats 42oz | Amazon Reviews 2023 | [amazon.com/dp/B0C5Z4J6L1](https://www.amazon.com/dp/B0C5Z4J6L1) | © brand / Amazon — not redistributed | 4 |
| `versace_eau_fraiche` | Versace — Man Eau Fraîche | Amazon Reviews 2023 | [amazon.com/dp/B0014XANUO](https://www.amazon.com/dp/B0014XANUO) | © brand / Amazon — not redistributed | 5 |
| `jomalone_wood_sage` | Jo Malone — Wood Sage & Sea Salt Cologne | Amazon Reviews 2023 | [amazon.com/dp/B076VDSPDX](https://www.amazon.com/dp/B076VDSPDX) | © brand / Amazon — not redistributed | 5 |
| `bodum_chrome_kettle` | Bodum — Bistro Gooseneck Kettle, Chrome | Amazon Reviews 2023 | [amazon.com/dp/B08FC48BZD](https://www.amazon.com/dp/B08FC48BZD) | © brand / Amazon — not redistributed | 4 |
| `rayban_rb3447_mirror` | Ray-Ban — RB3447 Round, Green Mirror | Amazon Reviews 2023 | [amazon.com/dp/B00J3YF7Q6](https://www.amazon.com/dp/B00J3YF7Q6) | © brand / Amazon — not redistributed | 4 |
| `timex_expedition_chrono` | Timex — Expedition Scout Chronograph | Amazon Reviews 2023 | [amazon.com/dp/B01M3P1ES7](https://www.amazon.com/dp/B01M3P1ES7) | © brand / Amazon — not redistributed | 4 |
| `casio_gshock_mtg` | Casio — G-Shock MT-G MTG900 | Amazon Reviews 2023 | [amazon.com/dp/B000248ZEW](https://www.amazon.com/dp/B000248ZEW) | © brand / Amazon — not redistributed | 4 |
| `adidas_grand_court` | adidas — Grand Court | Amazon Reviews 2023 | [amazon.com/dp/B09TJTD1ZB](https://www.amazon.com/dp/B09TJTD1ZB) | © brand / Amazon — not redistributed | 5 |
| `newbalance_515` | New Balance — 515 V1 Classic | Amazon Reviews 2023 | [amazon.com/dp/B0951NCR7Z](https://www.amazon.com/dp/B0951NCR7Z) | © brand / Amazon — not redistributed | 4 |
| `nike_lunarepic_flyknit` | Nike — LunarEpic Low Flyknit 2 | Amazon Reviews 2023 | [amazon.com/dp/B06XKT2RPL](https://www.amazon.com/dp/B06XKT2RPL) | © brand / Amazon — not redistributed | 7 |
| `carhartt_plaid_shirt` | Carhartt — Essential Plaid Work Shirt | Amazon Reviews 2023 | [amazon.com/dp/B0892J2PV5](https://www.amazon.com/dp/B0892J2PV5) | © brand / Amazon — not redistributed | 4 |
| `legendary_whitetails_flannel` | Legendary Whitetails — Women's Flannel Shirt | Amazon Reviews 2023 | [amazon.com/dp/B0BSQMNM4R](https://www.amazon.com/dp/B0BSQMNM4R) | © brand / Amazon — not redistributed | 4 |
| `londonfog_houndstooth_luggage` | London Fog — Cambridge II Carry-On, Houndstooth | Amazon Reviews 2023 | [amazon.com/dp/B079XHGHKY](https://www.amazon.com/dp/B079XHGHKY) | © brand / Amazon — not redistributed | 5 |
| `pandora_family_roots` | Pandora — Openwork Family Roots Charm | Amazon Reviews 2023 | [amazon.com/dp/B07G539CPB](https://www.amazon.com/dp/B07G539CPB) | © brand / Amazon — not redistributed | 6 |
| `pandora_sister_heart` | Pandora — Sister's Love CZ Charm | Amazon Reviews 2023 | [amazon.com/dp/B01IF1LO3C](https://www.amazon.com/dp/B01IF1LO3C) | © brand / Amazon — not redistributed | 4 |
| `casemate_soap_bubble` | Case-Mate — Soap Bubble iPhone 13 Pro Case | Amazon Reviews 2023 | [amazon.com/dp/B0BZK5JD37](https://www.amazon.com/dp/B0BZK5JD37) | © brand / Amazon — not redistributed | 6 |

`mise run fetch` downloads all 23 reference photos from the URLs pinned in [`data/products/manifest.yaml`](../data/products/manifest.yaml) into `data/products/images/` (git-ignored except the three openly licensed ones).

## Source datasets

- **Amazon Reviews 2023** (McAuley Lab, UCSD) — [project page](https://amazon-reviews-2023.github.io/) · [Hugging Face](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023). The dataset publishes product metadata with links to Amazon-hosted images; it grants no licence to the images themselves, which belong to Amazon and the brands. We use them for non-commercial research only and **do not redistribute** them — the manifest stores the ASIN and image URL instead.
- **Amazon Berkeley Objects (ABO)** — Collins et al., CVPR 2022 · [dataset](https://amazon-berkeley-objects.s3.amazonaws.com/index.html) · licensed **CC BY 4.0**. Used: OWN PWR Elite Series Pre Workout, 365 Everyday Value Organic Barbeque Potato Chips.
- **Open Food Facts** — [world.openfoodfacts.org](https://world.openfoodfacts.org) · product images licensed **CC BY-SA 3.0** by their contributors. Used: Nutella Biscuits (front image, revision 586).

## Generated advertisements

All 109 golden-set ads were generated with Gemini 3.1 Flash Image from the reference photos above (or are single-change edits of those ads).

| Ads | In the repo? | Licence |
|---|---|---|
| 15 ads derived from the ABO and Open Food Facts photos (OWN PWR ×5, 365 BBQ chips ×5, Nutella ×5) | **yes** | derived from ABO photos: CC BY 4.0 · derived from the Open Food Facts photo: CC BY-SA 3.0 (share-alike) |
| 94 ads derived from Amazon Reviews 2023 photos | no — not redistributed | — |

Every golden image's **SHA-256** is recorded in [`data/golden/items.yaml`](../data/golden/items.yaml); `mise run verify` checks any image that is present against it. Regenerated ads will not be pixel-identical (image generation is not deterministic), but all labels, judge outputs and scores are published, so every reported number can be re-derived without the images (see README §6).

## Trademarks

Brand names, logos and packaging designs visible in any image are trademarks of their respective owners. They appear only to evaluate image-generation fidelity in a non-commercial research setting; no affiliation or endorsement is implied.

## Fonts

`assets/fonts/` — Inter, Playfair Display, Oswald — SIL Open Font License 1.1 (licence files included).
