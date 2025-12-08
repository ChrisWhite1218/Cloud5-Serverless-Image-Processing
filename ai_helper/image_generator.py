import base64
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-image-1"  # OpenAI image model (works on free tier)
DEFAULT_SIZE = "1024x1024"  # Default output resolution


class AIImageGenerationError(Exception):
    """Raised when the image-generation request fails."""


@dataclass
class ImageGenerationResult:
    prompt: str
    model: str
    size: str
    created: int
    image_bytes: bytes
    mime_type: str = "image/png"
    seed: Optional[int] = None
    revised_prompt: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class OpenAIImageGenerator:
    """
    Small helper around the OpenAI Images API with retry and validation.

    Example:
        generator = OpenAIImageGenerator()
        result = generator.generate("a cat in the snow")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        model: str = DEFAULT_MODEL,
        size: str = DEFAULT_SIZE,
        user: Optional[str] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.5,
        backoff_factor: float = 2.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")  # Pull from env by default
        if not self.api_key:
            raise AIImageGenerationError(
                "OPENAI_API_KEY is required for image generation."
            )

        self.model = model
        self.size = size
        self.user = user
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_factor = backoff_factor
        self.client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        user: Optional[str] = None,
        response_format: str = "b64_json",
    ) -> ImageGenerationResult:
        if not prompt or not prompt.strip():
            raise AIImageGenerationError("Prompt must be a non-empty string.")

        chosen_model = model or self.model
        chosen_size = size or self.size
        chosen_user = user or self.user
        # Base payload for OpenAI Images API
        payload = {
            "model": chosen_model,
            "prompt": prompt,
            "size": chosen_size,
            "n": 1,
            "response_format": response_format,
        }
        if chosen_user:
            payload["user"] = chosen_user

        attempt = 0
        backoff = self.initial_backoff
        last_error: Optional[Exception] = None

        while attempt < self.max_retries:
            try:
                start_time = time.time()
                response = self.client.images.generate(**payload)
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    "Image generated with model=%s size=%s in %sms",
                    chosen_model,
                    chosen_size,
                    duration_ms,
                )
                return self._parse_response(
                    prompt=prompt,
                    response=response,
                    model=chosen_model,
                    size=chosen_size,
                    duration_ms=duration_ms,
                    user=chosen_user,
                )
            except OpenAIError as exc:  # covers rate-limit + server errors
                last_error = exc
                should_retry = getattr(exc, "status_code", None) in (
                    429,
                    500,
                    502,
                    503,
                    504,
                )
                logger.warning(
                    "OpenAI image generation failed (attempt %s/%s): %s",
                    attempt + 1,
                    self.max_retries,
                    exc,
                )
                if not should_retry or attempt >= self.max_retries - 1:
                    raise AIImageGenerationError(
                        f"Image generation failed after {attempt + 1} attempts: {exc}"
                    ) from exc

                time.sleep(backoff)  # exponential backoff for transient errors
                backoff *= self.backoff_factor
                attempt += 1
            except Exception as exc:  # pragma: no cover - defensive catch
                last_error = exc
                logger.exception("Unexpected error during image generation.")
                raise AIImageGenerationError(str(exc)) from exc

        raise AIImageGenerationError(
            f"Image generation failed after retries: {last_error}"
        )

    @staticmethod
    def _parse_response(
        *,
        prompt: str,
        response: object,
        model: str,
        size: str,
        duration_ms: int,
        user: Optional[str],
    ) -> ImageGenerationResult:
        try:
            data = response.data[0]  # first (and only) generated image
            b64_payload = getattr(data, "b64_json", None)
            if not b64_payload:
                raise AIImageGenerationError("OpenAI response missing image payload.")

            image_bytes = base64.b64decode(b64_payload)
            created = getattr(data, "created", None) or getattr(response, "created", 0)
            seed = getattr(data, "seed", None)
            revised_prompt = getattr(data, "revised_prompt", None)

            metadata = {
                "duration_ms": str(duration_ms),
                "size": size,
            }
            if user:
                metadata["user"] = user
            if seed is not None:
                metadata["seed"] = str(seed)
            request_id = getattr(response, "request_id", None)
            if request_id:
                metadata["request_id"] = request_id

            return ImageGenerationResult(
                prompt=prompt,
                model=model,
                size=size,
                created=created or int(time.time()),
                image_bytes=image_bytes,
                seed=seed,
                revised_prompt=revised_prompt,
                metadata=metadata,
            )
        except AIImageGenerationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch
            logger.exception("Failed to parse OpenAI response.")
            raise AIImageGenerationError("Invalid OpenAI image response.") from exc


def generate_image(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    user: Optional[str] = None,
    max_retries: int = 3,
) -> ImageGenerationResult:
    """
    Convenience wrapper for one-off image generation.
    """
    generator = OpenAIImageGenerator(
        api_key=api_key,
        model=model,
        size=size,
        user=user,
        max_retries=max_retries,
    )
    return generator.generate(prompt)

