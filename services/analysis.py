import os
import base64
from typing import Dict, Optional
from anthropic import Anthropic
from .photo import extract_exif_data
from .tools import adjust_brightness, enhance_saturation, apply_sharpen_filter
from prompts import ANALYSE_SYSTEM_PROMPT


class PhotoAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))

    def get_exif_analysis(self, image_path: str) -> Dict:
        """Extract and format EXIF data for analysis"""
        from PIL import Image
        from PIL.ExifTags import TAGS

        try:
            image = Image.open(image_path)
            exifdata = image.getexif()

            analysis = {
                'camera_info': {},
                'technical_settings': {},
                'other_data': {}
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
                    if tag_name in ['Make', 'Model', 'Software']:
                        analysis['camera_info'][tag_name] = value
                    elif tag_name in ['FNumber', 'ExposureTime', 'ISOSpeedRatings', 'FocalLength']:
                        analysis['technical_settings'][tag_name] = value
                    else:
                        analysis['other_data'][tag_name] = value

            return analysis

        except Exception as e:
            return {'error': f'Could not extract EXIF data: {e}'}

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for Claude API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_photo(self, image_path: str) -> str:
        """Analyze photo using Claude with EXIF data context"""
        try:
            # Get EXIF data
            exif_analysis = self.get_exif_analysis(image_path)

            # Encode image
            base64_image = self.encode_image(image_path)

            # Create context from EXIF data
            exif_context = ""
            if 'technical_settings' in exif_analysis:
                settings = exif_analysis['technical_settings']
                exif_context = f"""

**Available EXIF Data:**
- Aperture (f-stop): {settings.get('FNumber', 'Not available')}
- Shutter Speed: {settings.get('ExposureTime', 'Not available')}
- ISO: {settings.get('ISOSpeedRatings', 'Not available')}
- Focal Length: {settings.get('FocalLength', 'Not available')}
"""

            # Combine system prompt with EXIF context
            full_prompt = ANALYSE_SYSTEM_PROMPT + exif_context

            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "Please analyze this photograph following your FotoMentor guidelines."
                            }
                        ]
                    }
                ],
                system=full_prompt
            )

            return message.content[0].text

        except Exception as e:
            return f"Error analyzing photo: {e}"

    def suggest_edits(self, image_path: str, output_dir: str = "output") -> Dict[str, str]:
        """Apply basic editing suggestions and save results"""
        results = {}

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(image_path))[0]

        try:
            # Apply basic enhancements
            brightness_path = os.path.join(output_dir, f"{filename}_bright.jpg")
            saturation_path = os.path.join(output_dir, f"{filename}_saturated.jpg")
            sharp_path = os.path.join(output_dir, f"{filename}_sharp.jpg")

            results['brightness'] = adjust_brightness(image_path, brightness_path, 1.2)
            results['saturation'] = enhance_saturation(image_path, saturation_path, 1.3)
            results['sharpening'] = apply_sharpen_filter(image_path, sharp_path)

        except Exception as e:
            results['error'] = f"Error applying edits: {e}"

        return results