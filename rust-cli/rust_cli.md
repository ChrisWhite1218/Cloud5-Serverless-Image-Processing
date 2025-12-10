## Rust CLI for Cloud5 Image Generation

This CLI sends a prompt to your backend HTTP endpoint (Function URL / API Gateway) and saves the returned image. It does **not** expose or require the OpenAI key on the client side.

### Prerequisites
- Rust toolchain with Cargo.
- Backend HTTP endpoint that accepts `POST` JSON `{"prompt": "<text>"}` and returns:
  ```json
  {
    "image_base64": "<base64-encoded PNG>",
    "metadata": { ... optional ... }
  }
  ```
- Your backend uses the OpenAI key server-side (e.g., via Secrets Manager). End users don’t need the key.

### Quick start
Replace `https://<function-url>/` with your real Function URL or API Gateway URL.

macOS/Linux:
```bash
cd rust-cli
API_URL="https://<function-url>/" cargo run -- "a postcard illustration of a mountain sunrise"
```

Windows (cmd):
```cmd
cd rust-cli
set "API_URL=https://<function-url>/"
cargo run -- "a postcard illustration of a mountain sunrise"
```

Windows (PowerShell):
```powershell
cd rust-cli
$env:API_URL="https://<function-url>/"
cargo run -- "a postcard illustration of a mountain sunrise"
```

Output defaults to `out.png` in the current directory. To change the filename:
```bash
cargo run -- --output my.png "a sunset over the ocean"
```

### Arguments
- `prompt` (positional, required): the text prompt.
- `--output` (optional): output file name, default `out.png`.

### Notes
- Keep your backend protected if needed (e.g., API Gateway auth or a custom token header). The CLI currently assumes open access; add a token header in `src/main.rs` if your backend requires it.

