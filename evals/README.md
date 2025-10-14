# Frame AI Evaluation Suite

Automated testing framework for validating Frame AI photo analysis quality.

## Quick Start

```bash
# Run all tests
pytest evals/tests/ -v

# Run specific test
pytest evals/tests/test_analysis.py::TestPhotoAnalysis::test_produces_valid_json -v

# With report generation
python -m evals.scripts.run_evals
```

## Structure

```
evals/
├── README.md                # This file
├── config.py                # Configuration and constants
├── conftest.py              # Pytest fixtures
├── tests/
│   ├── __init__.py
│   └── test_analysis.py     # Main test suite (13 tests)
├── fixtures/
│   ├── images/              # Test images (add your photos here)
│   └── expected/            # Expected outputs (future use)
├── utils/
│   ├── __init__.py
│   └── validation.py        # Validation helper functions
├── scripts/
│   └── run_evals.py         # CLI test runner with reports
└── results/                 # Auto-generated test reports
```

## Test Coverage

### 13 Comprehensive Tests

**JSON Structure (4 tests)**
- Valid JSON format
- Required fields present
- Correct nested structure
- Proper data types

**Content Quality (4 tests)**
- Appropriate text lengths
- No placeholder text
- All sections unique
- Quality standards met

**Content Depth (5 tests)**
- Meaningful impression (not generic)
- Technical feedback depth
- Artistic feedback depth
- Actionable next steps
- Image-specific analysis

## Adding Test Images

```bash
# Add test images to fixtures/images/
cp ~/photos/*.{jpg,png} evals/fixtures/images/

# Supported formats: JPG, JPEG, PNG
```

**Recommended test images:**
- Good composition (baseline quality)
- Poor lighting (detection test)
- Composition issues (feedback test)
- Technical problems (advice test)
- Various subjects (portraits, landscapes, etc.)

## Configuration

Edit `config.py` to adjust thresholds:

```python
MAX_RESPONSE_TIME_SECONDS = 30
MIN_OVERALL_IMPRESSION_LENGTH = 10
MAX_OVERALL_IMPRESSION_LENGTH = 500
MIN_BULLET_POINT_LENGTH = 5
```

## Running Tests

### Development Workflow

```bash
# Quick check during coding
pytest evals/tests/ -v

# Stop on first failure
pytest evals/tests/ -x

# Run specific test class
pytest evals/tests/test_analysis.py::TestPhotoAnalysis -v

# With detailed output
pytest evals/tests/ -vv -s
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run Evaluations
  run: pytest evals/tests/ -v
```

## Performance

- **Runtime:** ~25-30s per test (runs real photo analysis)
- **Cost:** Minimal (uses Gemini API for analysis)
- **Optimization:** Tests reuse analysis when possible

## Test Results

All tests validate real photo analysis output:

| Category | Tests | What It Checks |
|----------|-------|----------------|
| Structure | 4 | JSON format, schema compliance |
| Quality | 4 | Content standards, uniqueness |
| Depth | 5 | Specificity, actionable feedback |

## Extending Tests

Add new tests to `tests/test_analysis.py`:

```python
async def test_my_new_check(self, analysis_data: dict):
    """Test description."""
    # Your test logic
    assert condition, "Error message"
```

## Troubleshooting

**No test images found**
- Add images to `evals/fixtures/images/`
- Tests will skip if no images available

**Import errors**
- Run from project root: `cd /path/to/frame-ai`
- Ensure dependencies installed: `uv sync`

**Tests take too long**
- Expected: ~25-30s per test (real LLM analysis)
- Use `-k` flag to run specific tests

## Future Enhancements

- [ ] LLM-as-judge evaluation (Phase 4)
- [ ] Metrics tracking over time (Phase 5)
- [ ] Regression detection
- [ ] Performance benchmarks
- [ ] Multi-image batch testing

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [LLM Evaluation Best Practices](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation)

---

**Status:** 13 tests | All passing ✅
