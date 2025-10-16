from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import os
import tempfile
import json
import hashlib
from config.logger import get_logger
from services.analysis import PhotoAnalyzer
from services.database import db
from services.llm import gemini_llm_call, generate_image
from services.tools import compare_image_metrics
from prompts import (
    IMAGE_GEN_SYSTEM_PROMPT,
    IMAGE_GEN_USER_PROMPT,
    EDIT_INS_GEN_SYSTEM_PROMPT,
    EDIT_INS_GEN_USER_PROMPT,
)

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


class ImageEditRequest(BaseModel):
    file_hash: str


# Response models
class AnalyzeResponse(BaseModel):
    analysis: str


class EditResponse(BaseModel):
    results: Dict[str, str]


class ImageEditResponse(BaseModel):
    success: bool
    image_path: Optional[str] = None
    text_response: Optional[str] = None
    error: Optional[str] = None
    metrics: Optional[Dict] = None


class AnalysisHistoryResponse(BaseModel):
    id: int
    filename: str
    analysis_text: str
    created_at: str
    exif_data: Optional[Dict[str, str]] = None


# Initialize analyzer
analyzer = PhotoAnalyzer()

# Cache statistics (in-memory for demo purposes)
cache_stats = {"hits": 0, "misses": 0, "uploads": 0}


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


def get_content_hash(file_content: bytes) -> str:
    """
    Generate SHA-256 hash from file content for cache key and deduplication.

    This ensures:
    - Same image content = same hash (deduplication)
    - Different images with same filename = different hashes (correctness)
    - No PII (IP addresses) in cache keys (privacy)

    Args:
        file_content: Raw bytes of the uploaded file

    Returns:
        Hex string of SHA-256 hash (64 characters)
    """
    return hashlib.sha256(file_content).hexdigest()


