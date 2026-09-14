---
name: api-ace-step-pinokio
description: Generate or cover music through the public Gradio API exposed by ACE-Step 1.5.
---

# ACE-Step 1.5 API

## Clients

Use `clients/generate_cover.py` for a melody-preserving vocal cover. Supply the runtime base URL, source audio, UTF-8 lyrics file, output directory, caption, duration, BPM, key, and cover strength.
When the service is online but model components are not loaded, also pass `--initialize` and the checkpoint path reported by the runtime API.

## Operations

The client calls the public `/generation_wrapper` Gradio endpoint and copies the first generated audio sample into the requested output directory.
It first calls `/_handle_mode_change` in the same API session; use `--mode Remix` for source-audio melody retention.

## Runtime Inputs

- Source audio is sent through the Source Audio field.
- Cover Strength controls melody retention; values around 0.73 to 0.80 are suitable when lyrics otherwise pull the melody away.
- Lyrics should be shortened to the requested test duration rather than squeezing a full song into a short preview.

## Outputs

The client prints a JSON object containing the copied output path and generation details.

## Notes

The operation requires `gradio_client`. Resolve and launch the app through Pinokio before calling the client.
