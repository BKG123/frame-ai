from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict
import numpy as np
from scipy import ndimage


def calculate_sharpness(img: Image.Image) -> float:
    """
    Calculate image sharpness using Laplacian variance.
    Higher values indicate sharper images with more detail.

    Args:
        img: PIL Image object

    Returns:
        float: Sharpness score (0-100 scale)
    """
    # Convert to grayscale
    gray = np.array(img.convert("L"))

    # Calculate Laplacian variance
    laplacian = ndimage.laplace(gray)
    variance = laplacian.var()

    # Normalize to 0-100 scale (empirical scaling)
    sharpness = min(100, variance / 10)

    return sharpness


def calculate_dynamic_range(img: Image.Image) -> float:
    """
    Calculate dynamic range based on histogram distribution.
    Measures how well the image uses available tonal range.

    Args:
        img: PIL Image object

    Returns:
        float: Dynamic range score (0-100 scale)
    """
    # Convert to grayscale
    gray = np.array(img.convert("L"))

    # Calculate histogram
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))

    # Find the range of tones used (non-zero bins)
    non_zero = hist > (hist.max() * 0.01)  # Filter noise
    used_range = non_zero.sum()

    # Calculate standard deviation (tonal spread)
    std_dev = gray.std()

    # Combine range and spread for final score
    range_score = (used_range / 256) * 100
    spread_score = (std_dev / 128) * 100

    dynamic_range = range_score * 0.4 + spread_score * 0.6

    return min(100, dynamic_range)


def calculate_color_richness(img: Image.Image) -> float:
    """
    Calculate color richness using color entropy and distribution.
    Measures color diversity and vibrancy.

    Args:
        img: PIL Image object

    Returns:
        float: Color richness score (0-100 scale)
    """
    # Convert to RGB
    rgb = np.array(img.convert("RGB"))

    # Calculate color entropy for each channel
    entropy_scores = []
    for channel in range(3):
        hist, _ = np.histogram(rgb[:, :, channel], bins=256, range=(0, 256))
        # Normalize histogram
        hist = hist / hist.sum()
        # Remove zeros to avoid log(0)
        hist = hist[hist > 0]
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist))
        entropy_scores.append(entropy)

    # Average entropy across channels
    avg_entropy = np.mean(entropy_scores)

    # Calculate color diversity (unique colors)
    unique_colors = len(np.unique(rgb.reshape(-1, 3), axis=0))
    max_possible = min(65536, rgb.shape[0] * rgb.shape[1])  # Cap for very large images
    diversity_score = (unique_colors / max_possible) * 100

    # Calculate saturation for vibrancy
    hsv = np.array(img.convert("HSV"))
    saturation = hsv[:, :, 1].mean() / 255 * 100

    # Combine metrics
    color_richness = avg_entropy / 8 * 40 + diversity_score * 0.3 + saturation * 0.3

    return min(100, color_richness)


def calculate_overall_quality(
    sharpness: float, dynamic_range: float, color_richness: float
) -> float:
    """
    Calculate overall quality score as weighted combination of metrics.

    Args:
        sharpness: Sharpness score
        dynamic_range: Dynamic range score
        color_richness: Color richness score

    Returns:
        float: Overall quality score (0-100 scale)
    """
    # Weighted average emphasizing sharpness and dynamic range
    quality = sharpness * 0.4 + dynamic_range * 0.35 + color_richness * 0.25

    return round(quality, 2)


def calculate_image_metrics(image_path: str) -> Dict[str, float]:
    """
    Calculate quality-focused metrics for an image that convey improvement.

    Args:
        image_path (str): The path to the input image file.

    Returns:
        Dict[str, float]: Dictionary containing quality metrics (0-100 scale).
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Calculate quality metrics
            sharpness = round(calculate_sharpness(img), 2)
            dynamic_range = round(calculate_dynamic_range(img), 2)
            color_richness = round(calculate_color_richness(img), 2)
            overall_quality = calculate_overall_quality(
                sharpness, dynamic_range, color_richness
            )

            return {
                "sharpness": sharpness,
                "dynamic_range": dynamic_range,
                "color_richness": color_richness,
                "overall_quality": overall_quality,
            }
    except Exception as e:
        raise Exception(f"Failed to calculate image metrics: {e}")


def compare_image_metrics(
    original_path: str, edited_path: str
) -> Dict[str, Dict[str, float]]:
    """
    Compare quality metrics between original and AI-edited images.

    Args:
        original_path (str): Path to the original image.
        edited_path (str): Path to the edited image.

    Returns:
        Dict[str, Dict[str, float]]: Dictionary containing original, edited, and improvement metrics.
    """
    try:
        original_metrics = calculate_image_metrics(original_path)
        edited_metrics = calculate_image_metrics(edited_path)

        # Calculate improvements (absolute and percentage)
        changes = {}
        for key in original_metrics.keys():
            absolute_change = edited_metrics[key] - original_metrics[key]
            percent_change = (
                (absolute_change / original_metrics[key] * 100)
                if original_metrics[key] != 0
                else 0
            )

            changes[key] = round(absolute_change, 2)
            changes[f"{key}_percent"] = round(percent_change, 2)

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
