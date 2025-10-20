---
layout: post
title: "Frame AI: Building an AI-Powered Photography Assistant"
date: 2025-10-20
description: "How I built an AI system that analyzes and enhances photos while teaching me."
author: "Bejay"
acknowledgment: "Built with curiosity, debugged with patience, polished with <span style='color: #3182ce; font-weight: 500;'>Claude</span>."
---

## Introduction: The Mobile Photography Itch

Every developer will tell you this: "I want to work on a side project to improve my portfolio." But almost all of them will also admit they never got around to building it. I wanted to break that loop, so I started hunting for ideas. I've always been fascinated by photography. Never professional-level good, but I can click half-decent pics on my iPhone. One of my friends introduced me to amateur photography principles — rule of thirds, leading lines, proper lighting. I try to keep those in mind while taking snaps. More often than not, I fail, lol. That's when the idea hit me: What if I could analyze images using vision LLMs (like Gemini 2.5 Flash) by prompting them correctly to check alignment with widely accepted photography rules? As I was iterating on the project, Google launched Gemini 2.5 Flash Image (nicknamed "nano-banana" by the developer community) in August 2025 — a breakthrough in image generation and editing that hit #1 on LMArena's leaderboards. I thought, why not edit the images based on the analysis? So yeah, in short: Frame AI analyzes images and critiques them, and you can enhance images using Gemini 2.5 Flash Image.

**Why build Frame AI as a side project:**
- Bridge the gap between taking photos and knowing how to improve them
- Explore the AI + photography intersection
- Build a real learning playground for system design

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/app-1.png" alt="Sample app image">
  <figcaption>Frame AI Home</figcaption>
</figure>

---

## What Frame AI Actually Does

**The core idea**: An AI assistant that understands photography principles.

Not just "make it prettier" - actual compositional feedback. There are fixed rules in photography: rule of thirds, leading lines, lighting, balance, and so on. Frame AI analyzes against these principles and suggests improvements.

**Two main features:**

1. **Analysis**: What's working, what's not, and why
2. **Enhancement**: AI-powered edits based on best practices

**The interesting twist**: Instructions generated separately -> So basically I make a separate call to the LLM to generate 3 distinct editing prompts from the analysis, each focusing on different aspects: technical perfection, atmospheric reinterpretation, and conceptual narrative. It also has access to the best practices of Gemini 2.5 Flash Image prompting techniques.

Earlier I was passing the analysis directly to the image generation prompt but the output wasn't that good. My intuition was that Gemini 2.5 Flash Image excels at generating or editing images when given clear, specific instructions. We shouldn't depend on it to reason and then generate — separation of concerns works better.

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/quick-analysis.png" alt="Sample analysis output">
  <figcaption>Digestible, bullet-pointed feedback that actually helps</figcaption>
</figure>

---

## System Design: How It All Fits Together

**High-level architecture:**

User uploads image → FastAPI backend → Image processing & caching layer → LLM analysis → Stored in DB → Enhance Image Trigger → 3 editing prompts generated from analysis → 3 images generated in parallel using Gemini 2.5 Flash Image

**Key components:**

- **Database**: SQLite (content-based hash indexing for deduplication)
- **LLM Integration**: Gemini 2.5 Flash for analysis, Gemini 2.5 Flash Lite for JSON structuring, Gemini 2.5 Flash Image for enhancement
- **Caching Strategy**: Content-based hashing prevents duplicate processing (performance + cost optimization)
- **API Design**: RESTful endpoints with Server-Sent Events for streaming analysis

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/system-design.png" alt="System architecture diagram" data-lightbox="image">
  <figcaption>Clean architectural overview of Frame AI</figcaption>
</figure>

As mentioned earlier, the product has two main parts: image analysis and image enhancement.

**Image Analysis Flow:**
1. Frontend calls `/upload` API with image file
2. Backend workflow:
   - Content-based hash is generated from file bytes (fixes duplicate detection edge cases)
   - Image stored permanently in `static/uploaded_images/{hash}.{ext}` (deduplication happens here)
   - Check SQLite cache — if hash exists, stream cached analysis immediately
   - For new images:
     - Temporary file created for processing
     - Gemini 2.5 Flash call with image + photography best practices prompt
     - LLM streams detailed analysis with scores (exposure, composition, lighting, overall)
     - Analysis stored in SQLite against file hash
     - Frontend receives analysis via Server-Sent Events (real-time streaming)
   - EXIF data extracted and stored for context

