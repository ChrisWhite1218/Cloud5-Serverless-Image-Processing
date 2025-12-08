## M2 AI Image Helper

This module wraps OpenAI's Images API to generate images from text prompts with retries, validation, and convenient defaults suitable for AWS Lambda usage.

### Components
- `ai_helper/image_generator.py`
  - `OpenAIImageGenerator`: retry/backoff wrapper around the OpenAI client.
  - `ImageGenerationResult`: structured response with image bytes, prompt, model, size, metadata (duration, request_id, seed if provided).
  - `generate_image()`: one-shot convenience helper for callers that just need a single image.

### Dependencies
- Install: `pip install -r requirements.txt`
- Env var: `OPENAI_API_KEY` (for production, load from AWS Secrets Manager and inject into the Lambda runtime).
- Defaults use model `gpt-image-1` and size `1024x1024`, which work on the OpenAI free tier.

### Quick local smoke test
```
python
from ai_helper import generate_image
result = generate_image("a postcard illustration of a mountain sunrise")
with open("out.png", "wb") as f:
    f.write(result.image_bytes)
print("metadata:", result.metadata)
```

### Error handling and retries
- Validates non-empty prompts before calling the API.
- Retries on common transient statuses (429, 500, 502, 503, 504) with exponential backoff (configurable via `max_retries`, `initial_backoff`, `backoff_factor`).
- Raises `AIImageGenerationError` with context on failure.

### Integration notes (for M3 and beyond)
- Lambda handler should import `generate_image` or `OpenAIImageGenerator` and write the resulting `image_bytes` to `processed/ai/` in S3 with accompanying metadata (prompt, model, size, duration_ms, request_id, seed).
- Capture `revised_prompt` if returned by the API and log it for traceability.
- Ensure the Lambda role can read the secret, call OpenAI, and write to S3; keep API keys out of code and plain env files.


