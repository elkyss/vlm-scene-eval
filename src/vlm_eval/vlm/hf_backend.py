"""Generic Hugging Face image-text-to-text backend (SmolVLM, Qwen2-VL, ...)."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from vlm_eval.vlm.base import BACKENDS, VLMRequest, VLMResponse

log = logging.getLogger(__name__)


@BACKENDS.register("hf")
class HFVisionChatBackend:
    """Runs any chat-template VLM supported by ``AutoModelForImageTextToText``.

    The model is loaded lazily on the first request so building a pipeline is cheap.
    Decoding is greedy (``do_sample=False``) so runs are reproducible.
    """

    def __init__(
        self,
        model_id: str = "HuggingFaceTB/SmolVLM-500M-Instruct",
        max_new_tokens: int = 256,
        device: str = "auto",
        max_image_side: int | None = 768,
        revision: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.revision = revision  # pin a Hugging Face commit for reproducibility
        self.max_new_tokens = max_new_tokens
        self.max_image_side = max_image_side
        self._device = device
        self._model: Any = None
        self._processor: Any = None

    @property
    def name(self) -> str:
        return self.model_id.split("/")[-1]

    @property
    def signature(self) -> str:
        return (
            f"{self.model_id}@{self.revision or 'default'}|max_new_tokens={self.max_new_tokens}"
            f"|max_image_side={self.max_image_side}|greedy"
        )

    @property
    def resolved_revision(self) -> str | None:
        """The Hugging Face commit used (for the run manifest), even if nothing was loaded."""
        if self._model is not None:
            loaded = getattr(self._model.config, "_commit_hash", None)
            if loaded:
                return str(loaded)
        try:
            from huggingface_hub import constants
        except ImportError:
            return self.revision
        ref = (
            Path(constants.HF_HUB_CACHE)
            / f"models--{self.model_id.replace('/', '--')}"
            / "refs"
            / (self.revision or "main")
        )
        return ref.read_text().strip() if ref.exists() else self.revision

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        device = self._device
        if device == "auto":
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "mps"
                if torch.backends.mps.is_available()
                else "cpu"
            )
        dtype = torch.float32 if device == "cpu" else torch.float16
        log.info("Loading %s on %s", self.model_id, device)
        self._processor = AutoProcessor.from_pretrained(self.model_id, revision=self.revision)
        model_cls: Any = AutoModelForImageTextToText
        self._model = model_cls.from_pretrained(
            self.model_id, revision=self.revision, dtype=dtype
        ).to(device)
        self._model.eval()
        self._device = device

    def generate(self, request: VLMRequest) -> VLMResponse:
        import torch

        if self._model is None:
            self._load()
        start = time.perf_counter()
        images = [self._resize(img) for img in request.images.load()]
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"} for _ in images]
                + [{"type": "text", "text": request.prompt}],
            }
        ]
        text = self._processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self._processor(text=[text], images=images, return_tensors="pt").to(self._device)
        with torch.inference_mode():
            out = self._model.generate(
                **inputs, max_new_tokens=self.max_new_tokens, do_sample=False
            )
        new_tokens = out[:, inputs["input_ids"].shape[1] :]
        text = str(self._processor.batch_decode(new_tokens, skip_special_tokens=True)[0]).strip()
        return VLMResponse(text, time.perf_counter() - start)

    def _resize(self, image: Any) -> Any:
        if self.max_image_side is None:
            return image
        image = image.copy()
        image.thumbnail((self.max_image_side, self.max_image_side))
        return image
