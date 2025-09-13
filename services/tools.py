from PIL import Image, ImageEnhance, ImageFilter


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