**Image Enhancement Flow:**
1. Frontend calls `/image/edit` API with file hash
2. Backend workflow:
   - Fetch cached analysis from SQLite using hash
   - Generate 3 distinct editing prompts via Gemini 2.5 Flash (with Gemini 2.5 Flash Image best practices as context)
     - Prompt 1: Technical perfection & enhancement
     - Prompt 2: Atmospheric & mood reinterpretation
     - Prompt 3: Conceptual & narrative composite
   - Launch 3 parallel Gemini 2.5 Flash Image API calls (`asyncio.gather`)
   - Each call returns: enhanced image + text description of changes
   - Text descriptions converted to structured JSON via Gemini 2.5 Flash Lite (temperature = 0 for consistency)
   - Return 3 enhanced images with metadata to frontend

---

## Design Decisions & Lessons Learned

### Decision 1: Content-Based Hashing for Caching

**Why it's critical:**
- Analysis needs to be reused for enhancement (same image = same analysis)
- Duplicate uploads waste API calls and cost money
- User experience: instant results for previously analyzed images

**Evolution of approach:**
- **First attempt**: Filename + IP-based caching
  - Problem: Same filename, different image = cache collision
  - Problem: Storing IP addresses = PII concerns
- **Final solution**: Content-based hashing (SHA-256 of file bytes)
  - Same image content → same hash → reliable cache hit
  - Different images → different hashes → no false positives
  - Privacy-friendly: no PII stored

**Impact**: ~40% cache hit rate in production (multiple users upload popular stock photos for testing)

### Decision 2: Three Parallel Image Variations

**Why not just one enhanced image?**
- Photography enhancement is highly subjective
- Analysis covers multiple dimensions (technical, artistic, mood)
- Users prefer choice — what looks "better" varies by taste and use case
- Three variations let users see different creative directions

**The three approaches:**
1. **Technical perfection**: Fix exposure, sharpen details, recover dynamic range
2. **Atmospheric reinterpretation**: Transform mood through color grading and lighting
3. **Conceptual narrative**: Reimagine the story (subtle compositing, creative edits)

**Hyperparameter tuning:**
- **Analysis LLM** (Gemini 2.5 Flash): temperature = 0.3-0.5 (balance creativity with structure)
- **JSON structuring** (Gemini 2.5 Flash Lite): temperature = 0 (deterministic output)
- **Prompt generation** (Gemini 2.5 Flash): temperature = 0.5 (creative but focused)

**Performance**: Using `asyncio.gather()` for parallel generation reduces total wait time from ~45s to ~15s

### Decision 3: Separate LLM Call for Prompt Generation

**Initial approach**: Passing analysis directly to Gemini 2.5 Flash Image
- Problem: Output quality was inconsistent
- Image model struggled to extract actionable edits from verbose analysis

**Final solution**: Dedicated prompt generation step
- Generate 3 specific editing prompts via Gemini 2.5 Flash
- Include [Gemini 2.5 Flash Image best practices](https://ai.google.dev/gemini-api/docs/image-generation#best-practices){:target="_blank" rel="noopener noreferrer"} as context
- Pass clean, focused instructions to image model

**Why it works**: Gemini 2.5 Flash Image excels at following clear, step-by-step instructions — but we shouldn't ask it to reason about photography theory *and* generate images. Separation of concerns wins again.

**Results**: More precise, actionable edits. The enhancements became subtle but comprehensible instead of over-processed.

### Decision 4: Design Constraints & Negative Prompting

**What I explicitly told the models NOT to do:**
- Don't add objects/people that weren't in the original (authenticity matters for photography)
- Don't rotate or change orientation (preserve photographer's intent)
- Don't over-process to the point of looking fake

**UX decisions:**
- Keep feedback digestible — no one reads walls of text
- Focus on enhancement, not transformation
- Make AI feedback feel specific, not generic

