from google import genai

import os
from mimetypes import guess_type
import mimetypes

from google.genai import types
import requests
from dotenv import load_dotenv
from config.logger import get_logger


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
    json_format: None = None,
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


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate_image(system_prompt: str, user_prompt: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
        system_instruction=[
            types.Part.from_text(text=system_prompt),
        ],
    )

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if (
            chunk.candidates[0].content.parts[0].inline_data
            and chunk.candidates[0].content.parts[0].inline_data.data
        ):
            file_name = f"ENTER_FILE_NAME_{file_index}"
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)
