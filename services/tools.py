from PIL import Image, ImageEnhance, ImageFilter, ImageStat
from typing import Dict


def calculate_image_metrics(image_path: str) -> Dict[str, float]:
    """
    Calculate brightness, contrast, and saturation metrics for an image.

    Args:
        image_path (str): The path to the input image file.

    Returns:
        Dict[str, float]: Dictionary containing brightness, contrast, and saturation values.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Calculate brightness (average luminance)
            # Convert to grayscale and calculate mean
            grayscale = img.convert("L")
            stat = ImageStat.Stat(grayscale)
            brightness = stat.mean[0]  # 0-255 scale

            # Calculate contrast (standard deviation of luminance)
            contrast = stat.stddev[0]  # 0-255 scale

            # Calculate saturation (average saturation in HSV color space)
            hsv_img = img.convert("HSV")
            hsv_stat = ImageStat.Stat(hsv_img)
            saturation = hsv_stat.mean[1]  # 0-255 scale

            return {
                "brightness": round(brightness, 2),
                "contrast": round(contrast, 2),
                "saturation": round(saturation, 2),
            }
    except Exception as e:
        raise Exception(f"Failed to calculate image metrics: {e}")


def compare_image_metrics(
    original_path: str, edited_path: str
) -> Dict[str, Dict[str, float]]:
    """
    Compare metrics between original and edited images.

    Args:
        original_path (str): Path to the original image.
        edited_path (str): Path to the edited image.

    Returns:
        Dict[str, Dict[str, float]]: Dictionary containing original, edited, and change metrics.
    """
    try:
        original_metrics = calculate_image_metrics(original_path)
        edited_metrics = calculate_image_metrics(edited_path)

        # Calculate percentage changes
        changes = {
            "brightness": round(
                edited_metrics["brightness"] - original_metrics["brightness"], 2
            ),
            "brightness_percent": round(
                (
                    (edited_metrics["brightness"] - original_metrics["brightness"])
                    / original_metrics["brightness"]
                    * 100
                )
                if original_metrics["brightness"] != 0
                else 0,
                2,
            ),
            "contrast": round(
                edited_metrics["contrast"] - original_metrics["contrast"], 2
            ),
            "contrast_percent": round(
                (
                    (edited_metrics["contrast"] - original_metrics["contrast"])
                    / original_metrics["contrast"]
                    * 100
                )
                if original_metrics["contrast"] != 0
                else 0,
                2,
            ),
            "saturation": round(
                edited_metrics["saturation"] - original_metrics["saturation"], 2
            ),
            "saturation_percent": round(
                (
                    (edited_metrics["saturation"] - original_metrics["saturation"])
                    / original_metrics["saturation"]
                    * 100
                )
                if original_metrics["saturation"] != 0
                else 0,
                2,
            ),
        }

        return {
            "original": original_metrics,
            "edited": edited_metrics,
            "changes": changes,
        }
    except Exception as e:
        raise Exception(f"Failed to compare image metrics: {e}")


def adjust_brightness(image_path: str, output_path: str, factor: float):
    """
    Adjusts the brightness of an image.

    Args:
        image_path (str): The path to the input image file.
        output_path (str): The path where the edited image will be saved.
        factor (float): The brightness factor. A value > 1.0 increases brightness,
                        and a value < 1.0 decreases it.
    """
    try:
        with Image.open(image_path) as img:
            enhancer = ImageEnhance.Brightness(img)
            bright_img = enhancer.enhance(factor)
            bright_img.save(output_path)
            return f"Successfully adjusted brightness and saved to {output_path}"
    except Exception as e:
        return f"Error: Failed to adjust brightness. {e}"


def enhance_saturation(image_path: str, output_path: str, factor: float):
    """
    Adjusts the color saturation of an image.

    Args:
        image_path (str): The path to the input image file.
        output_path (str): The path where the edited image will be saved.
        factor (float): The saturation factor. A value > 1.0 increases saturation,
                        0.0 makes the image black and white.
    """
    try:
        with Image.open(image_path) as img:
            enhancer = ImageEnhance.Color(img)
            saturated_img = enhancer.enhance(factor)
            saturated_img.save(output_path)
            return f"Successfully enhanced saturation and saved to {output_path}"
    except Exception as e:
        return f"Error: Failed to enhance saturation. {e}"


def apply_sharpen_filter(image_path: str, output_path: str):
    """
    Applies a sharpening filter to an image.

    Args:
        image_path (str): The path to the input image file.
        output_path (str): The path where the edited image will be saved.
    """
    try:
        with Image.open(image_path) as img:
            sharpened_img = img.filter(ImageFilter.SHARPEN)
            sharpened_img.save(output_path)
            return f"Successfully sharpened image and saved to {output_path}"
    except Exception as e:
        return f"Error: Failed to sharpen image. {e}"
