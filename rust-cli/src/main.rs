use std::{env, fs::File, io::Write};

use anyhow::{bail, Context, Result};
use clap::Parser;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use base64::Engine;
use base64::engine::general_purpose::STANDARD as B64;

#[derive(Parser, Debug)]
#[command(about = "Minimal CLI to request an image from our API (no OpenAI key needed)")]
struct Args {
    /// Text prompt to generate an image
    prompt: String,

    /// Output file path for the image
    #[arg(short, long, default_value = "out.png")]
    output: String,
}

#[derive(Serialize)]
struct PromptRequest<'a> {
    prompt: &'a str,
}

#[derive(Deserialize)]
struct ApiResponse {
    /// Raw image bytes from backend
    image_base64: String,
    /// Optional metadata returned by backend
    metadata: Option<serde_json::Value>,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let api_url = env::var("API_URL")
        .context("API_URL not set (point this to your backend endpoint, e.g., https://example.com/generate)")?;

    let client = Client::new();

    let response = client
        .post(api_url)
        .json(&PromptRequest {
            prompt: &args.prompt,
        })
        .send()
        .context("Failed to call backend API")?;

    let status = response.status();
    let body = response
        .text()
        .context("Failed to read backend response body")?;

    if !status.is_success() {
        bail!("Backend returned {} with body: {}", status, body);
    }
    if body.trim().is_empty() {
        bail!("Backend returned empty body");
    }

    let resp: ApiResponse = serde_json::from_str(&body)
        .context("Failed to parse backend response")?;

    let image_bytes = B64
        .decode(&resp.image_base64)
        .context("Failed to decode image_base64 from backend")?;

    let mut file = File::create(&args.output).context("Failed to create output file")?;
    file.write_all(&image_bytes)
        .context("Failed to write image to file")?;

    println!("Saved image to {}", args.output);
    if let Some(meta) = resp.metadata {
        println!("Metadata: {meta}");
    }

    Ok(())
}

