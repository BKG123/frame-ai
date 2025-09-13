from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import os
from services.analysis import PhotoAnalyzer

app = FastAPI(
    title="Frame AI",
    description="AI-powered photography coach and analysis tool",
    version="0.1.0",
)


# Request models
class AnalyzeRequest(BaseModel):
    image_url: HttpUrl


class EditRequest(BaseModel):
    image_url: HttpUrl
    output_dir: Optional[str] = "output"


# Response models
class AnalyzeResponse(BaseModel):
    analysis: str


class EditResponse(BaseModel):
    results: Dict[str, str]


# Initialize analyzer
analyzer = PhotoAnalyzer()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Frame AI - Your Photography Coach",
        "version": "0.1.0",
        "endpoints": {
            "analyze": "/analyze - Analyze a photo from URL",
            "edit": "/edit - Generate sample edited versions",
            "docs": "/docs - API documentation",
        },
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_photo(request: AnalyzeRequest):
    """Analyze a photograph and provide professional feedback"""
    try:
        analysis = await analyzer.analyze_photo(str(request.image_url))
        return AnalyzeResponse(analysis=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing photo: {str(e)}")


@app.post("/edit", response_model=EditResponse)
async def edit_photo(request: EditRequest):
    """Generate sample edited versions of the photo"""
    try:
        # Create output directory if it doesn't exist
        output_dir = request.output_dir or "output"
        os.makedirs(output_dir, exist_ok=True)

        edit_results = analyzer.suggest_edits(str(request.image_url), output_dir)
        return EditResponse(results=edit_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error editing photo: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
