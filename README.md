# 📷 **Frame AI – Photography Coach**

**Frame AI** is an AI-powered photography analysis and coaching tool that provides professional, real-time feedback on your photos. Designed with photographers—amateurs and pros alike—in mind, it delivers actionable insights through a sleek, modern web interface.

🌐 **Live Demo:** [https://frame-ai.onrender.com](https://frame-ai.onrender.com)

---

## ✨ Features

* 📸 **AI-Powered Photo Critique** – Get expert feedback on composition, lighting, and framing powered by [Gemini ](https://aistudio.google.com/welcome).
* 🔄 **Real-Time Streaming Analysis** – Watch the AI’s thought process unfold as it analyzes your photo.
* 📷 **EXIF Data Insights** – Understand how your camera settings impact the shot.
* 📋 **Structured Feedback** – Organized sections for strengths, improvements, and tips with expandable analysis cards.
* 🌐 **Responsive Interface** – Works on desktop and mobile with drag-and-drop uploads.
* 🌙 **Dark/Light Mode** – Automatically adapts to your system preferences or manually toggle.
* 📋 **Shareable Results** – Copy and share feedback with ease.
* 🚀 **FastAPI Backend** – Built for speed with streaming support and auto-generated API docs.

---

## 🚀 Quick Start

### ✅ Prerequisites

* Python 3.11 or later
* An [Gemini API key](https://aistudio.google.com/welcome) for AI analysis

---

### 📂 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/BKG123/frame-ai.git
   cd frame-ai
   ```

2. **Install dependencies with uv:**

   ```bash
   uv sync
   ```

   > If you don’t have `uv`, install it:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

---

### ▶ Running the Application

Start the server with hot reloading:

```bash
uv run uvicorn main:app --reload
```

Or run it directly:

```bash
uv run python main.py
```

Access it at:

* **Web Interface:** `http://localhost:8000`
* **API Docs:** `http://localhost:8000/docs`
* **Health Check:** `http://localhost:8000/health`

---

## 📦 API Endpoints

### 📸 Photo Analysis

* `POST /upload` – Upload your photo and receive real-time analysis.

### ✅ Utility

* `GET /health` – Check if the service is running.
* `GET /` – Access the web interface.

---

## 🛠 Development

### Code Quality

Maintain standards using:

```bash
# Lint with ruff
uv run ruff check .

# Type check with mypy
uv run mypy .

# Install pre-commit hooks
uv run pre-commit install
```

### 📂 Project Structure

```
frame-ai/
├── config/            # Configuration files and logging
│   ├── __init__.py
│   └── logger.py
├── services/          # Core logic
│   ├── analysis.py    # Photo critique and streaming
│   ├── llm.py         # AI integration
│   └── tools.py       # Image processing utilities
├── static/
│   └── index.html    # Responsive web UI
├── main.py           # FastAPI app definition
├── prompts.py        # AI prompt templates
└── pyproject.toml    # Project dependencies with uv
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a new branch:

   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Implement your changes
4. Run tests:

   ```bash
   uv run ruff check . && uv run mypy .
   ```
5. Commit and push:

   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```
6. Open a Pull Request!

---

## 📄 License

This project is open source. See the `LICENSE` file for details.

---

## 🙏 Acknowledgments

* Built with [FastAPI](https://fastapi.tiangolo.com/)
* AI analysis powered by [Gemini](https://gemini.google.com/app)
* Image processing using [Pillow](https://python-pillow.org/)
