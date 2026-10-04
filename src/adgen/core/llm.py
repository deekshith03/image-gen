import base64
import io
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from PIL import Image

from adgen.core.config import MAX_EDGE, ProxySettings

DATA_URI = re.compile(r"data:image/[\w.+-]+;base64,(.+)", re.S)
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
COST_HEADER = "x-litellm-response-cost"


@dataclass(frozen=True)
class ImageResponse:
    image: Image.Image
    model: str
    cost_usd: float
    latency_s: float


def image_to_data_uri(path: Path, max_edge: int = 1536) -> str:
    image = Image.open(path).convert("RGB")
    image.thumbnail((max_edge, max_edge))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def fit_to_max_edge(image: Image.Image, max_edge: int = MAX_EDGE) -> Image.Image:
    if max(image.size) <= max_edge:
        return image
    resized = image.copy()
    resized.thumbnail((max_edge, max_edge), Image.LANCZOS)
    return resized


def parse_json_object(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in model output: {text[:200]!r}")
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", candidate))


def find_data_uris(node) -> list[str]:
    if isinstance(node, dict):
        return [uri for value in node.values() for uri in find_data_uris(value)]
    if isinstance(node, list):
        return [uri for value in node for uri in find_data_uris(value)]
    if isinstance(node, str) and (match := DATA_URI.match(node)):
        return [match.group(1)]
    return []


def user_message(prompt: str, images: list[Path]) -> list[dict]:
    content = [{"type": "image_url", "image_url": {"url": image_to_data_uri(path)}} for path in images]
    content.append({"type": "text", "text": prompt})
    return [{"role": "user", "content": content}]


def response_cost(response: httpx.Response) -> float:
    return float(response.headers.get(COST_HEADER) or 0)


class LiteLLMClient:
    def __init__(self, settings: ProxySettings | None = None, timeout: float = 180, max_attempts: int = 4):
        self.settings = settings or ProxySettings.from_env()
        self.max_attempts = max_attempts
        self.http = httpx.Client(
            base_url=self.settings.base_url,
            headers={"Authorization": f"Bearer {self.settings.api_key}"},
            timeout=timeout,
        )

    def _post(self, payload: dict) -> httpx.Response:
        for attempt in range(1, self.max_attempts + 1):
            last_attempt = attempt == self.max_attempts
            try:
                response = self.http.post("/v1/chat/completions", json=payload)
            except httpx.TransportError:
                if last_attempt:
                    raise
            else:
                if response.status_code not in RETRYABLE_STATUS or last_attempt:
                    response.raise_for_status()
                    return response
            time.sleep(2**attempt)
        raise AssertionError("retry loop exited without returning")

    def generate_image(self, model: str, prompt: str, reference_images: list[Path]) -> ImageResponse:
        started = time.monotonic()
        response = self._post({"model": model, "modalities": ["image", "text"], "messages": user_message(prompt, reference_images)})
        body = response.json()
        images = find_data_uris(body)
        if not images:
            finish = body.get("choices", [{}])[0].get("finish_reason")
            raise RuntimeError(f"{model} returned no image (finish_reason={finish})")
        return ImageResponse(
            image=Image.open(io.BytesIO(base64.b64decode(images[0]))).convert("RGB"),
            model=model,
            cost_usd=response_cost(response),
            latency_s=round(time.monotonic() - started, 2),
        )

    def chat_json(self, model: str, prompt: str, images: list[Path] | None = None, parse_attempts: int = 2) -> tuple[dict, float]:
        payload = {"model": model, "messages": user_message(prompt, images or []), "response_format": {"type": "json_object"}}
        total_cost = 0.0
        for attempt in range(1, parse_attempts + 1):
            response = self._post(payload)
            total_cost += response_cost(response)
            try:
                return parse_json_object(response.json()["choices"][0]["message"]["content"]), total_cost
            except (ValueError, json.JSONDecodeError):
                if attempt == parse_attempts:
                    raise
        raise AssertionError("parse loop exited without returning")
