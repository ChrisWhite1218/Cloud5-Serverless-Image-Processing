"""
Helpers for AI-powered image generation.

The main entry point for most callers is `generate_image`, which wraps
`OpenAIImageGenerator.generate` with sensible defaults.
"""

from .image_generator import (
    AIImageGenerationError,
    ImageGenerationResult,
    OpenAIImageGenerator,
    generate_image,
)

__all__ = [
    "AIImageGenerationError",
    "ImageGenerationResult",
    "OpenAIImageGenerator",
    "generate_image",
]