### Trade-offs: Cost vs. Quality

**Current approach**: Optimize for quality first
- Making multiple LLM calls per request (analysis + prompt generation + JSON structuring)
- Not worrying about cost during initial development
- Philosophy: Get best results, then optimize

**Future optimizations:**
- Replace JSON-generating LLM calls with markdown parsers
- Use Python imaging libraries (Pillow) for simple adjustments instead of image generation
- Fine-tune an open-source model for analysis
- Batch processing for multiple images

### The Metric Saga

**What happened**: Added metrics tracking. Then removed it.

**Why?**
- Had tried to give some quantitative insights using LLMs to calculate metrics like sharpness, color composition
- Problem: The generated image is completely new, not a modified version of the original
- Metrics might show "improvement" but they're comparing apples to oranges

**What I learned**: For AI-generated image enhancements, subjective visual comparison beats objective metrics. The user's eye is the best judge.

<div class="image-grid">
  <figure>
    <img src="/assets/images/2025-10-20-frame-ai/og_image.png" alt="Original photo">
    <figcaption>Original</figcaption>
  </figure>

  <figure>
    <img src="/assets/images/2025-10-20-frame-ai/var1.png" alt="Enhanced variation 1">
    <figcaption>Variation 1</figcaption>
  </figure>

  <figure>
    <img src="/assets/images/2025-10-20-frame-ai/var2.png" alt="Enhanced variation 2">
    <figcaption>Variation 2</figcaption>
  </figure>

  <figure>
    <img src="/assets/images/2025-10-20-frame-ai/var3.png" alt="Enhanced variation 3">
    <figcaption>Variation 3</figcaption>
  </figure>
</div>

---

## Technical Challenges & Solutions

### Challenge 1: MIME Type Detection for Various Image Formats

**Problem**: Different browsers and clients send images with different MIME types. Some don't include proper Content-Type headers.

**Solution**:
- Implemented a helper function `get_file_mime_type()` that detects MIME type from:
  1. File extension (`.jpg`, `.png`, `.heic`, etc.)
  2. HTTP headers when fetching remote images
  3. Fallback to `image/jpeg` for unknown types
- Used Python's `mimetypes` library for reliable extension-to-MIME mapping

### Challenge 2: Handling Large Images & EXIF Orientation

**Problem**:
- Large images (>10MB) were slow to process
- iPhone photos often had incorrect orientation due to EXIF rotation metadata

**Solution**:
- Used Pillow's `ImageOps.exif_transpose()` to auto-correct orientation before processing
- Temporary files created with proper cleanup using context managers
- Server-Sent Events for streaming analysis so users see progress immediately

