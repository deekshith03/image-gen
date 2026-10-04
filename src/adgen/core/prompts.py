from functools import cache

from adgen.core.config import PROMPTS


@cache
def load_prompt(prompt: str) -> str:
    return (PROMPTS / f"{prompt}.md").read_text()


def render_prompt(prompt: str, /, **values: str) -> str:
    return load_prompt(prompt).format(**values)
