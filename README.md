# Frame AI - Photography Coach

An AI-powered photography analysis and coaching tool that provides professional feedback on your photos.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

### Basic Analysis
```bash
python main.py analyze path/to/your/photo.jpg
```

### Analysis with Sample Edits
```bash
python main.py analyze path/to/your/photo.jpg --apply-edits
```

### Custom Output Directory
```bash
python main.py analyze path/to/your/photo.jpg --apply-edits --output-dir ./my-edits
```

## Features

- = **EXIF Data Analysis** - Extracts and analyzes technical camera settings
- <¨ **Professional Critique** - AI-powered analysis based on photography principles
- =à **Basic Editing Tools** - Applies sample brightness, saturation, and sharpening adjustments
- =Ê **Structured Feedback** - Organized strengths, improvements, and actionable tips

## Example

```bash
python main.py analyze files/ADDE0FAC-1B94-41DC-9DC0-E3306F11B730_1_102_o.jpeg --apply-edits
```

This will analyze your photo and create edited versions in the `output/` directory.
