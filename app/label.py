import random

import streamlit as st
from common import show_image

from adgen.core.briefs import Brief, load_briefs
from adgen.core.checks import CULTURAL_CHECKS, LABELLED_CHECKS, Verdict
from adgen.core.config import DATA, LOCKED_STRATEGY, ROOT
from adgen.golden.ground_truth import is_india
from adgen.golden.items import GoldenItem, Tier, blind_item_ids, load_items
from adgen.golden.labels import ANSWERS, load_labels, save_label
from adgen.golden.panel import load_panel, merge_verdicts

TIER_NAMES = {
    Tier.PLANTED: "Tier 1 · planted edits (1 question)",
    Tier.EARLIER: "Tier 2 · earlier-version issues (1 question)",
    Tier.FINAL: "Tier 3 · final ads (confirm / flip)",
}
VERDICTS = [str(v) for v in Verdict]
SHUFFLE_SEED = 7

st.set_page_config(page_title="Ad labelling", layout="wide")


@st.cache_data
def shuffled_item_ids() -> list[str]:
    ids = list(load_items())
    random.Random(SHUFFLE_SEED).shuffle(ids)
    return ids


def sidebar(items: dict[str, GoldenItem], labels: dict[str, dict]) -> tuple[str, Tier, bool]:
    with st.sidebar:
        labeller = st.text_input("Labeller", key="labeller")
        tier = st.radio("Tier", list(TIER_NAMES), format_func=TIER_NAMES.get, key="tier")
        only_unlabelled = st.toggle("Only unlabelled", value=True)
        for each, name in TIER_NAMES.items():
            in_tier = [i for i in items.values() if i.tier == each]
            done = sum(i.item_id in labels for i in in_tier)
            st.progress(done / len(in_tier), text=f"{name.split(' ·')[0]}: {done}/{len(in_tier)}")
        with st.expander("Guidelines"):
            st.markdown((ROOT / "docs" / "labelling_guidelines.md").read_text())
    return labeller.strip(), tier, only_unlabelled


def navigation(queue: list[GoldenItem], tier: Tier, labels: dict[str, dict]) -> GoldenItem:
    key = f"pos-{tier}"
    st.session_state[key] = min(st.session_state.get(key, 0), len(queue) - 1)
    item = queue[st.session_state[key]]
    prev_col, info_col, next_col = st.columns([1, 6, 1])
    if prev_col.button("← Prev", disabled=st.session_state[key] == 0):
        st.session_state[key] -= 1
        st.rerun()
    status = " · ✅ labelled" if item.item_id in labels else ""
    info_col.markdown(f"**{TIER_NAMES[tier]}** — item {st.session_state[key] + 1} of {len(queue)}{status}")
    if next_col.button("Next →", disabled=st.session_state[key] >= len(queue) - 1):
        st.session_state[key] += 1
        st.rerun()
    return item


def brief_header(brief: Brief) -> None:
    st.markdown(f"**Market:** {brief.geo} · **Season:** {brief.season}")
    st.markdown("**Required text:**")
    st.code(brief.text, language=None)


def question_view(item: GoldenItem, brief: Brief, existing: dict, labeller: str) -> dict | None:
    if item.tier == Tier.PLANTED:
        original = DATA / "ads" / "natural" / LOCKED_STRATEGY / f"{brief.id}.png"
        show_image(original, caption="Original (before the edit)", width=220)
    else:
        show_image(brief.product.image_path, caption=f"Reference: {brief.product.brand} {brief.product.name}", width=200)
    st.markdown(f"### {item.question}")
    note = st.text_input("Note (optional)", value=existing.get("note", ""), key=f"{item.item_id}-note")
    for answer, column in zip(ANSWERS, st.columns(len(ANSWERS)), strict=True):
        label = answer.capitalize() + (" ✓" if existing.get("answer") == answer else "")
        if column.button(label, key=f"{item.item_id}-{answer}", width="stretch", type="primary" if answer == "yes" else "secondary"):
            return {"item_id": item.item_id, "tier": int(item.tier), "labeller": labeller, "question": item.question, "answer": answer, "note": note.strip()}
    return None


