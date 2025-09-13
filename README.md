# Frame AI - Photography Coach

An AI-powered photography analysis and coaching tool that provides professional feedback on your photos through a modern web interface.

## Features

- 📸 **Professional Photo Analysis** - AI-powered critique based on photography principles
- 🎯 **EXIF Data Analysis** - Extracts and analyzes technical camera settings
- 🎨 **Basic Photo Editing** - Applies sample brightness, saturation, and sharpening adjustments
- 📋 **Structured Feedback** - Organized strengths, improvements, and actionable tips
- 🌐 **Web Interface** - Easy-to-use browser-based interface
- 🚀 **FastAPI Backend** - Modern, high-performance API with automatic documentation

## Quick Start

### Prerequisites

- Python 3.11 or higher
- An Anthropic API key (for AI analysis)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd frame-ai
```

2. Install dependencies with uv:
```bash
uv sync
```

> **Note**: This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python package management. If you don't have uv installed, install it with:
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the Application

Start the web server:
```bash
uv run uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

- **Web Interface**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## API Endpoints

### Photo Analysis
- `POST /analyze` - Analyze a photo from URL
- `POST /upload-analyze` - Upload and analyze a photo file

### Photo Editing
- `POST /edit` - Apply basic edits to a photo from URL
- `POST /upload-edit` - Upload a photo and apply basic edits

### Utility
- `GET /health` - Health check endpoint
- `GET /` - Web interface

## Development

### Code Quality

This project uses several tools to maintain code quality:

```bash
# Linting with ruff
uv run ruff check .

# Type checking with mypy
uv run mypy .

# Pre-commit hooks (automatically run on commit)
uv run pre-commit install
```

### Project Structure

```
frame-ai/
├── config/          # Configuration and logging
├── services/        # Core business logic
│   ├── analysis.py  # Photo analysis service
│   ├── llm.py      # AI/LLM integration
│   └── tools.py    # Image processing utilities
├── static/         # Web interface assets
├── main.py         # FastAPI application entry point
├── prompts.py      # AI prompt templates
└── pyproject.toml  # Project configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`uv run ruff check . && uv run mypy .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is open source. Please see the LICENSE file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI analysis powered by [Anthropic Claude](https://www.anthropic.com/)
- Image processing with [Pillow](https://python-pillow.org/)
