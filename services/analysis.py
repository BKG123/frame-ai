from typing import Dict, Any, Union
from services.llm import gemini_llm_call_stream
from prompts import ANALYSE_SYSTEM_PROMPT


class PhotoAnalyzer:
    def get_exif_context_from_file(self, file_path: str) -> str:
        """Extract and format EXIF data from local file for analysis"""
        from PIL import Image
        from PIL.ExifTags import TAGS

        try:
            image = Image.open(file_path)
            exifdata = image.getexif()

            analysis: Dict[str, Dict[Union[str, int], Any]] = {
                "camera_info": {},
                "technical_settings": {},
                "other_data": {},
            }

            if exifdata:
                for tag_id in exifdata:
                    tag_name = TAGS.get(tag_id, tag_id)
                    value = exifdata.get(tag_id)

                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except UnicodeDecodeError:
                            continue

                    # Categorize EXIF data
                    if tag_name in ["Make", "Model", "Software"]:
                        analysis["camera_info"][tag_name] = value
                    elif tag_name in [
                        "FNumber",
                        "ExposureTime",
                        "ISOSpeedRatings",
                        "FocalLength",
                    ]:
                        analysis["technical_settings"][tag_name] = value
                    else:
                        analysis["other_data"][tag_name] = value
            # Create context from EXIF data
            exif_context = ""
            if "technical_settings" in analysis:
                settings = analysis["technical_settings"]
                exif_context = f"""

**Available EXIF Data:**
- Aperture (f-stop): {settings.get("FNumber", "Not available")}
- Shutter Speed: {settings.get("ExposureTime", "Not available")}
- ISO: {settings.get("ISOSpeedRatings", "Not available")}
- Focal Length: {settings.get("FocalLength", "Not available")}
"""
            return exif_context

        except Exception as e:
            return f"Could not extract EXIF data: {e}"

    async def analyze_photo_from_file_stream(self, file_path: str):
        """Stream photo analysis from local file using Gemini with EXIF data context"""
        try:
            # Get EXIF data
            exif_context = self.get_exif_context_from_file(file_path)

            # Stream analysis results
            async for chunk in gemini_llm_call_stream(
                system_prompt=ANALYSE_SYSTEM_PROMPT,
                user_prompt=exif_context,
                model_name="gemini-2.5-flash",
                image_file_path=file_path,
            ):
                yield chunk

        except Exception as e:
            yield f"Error analyzing photo: {e}"
