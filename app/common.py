from pathlib import Path

import streamlit as st

NOT_REDISTRIBUTED = "Image not included in the public repo (licence) — see docs/data_sources.md · reference photos: `mise run fetch`"


def show_image(path: Path, caption: str | None = None, width: int | str = "stretch") -> None:
    if path.exists():
        st.image(str(path), caption=caption, width=width)
    else:
        st.info(f"{caption + ': ' if caption else ''}{NOT_REDISTRIBUTED}")
