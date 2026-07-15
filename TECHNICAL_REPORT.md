# Technical Report

## Model and Runtime

- **Model**: Microsoft Phi-3-mini (`phi3:mini` on Ollama)
- **Parameters**: ~3.8B
- **Runtime**: Ollama (local LLM serving), CPU inference
- **Serving endpoint**: `http://localhost:11434` (loopback only, no external network access)

## Quantization / Optimization

- Uses Ollama's default distribution of `phi3:mini`, which ships pre-quantized (4-bit, GGUF
  format) for efficient CPU inference — no additional quantization was performed by this
  project; the default Ollama model pull was used as-is.
- Generation-side optimization: temperature set to 0.2 (reduces sampling randomness, improves
  consistency) and `num_predict` capped at 150 tokens to bound response length and latency.

## Model Size

- ~2.2 GB on disk (per `ollama list` output).

## Inference Latency

- First call after model load (cold start): approximately 30-90 seconds, since Ollama loads the
  full model into memory from disk on first use.
- Subsequent calls (model already resident in memory): approximately [FILL IN — time one CLI
  run with a stopwatch, e.g. "8-15 seconds per explanation"].

## CPU / GPU / NPU Usage

- CPU-only inference; no GPU or NPU acceleration was used or required.
- Anomaly detection (Isolation Forest) also runs on CPU and completes in well under a second
  for the sample dataset sizes used (8-15 rows per skill pack).

## Peak Memory Usage

- Approximately 3-4 GB RAM while `phi3:mini` is loaded in Ollama (typical for a ~2.2GB
  quantized model plus inference overhead). Exact peak was not profiled with a memory tool in
  this project's timeframe; this is an estimate based on the model's disk size.

## Tested Device Specifications

- OS: Windows [FILL IN — e.g. "11"], PowerShell terminal
- CPU: [FILL IN — from Settings > System > About, e.g. "Intel Core i5-1135G7"]
- RAM: [FILL IN — e.g. "8 GB" or "16 GB"]
- No dedicated GPU was used; inference ran entirely on CPU.

## Additional Technical Details

- The anomaly-detection component (`core/anomaly_engine.py`) uses scikit-learn's
  `IsolationForest` with a per-skill-configurable `contamination` parameter (0.1-0.2 across the
  four skill packs), and only operates on numeric columns extracted per domain — non-numeric
  columns (timestamps, merchant names, topic names) are preserved for context but excluded from
  the model itself.
- The system was validated to correctly fall back to a clearly-labeled stub response if Ollama
  is not reachable (e.g. not yet installed, not running, or a proxy misconfiguration blocking
  `localhost` — an issue encountered and fixed during development on Windows, documented in
  `core/llm_client.py`'s use of `proxies={"http": None, "https": None}`).s
