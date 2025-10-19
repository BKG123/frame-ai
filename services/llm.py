from google import genai

import os
from typing import Any

from google.genai import types
import requests
from dotenv import load_dotenv
from config.logger import get_logger
from utils.helpers import get_file_mime_type


load_dotenv(override=True)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
logger = get_logger(__name__)


def _prepare_image_part(image_data: bytes, source: str) -> types.Part:
    """
    Create a Part object from image data.

    Args:
        image_data: Raw image bytes
        source: Source path or URL for MIME type detection

    Returns:
        types.Part object ready for Gemini API
    """
    mime_type = get_file_mime_type(source)
    return types.Part.from_bytes(data=image_data, mime_type=mime_type)


def _prepare_contents(
    user_prompt: str | None,
    image_urls: list[str],
    image_file_path: str | None,
) -> list:
    """
    Prepare contents list with text and images for Gemini API.

    Args:
        user_prompt: Optional user text prompt
        image_urls: List of image URLs to fetch and include
        image_file_path: Optional local image file path

    Returns:
        List of contents (strings and Part objects) for API call
    """
    contents: list = []

    # Add user prompt if provided
    if user_prompt:
        contents.append(user_prompt)

    # Fetch and attach images from URLs
    for url in image_urls:
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()

            # Determine MIME type from headers or URL
            mime_type = resp.headers.get("Content-Type")
            if not mime_type:
                mime_type = get_file_mime_type(url)

            image_part = types.Part.from_bytes(
                data=resp.content,
                mime_type=mime_type,
            )
            contents.append(image_part)
        except Exception as e:
            logger.error(f"Warning: Skipping image {url} due to error: {e}")

    # Attach image from file path if provided
    if image_file_path:
        try:
            with open(image_file_path, "rb") as f:
                image_data = f.read()

            image_part = _prepare_image_part(image_data, image_file_path)
            contents.append(image_part)
        except Exception as e:
            logger.error(
                f"Warning: Skipping image file {image_file_path} due to error: {e}"
            )

    return contents


async def gemini_llm_call(
    system_prompt: str,
    user_prompt: str | None,
    model_name: str,
    temperature: float = 0.1,
    json_format: bool = False,
    is_thinking_enabled: bool = True,
    image_urls: list[str] = [],
    image_file_path: str | None = None,
    url_context: None = None,
    **kwargs,
):
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        response_mime_type = "application/json" if json_format else "text/plain"
        if is_thinking_enabled:
            thinking_budget = kwargs.get("thinking_budget", 1024)
        else:
            thinking_budget = 0

        # Set up tools only when needed and not using JSON format
        tools_config = None
        if not json_format and url_context:
            # For now, skip tools configuration as it requires specific setup
            tools_config = None

        config = types.GenerateContentConfig(
            response_mime_type=response_mime_type,
            temperature=temperature,
            top_p=0.95,
            top_k=64,
            system_instruction=system_prompt,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            tools=tools_config,
        )

        # Prepare contents with optional images
        contents = _prepare_contents(user_prompt, image_urls, image_file_path)

        # Call the Gemini API with combined contents (images + prompt)
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        # Build messages for logging
        messages = [{"role": "system", "content": system_prompt}]
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        if image_urls:
            for url in image_urls:
                messages.append({"role": "user", "content": f"[Attached {url}]"})

        print(messages)
        return response.text

    except Exception as e:
        logger.error(f"Error in Gemini LLM call: {e}")
        raise


async def gemini_llm_call_stream(
    system_prompt: str,
    user_prompt: str | None,
    model_name: str,
    temperature: float = 0.1,
    json_format: bool = False,
    is_thinking_enabled: bool = True,
    image_urls: list[str] = [],
    image_file_path: str | None = None,
    **kwargs,
):
    """Streaming version of gemini_llm_call"""
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        if is_thinking_enabled:
            thinking_budget = kwargs.get("thinking_budget", 1024)
        else:
            thinking_budget = 0

        response_mime_type = "application/json" if json_format else "text/plain"

        config = types.GenerateContentConfig(
            response_mime_type=response_mime_type,
            temperature=temperature,
            top_p=0.95,
            top_k=64,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            system_instruction=system_prompt,
        )

        # Prepare contents with optional images
        contents = _prepare_contents(user_prompt, image_urls, image_file_path)

        # Call the Gemini API with streaming
        response = client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=config,
        )

        # Yield streaming content
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Error in Gemini LLM streaming call: {e}")
        yield f"Error: {str(e)}"


def generate_image(
    system_prompt: str,
    user_prompt: str,
    input_image_path: str | None = None,
    output_file_path: str = "generated_image.png",
):
    """
    Generate or edit an image using Gemini 2.5 Flash Image (Nano Banana)

    Args:
        system_prompt: System instruction for the model
        user_prompt: User prompt describing the image generation/editing task
        input_image_path: Optional path to input image for editing
        output_file_path: Path where the generated image will be saved

    Returns:
        dict: Contains 'text' response and 'image_path' if successful
    """
    try:
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        # Prepare contents list
        contents: list[Any] = [user_prompt]

        # Add input image if provided (for image editing)
        if input_image_path:
            try:
                from PIL import Image, ImageOps

                # Open and auto-orient the image based on EXIF data
                input_image = Image.open(input_image_path)

                # Apply EXIF orientation to ensure correct rotation
                input_image = ImageOps.exif_transpose(input_image)

                contents.append(input_image)
            except Exception as e:
                logger.error(f"Error loading input image {input_image_path}: {e}")
                raise

        # Configure generation with system instruction
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            system_instruction=system_prompt,
        )

        # Generate content
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents,
            config=config,
        )

        result: dict[str, str | None] = {"text": None, "image_path": None}

        # Process response parts
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            logger.info(
                f"Processing {len(response.candidates[0].content.parts)} response parts"
            )
            for i, part in enumerate(response.candidates[0].content.parts):
                logger.info(
                    f"Part {i}: text={part.text is not None}, inline_data={part.inline_data is not None}"
                )
                if part.text is not None:
                    result["text"] = part.text
                    logger.info(f"Generated text: {part.text}")
                elif part.inline_data is not None and part.inline_data.data is not None:
                    from PIL import Image
                    from io import BytesIO

                    # Save the generated image
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(output_file_path)
                    result["image_path"] = output_file_path
                    logger.info(f"Generated image saved to: {output_file_path}")
                else:
                    logger.warning(f"Part {i} has neither text nor inline_data")

        return result

    except Exception as e:
        logger.error(f"Error in generate_image: {e}")
        raise
