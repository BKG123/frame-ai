from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import os
import tempfile
import json
from config.logger import get_logger
from services.analysis import PhotoAnalyzer

logger = get_logger(__name__)
app = FastAPI(
    title="Frame AI",
    description="AI-powered photography coach and analysis tool",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML page"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {
            "message": "Welcome to Frame AI - Your Photography Coach",
            "version": "0.1.0",
            "endpoints": {
                "upload": "/upload - Upload and analyze a photo",
                "docs": "/docs - API documentation",
            },
        }


@app.post("/upload")
async def upload_and_analyze(file: UploadFile = File(...)):
    """Upload a photo and get streaming analysis"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    async def generate_analysis():
        try:
            async for chunk in analyzer.analyze_photo_from_file_stream(temp_file_path):
                # Format as server-sent events
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(str(e))
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate_analysis(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
