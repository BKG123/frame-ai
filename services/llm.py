from google import genai

import os
from mimetypes import guess_type

import requests
from dotenv import load_dotenv
from config.logger import get_logger
from google.genai import types


load_dotenv(override=True)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
logger = get_logger(__name__)


async def gemini_llm_call(
    system_prompt: str,
    user_prompt: str | None,
    model_name: str,
    temperature: float = 0.1,
    json_format: None = None,
    is_thinking_enabled: bool = True,
    image_urls: list[str] = [],
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
        # Only include the user prompt if it is provided
        contents: list = []
        if user_prompt:
            contents.append(user_prompt)

        # Fetch and attach images if provided
        for url in image_urls:
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()

                # Determine MIME type
                mime_type = resp.headers.get("Content-Type")
                if not mime_type:
                    mime_type, _ = guess_type(url)
                if not mime_type:
                    mime_type = "image/jpeg"  # sensible default

                # Wrap the image bytes into a Part so the SDK can handle inline images
                image_part = types.Part.from_bytes(
                    data=resp.content,
                    mime_type=mime_type,
                )
                contents.append(image_part)
            except Exception as e:
                logger.error(f"Warning: Skipping image {url} due to error: {e}")

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
        return response.text

    except Exception as e:
        logger.error(f"Error in Gemini LLM call: {e}")
        raise


async def gemini_llm_call_stream(
    system_prompt: str,
    user_prompt: str | None,
    model_name: str,
    temperature: float = 0.1,
    image_urls: list[str] = [],
    image_file_path: str | None = None,
    **kwargs,
):
    """Streaming version of gemini_llm_call"""
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            temperature=temperature,
            top_p=0.95,
            top_k=64,
            system_instruction=system_prompt,
        )

        # Prepare contents with optional images
        contents: list = []
        if user_prompt:
            contents.append(user_prompt)

        # Fetch and attach images from URLs if provided
        for url in image_urls:
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()

                # Determine MIME type
                mime_type = resp.headers.get("Content-Type")
                if not mime_type:
                    mime_type, _ = guess_type(url)
                if not mime_type:
                    mime_type = "image/jpeg"

                # Wrap the image bytes into a Part
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

                # Determine MIME type
                mime_type, _ = guess_type(image_file_path)
                if not mime_type:
                    mime_type = "image/jpeg"

                # Wrap the image bytes into a Part
                image_part = types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type,
                )
                contents.append(image_part)
            except Exception as e:
                logger.error(
                    f"Warning: Skipping image file {image_file_path} due to error: {e}"
                )

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