**Code snippet** ([utils/helpers.py:1-20](utils/helpers.py#L1-L20)):
```python
def get_file_mime_type(file_path: str) -> str:
    """Detect MIME type from file extension or headers"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    # Fallback for common extensions
    if file_path.endswith('.heic'):
        return 'image/heic'
    return 'image/jpeg'
```

### Challenge 3: Balancing LLM Call Costs with Quality

**Problem**: Each image analysis + enhancement requires 6+ LLM calls. Costs add up quickly.

**Solution**:
- Implemented aggressive caching with content-based hashing (40% hit rate)
- Used cheaper models where possible (Gemini 2.5 Flash Lite for JSON structuring)
- Set temperature = 0 for deterministic tasks to avoid retries
- Future: Will implement batch processing and consolidate LLM calls

**Cost breakdown** (per image):
- Analysis: ~$0.01 (Gemini 2.5 Flash with vision)
- Prompt generation: ~$0.002 (Gemini 2.5 Flash)
- 3x Image generation: ~$0.12 ($0.039 per image)
- 3x JSON structuring: ~$0.003 (Gemini 2.5 Flash Lite)
- **Total: ~$0.135 per full analysis + enhancement**

### Challenge 4: Making AI Feedback Actually Useful (Not Generic)

**Problem**: Early versions gave generic feedback like "nice composition" or "good lighting" that didn't help users improve.

**Solution**:
- Crafted a detailed system prompt with specific photography principles (rule of thirds, leading lines, etc.)
- Included EXIF data in the prompt so the LLM could explain technical settings
- Asked for structured feedback: strengths, improvements, professional tips
- Added numerical scores (1-10) for exposure, composition, lighting, overall

**Example of specific vs. generic feedback**:
- ❌ Generic: "The lighting could be better"
- ✅ Specific: "The main light source creates harsh shadows on the subject's face. Try shooting during the 'golden hour' or using a diffuser to soften the light."

---

## What I Built vs. What I Learned

**The product**: A working AI photography assistant that analyzes and enhances photos in real-time.

**The real wins:**

After 3 years working with LLMs, this project taught me lessons you can't learn from enterprise work alone:

- **Image models are fundamentally different from text models**: Thought my LLM prompting experience would transfer directly. It didn't. Image generation models need surgical precision in instructions, not reasoning ability. Separation of concerns (reasoning LLM → instruction generation → image model) worked better than end-to-end prompting.

- **Real-world system design beats architectural purity**: Content-based hashing wasn't the "cleanest" solution, but it solved real problems (cache collisions, PII concerns). Sometimes the pragmatic choice is the right choice.

- **Caching is both UX and economics**: 40% cache hit rate doesn't just save money — it makes the product feel responsive. Users don't care about Server-Sent Events or streaming; they care that analysis feels instant on the second try.

- **Iteration beats perfection**: Shipped with basic features, then improved based on real usage. The metrics tracking feature sounded great on paper, but added zero value in practice. Removing it improved focus.

- **Users want agency, not magic**: Three variations >>> one "perfect" edit. For subjective tasks like photography, showing the AI's work (via text descriptions) builds more trust than hiding complexity.

- **Async architecture compounds gains**: `asyncio.gather()` for parallel image generation wasn't just about speed (3x faster) — it fundamentally changed the user experience from "go grab coffee" to "wait a moment."

### Personal Reflections

Building Frame AI taught me something important: **side projects are learning artifacts**. After 3 years in the LLM industry, I thought I knew this space. But there's a difference between integrating LLMs into existing products and building something from scratch. The messy middle — debugging EXIF orientation at 2am, discovering my caching strategy had edge cases, iterating on prompts 20+ times — that's where real learning happens.

Frame AI isn't perfect, and it probably never will be. But it's a snapshot of what I know *right now* about LLMs, system design, and product thinking. And that's valuable.

---

## What's Next

**Potential improvements:**
- **Batch processing**: Upload multiple photos, get bulk analysis
- **Style preferences/learning**: Remember user preferences (prefers moody edits vs. bright and airy)
- **Mobile app integration**: PWA or native iOS app for on-the-go analysis
- **Community sharing features**: Gallery of before/after examples, upvoting best enhancements
- **Cost optimization**: Consolidate LLM calls, use open-source models for some tasks

**Open questions I'm still exploring:**
- How to balance automation with creative control? (Let users tweak prompts? Provide sliders for "enhancement intensity"?)
- What makes AI feedback feel "authentic" vs. generic? (Still experimenting with prompt engineering)
- Should I add a "learn from feedback" loop where users mark helpful vs. unhelpful critiques?

---

## Conclusion: The Side Project Effect

Started wanting to improve my photos. Ended up learning system design, LLM engineering, and product iteration.

Frame AI isn't just a tool — it's a learning artifact. It represents 2 weeks of curiosity-driven exploration, late-night debugging, and iterative improvement. I learned more from building this than I would have from a dozen tutorials.

If you're a developer thinking "I should build a side project," stop thinking and start building. Pick something you're genuinely curious about, not what's trending on Twitter. Your first version will be messy. Your caching strategy will have edge cases. Your prompts will need 20 iterations. That's fine. That's the point.

The real value isn't the final product — it's the process of figuring things out.

**Try it, break it, let me know what you think**: [https://frame-ai.bejayketanguin.com/](https://frame-ai.bejayketanguin.com/){:target="_blank" rel="noopener noreferrer"}

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/hero-app.png" alt="Frame AI in action">
  <figcaption>Frame AI in action</figcaption>
</figure>