def final_ad_view(item: GoldenItem, brief: Brief, existing: dict, labeller: str, reviews: list[dict], blind: bool) -> dict | None:
    show_image(brief.product.image_path, caption=f"Reference: {brief.product.brand} {brief.product.name}", width=180)
    prefill = {} if blind else {key: str(verdict) for key, verdict in merge_verdicts(reviews).items()}
    if is_india(brief) and not blind:
        prefill.update(dict.fromkeys(CULTURAL_CHECKS))
    if blind:
        st.info("Label this one from scratch (no pre-fill).")

    with st.form(key=f"form-{item.item_id}"):
        verdicts, notes = {}, {}
        for key, title in LABELLED_CHECKS.items():
            previous = existing.get("checks", {}).get(key, {}).get("verdict") or prefill.get(key)
            index = VERDICTS.index(previous) if previous in VERDICTS else None
            verdicts[key] = st.radio(title, VERDICTS, index=index, horizontal=True, key=f"{item.item_id}-{key}")
            if not blind and reviews:
                st.caption(" · ".join(f"*{r['model'].split('/')[-1]}*: {r.get('checks', {}).get(key, {}).get('reason', '')}" for r in reviews))
            notes[key] = st.text_input(
                f"{title} note",
                value=existing.get("checks", {}).get(key, {}).get("note", ""),
                key=f"{item.item_id}-{key}-note",
                label_visibility="collapsed",
                placeholder=f"{title}: why (optional)",
            )
        integrity_options = ["ok", "issue"]
        integrity = st.radio(
            "Visual integrity",
            integrity_options,
            horizontal=True,
            index=integrity_options.index(existing.get("visual_integrity", "ok")),
            key=f"{item.item_id}-integrity",
        )
        appeal = st.select_slider("Appeal (optional)", options=["–", 1, 2, 3, 4, 5], value=existing.get("appeal") or "–", key=f"{item.item_id}-appeal")
        submitted = st.form_submit_button("Save & next", type="primary", width="stretch")

    if not submitted:
        return None
    if missing := [LABELLED_CHECKS[k] for k, v in verdicts.items() if v is None]:
        st.error(f"Choose a verdict for: {', '.join(missing)}")
        return None
    return {
        "item_id": item.item_id,
        "tier": int(item.tier),
        "labeller": labeller,
        "prefill_shown": not blind,
        "prefill": prefill,
        "checks": {k: {"verdict": verdicts[k], "note": notes[k].strip()} for k in LABELLED_CHECKS},
        "visual_integrity": integrity,
        "appeal": None if appeal == "–" else appeal,
    }


def main() -> None:
    items, briefs, labels = load_items(), load_briefs(), load_labels()
    labeller, tier, only_unlabelled = sidebar(items, labels)
    queue = [items[i] for i in shuffled_item_ids() if items[i].tier == tier and not (only_unlabelled and i in labels)]
    if not queue:
        st.success(f"{TIER_NAMES[tier]} — all done.")
        return

    item = navigation(queue, tier, labels)
    brief = briefs[item.brief_id]
    existing = labels.get(item.item_id, {})

    ad_col, side_col = st.columns([3, 2])
    with ad_col:
        show_image(item.image)
    with side_col:
        brief_header(brief)
        if tier == Tier.FINAL:
            label = final_ad_view(item, brief, existing, labeller, load_panel().get(item.item_id, []), item.item_id in blind_item_ids(items))
        else:
            label = question_view(item, brief, existing, labeller)

    if not label:
        return
    if not labeller:
        st.error("Enter your name in the sidebar first.")
        return
    save_label(label)
    if not only_unlabelled:
        st.session_state[f"pos-{tier}"] = min(st.session_state[f"pos-{tier}"] + 1, len(queue) - 1)
    st.rerun()


main()
