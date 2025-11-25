# AI Providers Reference Guide

Complete documentation of all 4 AI providers integrated into GAMELOCK AI.

---

## 🔑 API Keys Location

All keys stored in: `dashboard/.streamlit/secrets.toml`

```toml
GOOGLE_API_KEY = "..."
ANTHROPIC_API_KEY = "..."
OPENAI_API_KEY = "..."
XAI_API_KEY = "..."
```

---

## 1. xAI Grok

**Console**: https://console.x.ai  
**Docs**: https://docs.x.ai

### Models
| Model | Context | Best For |
|-------|---------|----------|
| `grok-4-1-fast-reasoning` | 2,000,000 | Complex reasoning, largest context |
| `grok-4-fast-reasoning` | 2,000,000 | Fast reasoning |
| `grok-3-mini` | 131,072 | Fast, cheap |
| `grok-3` | 131,072 | General purpose |

### Built-in Agentic Tools (Server-Side)
| Tool | Description |
|------|-------------|
| `x_user_search` | Search X/Twitter users |
| `x_keyword_search` | Search X/Twitter posts by keyword |
| `web_search` | General web search |
| `browse_page` | Read webpage content |

### Image Generation
```python
POST https://api.x.ai/v1/images/generations
{
  "prompt": "...",
  "n": 1,  # 1-10
  "response_format": "url"  # or "b64_json"
}
```

### Usage (OpenAI Compatible)
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)
response = client.chat.completions.create(
    model="grok-3-mini",
    messages=[{"role": "user", "content": "..."}]
)
```

### Unique Features
- **X/Twitter Native Search** - Only AI with direct X integration
- **2M Context Window** - Largest available
- **Real-time X Data** - Live tweets, trends, user info

---

## 2. OpenAI GPT

**Console**: https://platform.openai.com  
**Docs**: https://platform.openai.com/docs

### Models
| Model | Context | Best For |
|-------|---------|----------|
| `gpt-4o` | 128,000 | Most capable, multimodal |
| `gpt-4o-mini` | 128,000 | Fast, cheap, great quality |
| `gpt-4-turbo` | 128,000 | Legacy, still good |
| `o1` | 200,000 | Deep reasoning |
| `o1-mini` | 128,000 | Fast reasoning |

### Responses API (NEW - Better than Chat Completions)
```python
response = client.responses.create(
    model="gpt-4o-mini",
    input="...",
    tools=[{"type": "web_search"}],  # Built-in tools!
    store=True,  # Enable context caching
    previous_response_id="..."  # Multi-turn
)
```

### Built-in Tools (Responses API)
| Tool | Description |
|------|-------------|
| `web_search` | Real-time web search |
| `file_search` | Search uploaded documents |
| `code_interpreter` | Execute Python code |
| `image_generation` | Generate images inline |
| `computer_use` | Control computer (beta) |

### Image Generation (DALL-E)
```python
response = client.images.generate(
    model="dall-e-3",
    prompt="...",
    size="1024x1024",
    quality="hd"
)
```

### Unique Features
- **Best Overall Quality** - Industry standard
- **DALL-E 3** - Best image generation
- **Whisper** - Best speech-to-text
- **TTS** - Text-to-speech

---

## 3. Anthropic Claude

**Console**: https://console.anthropic.com  
**Docs**: https://docs.anthropic.com

### Models
| Model | Context | Best For |
|-------|---------|----------|
| `claude-opus-4-0520` | 200,000 | Most intelligent, coding, agents |
| `claude-sonnet-4-5` | 200,000 | Balanced (recommended default) |
| `claude-3-haiku-20240307` | 200,000 | Fastest, cheapest |

### Built-in Tools
| Tool | Description |
|------|-------------|
| `bash_tool` | Run shell commands |
| `code_execution_tool` | Execute code |
| `computer_use_tool` | Screenshot, mouse, keyboard (beta) |
| `text_editor_tool` | Edit text files |
| `web_fetch_tool` | Fetch URL content |
| `web_search_tool` | Web search |
| `memory_tool` | Persistent memory |
| `tool_search_tool` | Search available tools |

### Usage
```python
import anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
)
```

### Unique Features
- **Best Reasoning** - Most thoughtful analysis
- **Computer Use** - Can control desktop (beta)
- **200K Context** - Very large window
- **Prompt Caching** - Save money on repeated prompts

---

## 4. Google Gemini

**Console**: https://aistudio.google.com  
**Docs**: https://ai.google.dev

### Models
| Model | Context | Best For |
|-------|---------|----------|
| `gemini-3-pro` | 1,000,000+ | Newest, most intelligent |
| `gemini-2.5-pro` | 1,000,000 | Very capable |
| `gemini-2.5-flash` | 1,000,000 | Fast, cheap |
| `gemini-2.5-flash-lite` | 1,000,000 | Fastest, cheapest |
| `gemini-pro` | 32,000 | Legacy, still works |

### Additional APIs
| API | Description |
|-----|-------------|
| **Imagen** | Image generation |
| **Veo** | Video generation |
| **Lyria** | Music generation |
| **Embeddings** | Vector embeddings |

### Usage
```python
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("...")
```

### Unique Features
- **1M+ Context** - Largest context window
- **Video Generation (Veo)** - Generate videos from text
- **Music Generation (Lyria)** - Generate music
- **Free Tier** - Generous free usage
- **Multimodal** - Text, image, video, audio input

---

## Quick Comparison

| Feature | Grok | GPT | Claude | Gemini |
|---------|------|-----|--------|--------|
| Max Context | 2M | 200K | 200K | 1M+ |
| X/Twitter Search | ✅ | ❌ | ❌ | ❌ |
| Web Search | ✅ | ✅ | ✅ | ✅ |
| Image Gen | ✅ | ✅ (DALL-E) | ❌ | ✅ (Imagen) |
| Video Gen | ❌ | ❌ | ❌ | ✅ (Veo) |
| Code Exec | ❌ | ✅ | ✅ | ✅ |
| Computer Use | ❌ | ✅ | ✅ | ❌ |
| Free Tier | ❌ | ❌ | ❌ | ✅ |

---

## Recommended Usage

| Task | Best Provider |
|------|---------------|
| X/Twitter Intel | **Grok** |
| Quick Analysis | **GPT** or **Grok** |
| Deep Reasoning | **Claude** |
| Free Usage | **Gemini** |
| Image Generation | **GPT (DALL-E)** |
| Video Generation | **Gemini (Veo)** |
| Largest Context | **Grok** (2M) |

---

## Rate Limits (Approximate)

| Provider | Requests/min | Tokens/min |
|----------|-------------|------------|
| Grok | 60 | 100K |
| GPT | 60-500 | 90K-150K |
| Claude | 50 | 100K |
| Gemini | 60 | 1M (free) |

---

*Last Updated: November 2025*

