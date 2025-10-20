---
layout: post
title: "Frame AI: Building an AI-Powered Photography Assistant"
date: 2025-10-20
description: "How I built an AI system that analyzes and enhances photos while teaching me."
author: "Bejay"
acknowledgment: "Built with curiosity, debugged with patience, polished with <span style='color: #3182ce; font-weight: 500;'>Claude</span>."
---

## Introduction: The Mobile Photography Itch

Every developer will tell you this: "I want to work on a side project to improve my portfolio." But almost all of them will also admit they never got around to building it. I wanted to break that loop, so I started hunting for ideas. I've always been fascinated by photography. Never professional-level good, but I can click half-decent pics on my iPhone. One of my friends introduced me to amateur photography principles — rule of thirds, leading lines, proper lighting. I try to keep those in mind while taking snaps. More often than not, I fail, lol. That's when the idea hit me: What if I could analyze images using vision LLMs (like gemini-2.5-flash) by prompting them correctly to check alignment with widely accepted photography rules? As I was iterating on the project, Google stealthily launched nano-banana — a revolution in closed-model image generation. I thought, why not edit the images based on the analysis? So yeah, in short: Frame AI analyzes images and critiques them, and you can enhance images using nano-banana.

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

**The interesting twist**: Instructions generated separately -> So basically I make a separate call to LLM to generate 3 prompts from the analysis, each focusing on separate parts of the feedback. It also has access to the best practices of nano banana prompting techniques.

Earlier I was passing the analysis directly to the nano banana generation prompt but the output wasn't that good. My intuition was that nano banana is good at generating or editing images given it is given clear cut instructions. We shouldn't depend on it to reason and then generate.

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/quick-analysis.png" alt="Sample analysis output">
  <figcaption>Digestible, bullet-pointed feedback that actually helps</figcaption>
</figure>

---

## System Design: How It All Fits Together

**High-level architecture:**

User uploads image → FastAPI backend → Image processing & caching layer → LLM analysis → Stored in DB -> Enhance Image Trigger → 3 prompts generated for analysis → 3 Images generated using nano-banana

**Key components:**

- **Database**: Sqlite
- **LLM Integration**: Using Gemini Flash Models ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash-image")
- **Caching Strategy**: Why images being cached matters (performance + cost)
- **API Design**: RESTful endpoints for upload, analyze, edit

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/system-design.png" alt="System architecture diagram" data-lightbox="image">
  <figcaption>Clean architectural overview of Frame AI</figcaption>
</figure>

As mentioned earlier the product has two main parts - image analysis and image enhancements.

Image Analysis:
- FE calls the upload api with image file

- In BE
  - A hash is created using the contents of the file.
  - The image file is stored in memory with the hash as the filename.
  - A temporary file is created for analysis.
  - A LLM call to gemini is made ("gemini-2.5-flash") with the image as input and best practices of photography in the prompt
  - The LLM outputs a detailed analysis along with scores.
  - This "Detailed Analysis" is parsed and shown in the frontend.
  - Another LLM call is made to output a "Quick Analysis" which is shown in a diff tab
  - Both the analyses are stored in SQLite db against the file hash and the value is returned to FE, along with the file hash

Image Enhancement
- FE calls the image enhancement API with file hash

- In BE
  - The analysis is fetched using the file hash.
  - From the analysis, 3 prompts are generated using LLM call (nano banana best practices are passed as context)
  - Using the 3 prompts, 3 parallel calls are made to nano banana api to generate 3 images and corresponding text outputs saying what changes were made
  - These text outputs are passed through 3 llm calls to structure the output into json



---

## Design Decisions & Lessons Learned

### Decision 1: Image Caching

Why it's critical:
  - Caching of analysis is mostly necessary as I wanted to reuse it for enhancement.

How I implemented it:
  - Frist tried with only filename + ip based caching but it was not that robust for same filename different image cases. Also didn't want to store PII


### Decision 2: Three Separate Generations for Analysis

Why not just one?
 - Enhancement of image is highly subjective, so it's better to have 3 different outputs instead of 1. Also the analysis focuses on multiple params and its better to have multiple outputs

Hyperparams:
  - Temperature: Kept temps closer to 0 for most structural things (jsonifaction and stuff) while mainatained 0.3-0.5 for analysis to find a balance between creativity and structure


### Decision 3: Separate Call for prompt of image generation

Initial approach: Earlier I was passing the analysis directly to the nano banana generation prompt but the output wasn't that good. So I separately made llm call to generate prompt

Why I split them:  My intuition was that nano banana is good at generating or editing images given it is given clear cut instructions. We shouldn't depend on it to reason and then generate.

Nano banana prompting technique:  For the prompt generation passed the [Nano Banana Best Practices as context](https://ai.google.dev/gemini-api/docs/image-generation#best-practices){:target="_blank" rel="noopener noreferrer"}

Results: More precise, actionable edits.
 - The edits were more subtle but comprehensible

### Decision 4: What NOT to Do. Negative prompting

- Don't add objects that weren't there (authenticity matters)
- Keep text digestible - no one reads walls of text
- Focus on enhancement, not transformation

### Trade-offs (cost vs. quality):
  - As of now, I haven't though much about cost.
  - Made as many llm calls.
  - Idea is to get best results and then optimise for cost.
  - Some ideas involve
    - Not making llm calls for json - instead use markdown parsers
    - Some changes can be made using python tools instead of image generation
    - Later: Finetune some opensource model and use it

### The Metric Saga

Added metrics tracking. Then removed it.

Why?
- Had tried to give some quantitative insights. Used LLMs to search for metrics like sharpness, color compositions.

What I learned: I learned that it made no sense as image generated is completely new. So metrics might be coming as good but would made no sense.

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

**Challenge 1**: MIME type detection for various image formats
[Your solution]

**Challenge 2**: Handling large images efficiently
[Your solution]

**Challenge 3**: Balancing LLM call costs with quality
[Your solution]

**Challenge 4**: Making AI feedback actually useful (not generic)
[Your solution]

[Optional: Include code snippet or flowchart]

---

## What I Built vs. What I Learned

**The product**: A working AI photography assistant.

**The real wins:**
- Understanding LLM prompting nuances in terms of image generation
- Caching strategies that actually matter
- Iteration over perfection
- Knowing when to remove features

[Your personal reflections]

---

## What's Next

Potential improvements:
- Batch processing
- Style preferences/learning
- Mobile app integration
- Community sharing features

Open questions:
- How to balance automation with creative control?
- What makes AI feedback feel "authentic" vs. generic?

---

## Conclusion: The Side Project Effect

Started wanting to improve my photos. Ended up learning system design, LLM engineering, and product iteration.

Frame AI isn't just a tool - it's a learning artifact.

[Your closing thoughts]

**Try it, break it, let me know what you think**: [https://frame-ai.bejayketanguin.com/](https://frame-ai.bejayketanguin.com/){:target="_blank" rel="noopener noreferrer"}

<figure>
  <img src="/assets/images/2025-10-20-frame-ai/hero-app.png" alt="Frame AI in action">
  <figcaption>Frame AI in action</figcaption>
</figure>
