from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import os
import tempfile
import json
from config.logger import get_logger
from services.analysis import PhotoAnalyzer
from services.database import db

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


class AnalysisHistoryResponse(BaseModel):
    id: int
    filename: str
    analysis_text: str
    created_at: str
    exif_data: Optional[Dict[str, str]] = None


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
                "upload": "/upload - Upload and analyze a photo (detailed + concise analysis)",
                "docs": "/docs - API documentation",
            },
        }


@app.post("/upload")
async def upload_and_analyze(request: Request, file: UploadFile = File(...)):
    """Upload a photo and get streaming analysis"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Read file content and create hash
    content = await file.read()
    file_hash = db.get_content_hash(content)

    # Check if this file has been analyzed before
    try:
        cached_analysis = db.get_analysis_by_hash(file_hash)
    except Exception as e:
        logger.error(f"Failed to check cache: {e}")
        cached_analysis = None

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

    async def generate_analysis():
        if cached_analysis:
            # Return cached analysis
            try:
                yield f"data: {json.dumps({'type': 'cache_hit', 'content': 'Found previous analysis for this image'})}\n\n"

                # Split cached analysis to separate detailed and JSON parts
                full_analysis = cached_analysis["analysis_text"]

                # Look for the JSON marker to split content
                if " *#123JSON PARSING START: " in full_analysis:
                    detailed_part, json_part = full_analysis.split(
                        " *#123JSON PARSING START: ", 1
                    )

                    # Send detailed analysis first
                    if detailed_part.startswith("DETAILED ANALYSIS: "):
                        detailed_content = detailed_part.replace(
                            "DETAILED ANALYSIS: ", ""
                        )
                        yield f"data: {json.dumps({'type': 'chunk', 'content': f'DETAILED ANALYSIS: {detailed_content}'})}\n\n"

                    # Send JSON marker
                    yield f"data: {json.dumps({'type': 'chunk', 'content': ' *#123JSON PARSING START: '})}\n\n"

                    # Send JSON part
                    yield f"data: {json.dumps({'type': 'chunk', 'content': json_part})}\n\n"
                else:
                    # Fallback: send as-is if no marker found
                    yield f"data: {json.dumps({'type': 'chunk', 'content': cached_analysis['analysis_text']})}\n\n"

                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"Failed to return cached analysis: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': 'Failed to retrieve cached analysis'})}\n\n"
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(str(e))
            return

        # Perform new analysis
        analysis_chunks = []
        try:
            yield f"data: {json.dumps({'type': 'analyzing', 'content': 'Analyzing new image...'})}\n\n"
            async for chunk in analyzer.analyze_photo_from_file_stream(temp_file_path):
                analysis_chunks.append(chunk)
                # Format as server-sent events
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            # Store analysis in database
            try:
                if analysis_chunks:
                    full_analysis = "".join(analysis_chunks)
                    # Get EXIF data for storage
                    exif_context = analyzer.get_exif_context_from_file(temp_file_path)

                    db.store_analysis(
                        ip_address=client_ip,
                        filename=file.filename or "unknown",
                        file_hash=file_hash,
                        analysis_text=full_analysis,
                        exif_data={"exif_context": exif_context},
                    )
            except Exception as e:
                logger.error(f"Failed to store analysis: {e}")

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


@app.get("/analysis/history")
async def get_analysis_history(request: Request, limit: int = 50):
    """Get analysis history for the requesting IP address"""
    client_ip = request.client.host if request.client else "unknown"

    try:
        analyses = db.get_analysis_by_ip(client_ip, limit)
        return {"status": "success", "count": len(analyses), "analyses": analyses}
    except Exception as e:
        logger.error(f"Failed to retrieve analysis history: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analysis history"
        )


@app.get("/analysis/{analysis_id}")
async def get_analysis(request: Request, analysis_id: int):
    """Get a specific analysis by ID (only if it belongs to the requesting IP)"""
    client_ip = request.client.host if request.client else "unknown"

    try:
        # First get all analyses for this IP to check ownership
        analyses = db.get_analysis_by_ip(client_ip, 1000)  # Large limit to check all
        analysis = next((a for a in analyses if a["id"] == analysis_id), None)

        if not analysis:
            raise HTTPException(
                status_code=404, detail="Analysis not found or access denied"
            )

        return {"status": "success", "analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")


@app.delete("/analysis/{analysis_id}")
async def delete_analysis(request: Request, analysis_id: int):
    """Delete a specific analysis by ID (only if it belongs to the requesting IP)"""
    client_ip = request.client.host if request.client else "unknown"

    try:
        success = db.delete_analysis(analysis_id, client_ip)
        if not success:
            raise HTTPException(
                status_code=404, detail="Analysis not found or access denied"
            )

        return {"status": "success", "message": "Analysis deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
