import os
import base64
import requests
from io import BytesIO
from typing import Dict, Any, Union
from services.llm import gemini_llm_call
from .tools import adjust_brightness, enhance_saturation, apply_sharpen_filter
from prompts import ANALYSE_SYSTEM_PROMPT


class PhotoAnalyzer:
    def get_exif_analysis(self, image_url: str) -> Dict:
        """Extract and format EXIF data for analysis"""
        from PIL import Image
        from PIL.ExifTags import TAGS

        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
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

            return analysis

        except Exception as e:
            return {"error": f"Could not extract EXIF data: {e}"}

    def encode_image(self, image_url: str) -> str:
        """Encode image to base64 for Claude API"""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            raise Exception(f"Could not download image from URL: {e}")

    async def analyze_photo(self, image_url: str) -> str:
        """Analyze photo using Claude with EXIF data context"""
        try:
            # Get EXIF data
            exif_analysis = self.get_exif_analysis(image_url)

            # Create context from EXIF data
            exif_context = ""
            if "technical_settings" in exif_analysis:
                settings = exif_analysis["technical_settings"]
                exif_context = f"""

**Available EXIF Data:**
- Aperture (f-stop): {settings.get("FNumber", "Not available")}
- Shutter Speed: {settings.get("ExposureTime", "Not available")}
- ISO: {settings.get("ISOSpeedRatings", "Not available")}
- Focal Length: {settings.get("FocalLength", "Not available")}
"""

            # Combine system prompt with EXIF context
            return await gemini_llm_call(
                system_prompt=ANALYSE_SYSTEM_PROMPT,
                user_prompt=exif_context,
                model_name="gemini-2.5-flash",
            )

        except Exception as e:
            return f"Error analyzing photo: {e}"

    def suggest_edits(
        self, image_url: str, output_dir: str = "output"
    ) -> Dict[str, str]:
        """Apply basic editing suggestions and save results"""
        results = {}

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract filename from URL
        filename = (
            os.path.splitext(os.path.basename(image_url.split("?")[0]))[0] or "image"
        )

        try:
            # Download image first
            response = requests.get(image_url)
            response.raise_for_status()

            # Save temporary file
            temp_path = os.path.join(output_dir, f"{filename}_temp.jpg")
            with open(temp_path, "wb") as f:
                f.write(response.content)

            # Apply basic enhancements
            brightness_path = os.path.join(output_dir, f"{filename}_bright.jpg")
            saturation_path = os.path.join(output_dir, f"{filename}_saturated.jpg")
            sharp_path = os.path.join(output_dir, f"{filename}_sharp.jpg")

            results["brightness"] = adjust_brightness(temp_path, brightness_path, 1.2)
            results["saturation"] = enhance_saturation(temp_path, saturation_path, 1.3)
            results["sharpening"] = apply_sharpen_filter(temp_path, sharp_path)

            # Clean up temporary file
            os.remove(temp_path)

        except Exception as e:
            results["error"] = f"Error applying edits: {e}"

        return results
