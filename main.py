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
from services.llm import generate_image
from prompts import IMAGE_GEN_SYSTEM_PROMPT, IMAGE_GEN_USER_PROMPT

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


def get_hash_from_ip_filename(ip: str, file_name: str):
    # create hash using filename and client_ip
    file_hash = file_name + "_" + ip
    return file_hash


@app.post("/upload")
async def upload_and_analyze(request: Request, file: UploadFile = File(...)):
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    """Upload a photo and get hash"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    filename = file.filename or "unknown"
    file_hash = get_hash_from_ip_filename(client_ip, filename)

    # Check if this file has been analyzed before
    try:
        cached_analysis = db.get_analysis_by_hash(file_hash)
    except Exception as e:
        logger.error(f"Failed to check cache: {e}")
        cached_analysis = None

    file_content = await file.read()

    # Create directory for uploaded images if it doesn't exist
    upload_dir = "static/uploaded_images"
    os.makedirs(upload_dir, exist_ok=True)

    # Save the original image with file_hash as filename
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    stored_image_path = os.path.join(upload_dir, f"{file_hash}{file_extension}")

    # Save original image permanently
    with open(stored_image_path, "wb") as stored_file:
        stored_file.write(file_content)

    # Create temporary file for analysis (will be deleted after analysis)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name

    async def generate_analysis():
        yield f"file_hash: {json.dumps({'file_hash': file_hash})}"
        yield f"file_name: {json.dumps({'file_name': temp_file_path})}"

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

        # Format the user prompt with analysis context only
        formatted_user_prompt = IMAGE_GEN_USER_PROMPT.format(analysis=analysis_context)

        # Call the generate_image function with existing prompts
        result = generate_image(
            system_prompt=IMAGE_GEN_SYSTEM_PROMPT,
            user_prompt=formatted_user_prompt,
            input_image_path=cached_analysis["image_path"],
            output_file_path=output_path,
        )

        return ImageEditResponse(
            success=True,
            image_path=f"/static/generated_images/{output_filename}",
            text_response=result.get("text"),
            error=None,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