@app.post("/upload")
async def upload_and_analyze(request: Request, file: UploadFile = File(...)):
    """Upload a photo and get streaming analysis with caching"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file content once for hashing and storage
    file_content = await file.read()

    # Generate content-based hash (fixes filename+IP weakness)
    file_hash = get_content_hash(file_content)

    # Get client IP for logging only (not used in cache key)
    client_ip = request.client.host if request.client else "unknown"

    # Track upload
    cache_stats["uploads"] += 1

    # Check if this file has been analyzed before
    try:
        cached_analysis = db.get_analysis_by_hash(file_hash)
    except Exception as e:
        logger.error(f"Failed to check cache: {e}")
        cached_analysis = None

    # Track cache hit/miss
    if cached_analysis:
        cache_stats["hits"] += 1
        logger.info(f"Cache HIT for hash: {file_hash[:8]}...")
    else:
        cache_stats["misses"] += 1
        logger.info(f"Cache MISS for hash: {file_hash[:8]}...")

    # Create directory for uploaded images if it doesn't exist
    upload_dir = "static/uploaded_images"
    os.makedirs(upload_dir, exist_ok=True)

    # Determine permanent storage path
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    stored_image_path = os.path.join(upload_dir, f"{file_hash}{file_extension}")

    # Only write permanent file if it doesn't exist (fixes redundant writes on cache hit)
    if not os.path.exists(stored_image_path):
        with open(stored_image_path, "wb") as stored_file:
            stored_file.write(file_content)
        logger.info(f"Stored new image: {stored_image_path}")
    else:
        logger.info(f"Image already exists (deduplication): {stored_image_path}")

    # Create temporary file for analysis (proper cleanup with context manager)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
    try:
        temp_file.write(file_content)
        temp_file.flush()
        temp_file_path = temp_file.name
    finally:
        temp_file.close()

    async def generate_analysis():
        yield f"file_hash: {json.dumps({'file_hash': file_hash})}\n\n"
        yield f"file_name: {json.dumps({'file_name': temp_file_path})}\n\n"

        if cached_analysis:
            # Return cached analysis
            try:
                yield f"data: {json.dumps({'type': 'cache_hit', 'content': 'Found previous analysis for this image'})}\n\n"
                yield f"data: {json.dumps({'type': 'analyzing', 'content': 'Loading cached analysis...'})}\n\n"

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
                        image_path=stored_image_path,
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


@app.post("/image/edit", response_model=ImageEditResponse)
async def edit_image(request: ImageEditRequest):
    """Edit an image using Gemini 2.5 Flash Image (Nano Banana) with original uploaded image and analysis context"""
    try:
        # Get the cached analysis and original image path
        cached_analysis = None
        try:
            cached_analysis = db.get_analysis_by_hash(request.file_hash)
        except Exception as e:
            logger.error(f"Failed to check cache: {e}")

        if not cached_analysis:
            raise HTTPException(
                status_code=404, detail="Couldn't find analysis for the file"
            )

        if not cached_analysis.get("image_path") or not os.path.exists(
            cached_analysis["image_path"]
        ):
            raise HTTPException(
                status_code=404,
                detail="Original image not found. Please re-upload the image.",
            )

        # Create output directory if it doesn't exist
        output_dir = "static/generated_images"
        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename for the edited image
        import uuid

        output_filename = f"edited_{uuid.uuid4().hex}.png"
        output_path = os.path.join(output_dir, output_filename)

        # Use existing prompts with analysis context only
        analysis_context = cached_analysis["analysis_text"]
        edit_ins_user_prompt = EDIT_INS_GEN_USER_PROMPT.format(
            analysis=analysis_context
        )

        # Generate editing instructions with error handling
        try:
            editing_instructions = await gemini_llm_call(
                system_prompt=EDIT_INS_GEN_SYSTEM_PROMPT,
                user_prompt=edit_ins_user_prompt,
                model_name="gemini-2.5-flash",
                temperature=0.5,
            )

            # Check if instructions were actually generated
            if not editing_instructions or not editing_instructions.strip():
                logger.error("Generated editing instructions are empty")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate editing instructions: AI returned empty response",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate editing instructions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate editing instructions: {str(e)}",
            )

        # Format the user prompt with analysis context only
        formatted_user_prompt = IMAGE_GEN_USER_PROMPT.format(
            instructions=editing_instructions
        )

        # Call the generate_image function with existing prompts
        result = generate_image(
            system_prompt=IMAGE_GEN_SYSTEM_PROMPT,
            user_prompt=formatted_user_prompt,
            input_image_path=cached_analysis["image_path"],
            output_file_path=output_path,
        )

        # Calculate before/after comparison metrics only if image was generated
        metrics = None
        if result.get("image_path") and os.path.exists(output_path):
            try:
                metrics = compare_image_metrics(
                    original_path=cached_analysis["image_path"], edited_path=output_path
                )
                logger.info(f"Metrics calculated successfully: {metrics}")
            except Exception as e:
                logger.error(f"Failed to calculate metrics: {e}")
                # Continue without metrics rather than failing the whole request
        else:
            logger.warning(
                f"Skipping metrics calculation - output image not found at {output_path}"
            )

        return ImageEditResponse(
            success=True,
            image_path=f"/static/generated_images/{output_filename}",
            text_response=result.get("text"),
            error=None,
            metrics=metrics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image editing: {e}")
        return ImageEditResponse(
            success=False, image_path=None, text_response=None, error=str(e)
        )


@app.post("/image/generate", response_model=ImageEditResponse)
async def generate_image_from_text(
    file: UploadFile = File(None),
    system_prompt: str = "You are an expert image editor. Create high-quality, detailed images based on the user's instructions.",
    user_prompt: str = "Create a beautiful image",
):
    """Generate a new image or edit an uploaded image using Gemini 2.5 Flash Image"""
    try:
        input_image_path = None

        # Handle uploaded file if provided
        if file and file.content_type and file.content_type.startswith("image/"):
            # Save uploaded file temporarily
            file_content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(file_content)
                input_image_path = temp_file.name

        # Create output directory if it doesn't exist
        output_dir = "static/generated_images"
        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        import uuid

        output_filename = f"generated_{uuid.uuid4().hex}.png"
        output_path = os.path.join(output_dir, output_filename)

        # Call the generate_image function
        result = generate_image(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            input_image_path=input_image_path,
            output_file_path=output_path,
        )

        # Clean up temporary file if it was created
        if input_image_path:
            try:
                os.unlink(input_image_path)
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {e}")

        return ImageEditResponse(
            success=True,
            image_path=f"/static/generated_images/{output_filename}",
            text_response=result.get("text"),
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        return ImageEditResponse(
            success=False, image_path=None, text_response=None, error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for monitoring performance.

    Returns:
        - hits: Number of cache hits
        - misses: Number of cache misses
        - uploads: Total uploads
        - hit_rate: Percentage of cache hits
        - unique_images: Number of unique images stored
    """
    try:
        # Get unique image count from filesystem
        upload_dir = "static/uploaded_images"
        unique_images = len(os.listdir(upload_dir)) if os.path.exists(upload_dir) else 0

        total_requests = cache_stats["hits"] + cache_stats["misses"]
        hit_rate = (
            (cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0
        )

        return {
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "total_uploads": cache_stats["uploads"],
            "hit_rate_percent": round(hit_rate, 2),
            "unique_images_stored": unique_images,
            "deduplication_savings": cache_stats["uploads"] - unique_images
            if cache_stats["uploads"] > 0
            else 0,
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve cache statistics"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
