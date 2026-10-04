import hashlib

import streamlit as st
from common import show_image

from adgen.core.briefs import PRODUCT_IMAGES, Brief, Product, load_products
from adgen.core.checks import LABELLED_CHECKS, Verdict
from adgen.core.config import ProxySettings
from adgen.core.llm import LiteLLMClient
from adgen.pipeline import MAX_RETRIES, Attempt, PipelineResult, run_pipeline

st.set_page_config(page_title="Ad generator demo", layout="wide")


def uploaded_product(upload, brand: str, name: str) -> Product:
    data = upload.getvalue()
    product_id = f"upload_{hashlib.sha256(data).hexdigest()[:10]}"
    path = PRODUCT_IMAGES / f"{product_id}.jpg"
    if not path.exists():
        path.write_bytes(data)
    return Product(id=product_id, brand=brand, name=name, category="upload", split="demo", risk="")


def brief_form() -> tuple[Brief | None, int, bool]:
    products = load_products()
    with st.sidebar:
        st.header("Brief")
        source = st.radio("Product", ["Pick from catalogue", "Upload my own"], horizontal=True)
        product = None
        if source == "Pick from catalogue":
            product_id = st.selectbox("Reference product", list(products), format_func=lambda p: f"{products[p].brand} — {products[p].name}")
            product = products[product_id]
        else:
            upload = st.file_uploader("Product photo (clean packshot works best)", type=["jpg", "jpeg", "png"])
            brand = st.text_input("Brand")
            name = st.text_input("Product name")
            if upload and brand and name:
                product = uploaded_product(upload, brand, name)
        if product:
            show_image(product.image_path, width=200)
        geo = st.text_input("Target geography", "Mumbai, India")
        season = st.text_input("Season", "monsoon")
        text = st.text_input("Headline (must appear exactly)", "HYDRATION THAT LASTS")
        max_retries = st.slider("Max retries", 0, 3, MAX_RETRIES)
        missing_photo = product is not None and not product.image_path.exists()
        if missing_photo:
            st.warning("Reference photo not downloaded yet — run `mise run fetch` (Docker does this on start).")
        ready = bool(product and geo and season and text) and not missing_photo
        run = st.button("Generate ad", type="primary", disabled=not ready, width="stretch")
    brief = Brief(id="demo", product=product, split="demo", geo=geo, season=season, text=text) if ready else None
    return brief, max_retries, run


def show_attempt(attempt: Attempt) -> None:
    status = "✅ pass" if not attempt.failures else "❌ fails: " + ", ".join(attempt.failures)
    st.markdown(f"#### {attempt.label.replace('_', ' ')} — {status}")
    image_col, checks_col = st.columns([2, 3])
    with image_col:
        show_image(attempt.image_path)
    with checks_col:
        checks = attempt.evaluation.as_dict()["checks"]
        for key, title in LABELLED_CHECKS.items():
            icon = "✅" if checks[key]["verdict"] == Verdict.PASS else "❌"
            st.caption(f"{icon} **{title}** — {checks[key]['reason']}")
        st.caption(f"${attempt.cost_usd:.3f}")


def show_result(result: PipelineResult) -> None:
    st.divider()
    st.markdown("### Final")
    left, right = st.columns([2, 3])
    with left:
        show_image(result.final.image_path, caption="Final ad")
    with right:
        st.subheader(result.summary)
        st.metric("Total cost", f"${result.cost_usd:.3f}")
        st.metric("Attempts", len(result.attempts))
        st.caption(f"Trace: data/runs/{result.run_id}/trace.json")
        with open(result.final.image_path, "rb") as handle:
            st.download_button("Download final ad", handle, file_name=f"{result.run_id}.png", mime="image/png")


def main() -> None:
    st.title("Context-enriched ad generator")
    st.caption("Brief → art-direction planner → Gemini image → Claude judge → retry with critique → deterministic fallback")
    brief, max_retries, run = brief_form()
    try:
        ProxySettings.from_env()
    except RuntimeError:
        st.error("Set LITELLM_BASE_URL and LITELLM_API_KEY in .env to generate ads (see README §5). Tests, verify and scoring work without them.")
        return
    if run and brief:
        with st.spinner("Planning, generating and judging… (~30s per attempt)"):
            result = run_pipeline(LiteLLMClient(), brief, on_attempt=show_attempt, max_retries=max_retries)
        show_result(result)


main()
