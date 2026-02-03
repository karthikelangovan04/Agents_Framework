# Model Optimization Guide

## ✅ Current Configuration (Optimized for Your Rate Limits)

**Active Model:** `gemini-2.5-flash`

### Your Available Rate Limits (from Google Cloud Console)

| Model | RPM Limit | TPM Limit | RPD Limit | Status |
|-------|-----------|-----------|-----------|--------|
| **Gemini 2.5 Flash** | 1,000 | 1M | 10K | ⭐ **Best Choice** |
| Gemini 2.0 Flash | 2,000 | 4M | Unlimited | Excellent |
| Gemini 2 Flash Exp | 10 | 250K | 500 | ⚠️ Too low |

**RPM** = Requests Per Minute  
**TPM** = Tokens Per Minute  
**RPD** = Requests Per Day

## Why Gemini 2.5 Flash?

✅ **High rate limits** - 1,000 requests per minute  
✅ **Newest model** - Latest features and improvements  
✅ **Fast responses** - Flash models are optimized for speed  
✅ **Good quality** - Excellent for chat applications  
✅ **Large token limit** - 1M tokens per minute  

## Model Comparison

| Model | Speed | Quality | Your RPM Limit | Best For |
|-------|-------|---------|----------------|----------|
| **gemini-2.5-flash** ⭐ | ⚡⚡⚡ | ⭐⭐⭐⭐ | 1,000 | **Current** - Best balance |
| gemini-2.0-flash | ⚡⚡⚡ | ⭐⭐⭐⭐ | 2,000 | High traffic apps |
| gemini-1.5-pro | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~60 | Complex reasoning |
| gemini-1.5-flash | ⚡⚡⚡ | ⭐⭐⭐ | ~15 | Quick responses |

## When to Change Models

### Switch to `gemini-2.0-flash` if:
- You expect very high traffic (>1K requests/min)
- You need maximum throughput
- Speed is more important than latest features

```bash
./change-model.sh
# Select option 2
```

### Switch to `gemini-1.5-pro` if:
- You need the highest quality responses
- Complex reasoning is required
- Traffic is low to moderate (<60 requests/min)

```bash
./change-model.sh
# Select option 3
```

## Monitoring Your Usage

Check your current usage at:
https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

Current usage (from your dashboard):
- Gemini 2.5 Flash: 7 / 1,000 RPM (0.7% used)
- Gemini 2.0 Flash: 8 / 2,000 RPM (0.4% used)

You have plenty of headroom! 🎉

## Cost Comparison (Approximate)

| Model | Input Cost | Output Cost | Total Cost* |
|-------|------------|-------------|-------------|
| gemini-2.5-flash | $0.0375/1M | $0.15/1M | ~$4.50/day |
| gemini-2.0-flash | $0.0750/1M | $0.30/1M | ~$9.00/day |
| gemini-1.5-pro | $1.25/1M | $5.00/1M | ~$150/day |

*Based on typical chat app usage (1K requests/day, avg 500 tokens each)

## Quick Commands

### Check current model:
```bash
grep GEMINI_MODEL backend/.env
```

### Change model interactively:
```bash
./change-model.sh
```

### Manually set model:
```bash
# Edit backend/.env
GEMINI_MODEL=gemini-2.5-flash  # Current (recommended)
# or
GEMINI_MODEL=gemini-2.0-flash  # For higher throughput
```

### Restart backend after changing:
```bash
lsof -ti:8000 | xargs kill -9
.venv/bin/python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

## Advanced: Using Other AI Providers

If you want to use OpenAI, Anthropic, or other providers:

1. Install extensions:
```bash
uv pip install google-adk[extensions]
# or
pip install litellm>=1.75.5
```

2. Set model in `.env`:
```bash
GEMINI_MODEL=openai/gpt-4o        # OpenAI
GEMINI_MODEL=anthropic/claude-3-5  # Anthropic
GEMINI_MODEL=groq/llama-3-70b      # Groq
```

3. Add API keys:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

See full provider list: https://docs.litellm.ai/docs/providers

## Troubleshooting

### Error: "Resource exhausted" (429)
- You've hit rate limits
- Switch to a model with higher limits
- Check usage at console.cloud.google.com

### Error: "Model not found" (404)
- Model name is incorrect
- Remove `models/` prefix (use `gemini-2.5-flash`, not `models/gemini-2.5-flash`)
- Check available models: `./change-model.sh`

### Slow responses
- Current model (gemini-2.5-flash) is optimized for speed
- If still slow, it might be network/database latency
- Check backend logs for timing

---

**Current Status:** ✅ Optimized for your rate limits with `gemini-2.5-flash`

**Last Updated:** February 3, 2026
