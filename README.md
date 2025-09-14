# Frame AI - Photography Coach

An AI-powered photography analysis and coaching tool that provides professional feedback on your photos through a modern, responsive web interface with real-time streaming analysis.

## Features

- 📸 **Professional Photo Analysis** - AI-powered critique based on photography principles using Anthropic Claude
- 🔄 **Real-Time Streaming** - Watch your analysis unfold in real-time with streaming responses
- 🎯 **EXIF Data Analysis** - Extracts and analyzes technical camera settings
- 📋 **Structured Analysis Cards** - Organized sections for strengths, improvements, and actionable tips with collapsible interface
- 🌐 **Modern Web Interface** - Responsive, accessible design with drag-and-drop photo upload
- 🌙 **Dark/Light Theme** - Toggle between themes with automatic system preference detection
- 📋 **Copy & Share** - Easy sharing of analysis results with clipboard integration
- 🚀 **FastAPI Backend** - High-performance API with streaming support and automatic documentation

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
```

### Running the Application

Start the web server with hot reloading:
```bash
uv run uvicorn main:app --reload
```

Or run directly:
```bash
uv run python main.py
```

The application will be available at `http://localhost:8000`

- **Web Interface**: `http://localhost:8000` - Modern drag-and-drop photo analysis interface
- **API Documentation**: `http://localhost:8000/docs` - Interactive FastAPI documentation
- **Health Check**: `http://localhost:8000/health` - Service health status

## API Endpoints

### Photo Analysis
- `POST /upload` - Upload and analyze a photo with streaming response

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
│   ├── __init__.py
│   └── logger.py    # Logging configuration
├── services/        # Core business logic
│   ├── analysis.py  # Photo analysis service with streaming
│   ├── llm.py      # AI/LLM integration (Anthropic Claude)
│   └── tools.py    # Image processing utilities
├── static/
│   └── index.html  # Modern responsive web interface with streaming UI
├── main.py         # FastAPI application with streaming endpoints
├── prompts.py      # AI prompt templates for photography analysis
└── pyproject.toml  # Project configuration with uv dependencies
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
