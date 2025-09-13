from PIL import Image
from PIL.ExifTags import TAGS


def extract_exif_data(image_path):
    try:
        # Open the image
        image = Image.open(image_path)

        # Extract EXIF data
        exifdata = image.getexif()

        if exifdata:
            print(f"EXIF data for {image_path}:")
            # Loop through all the tags present in exifdata
            for tag_id in exifdata:
                # Get the tag name instead of tag ID
                tag_name = TAGS.get(tag_id, tag_id)
                # Get the corresponding value
                value = exifdata.get(tag_id)

                # Decode bytes if necessary for readability
                if isinstance(value, bytes):
                    try:
                        value = value.decode()
                    except UnicodeDecodeError:
                        pass  # Keep as bytes if decoding fails

                print(f"{tag_name:25}: {value}")
        else:
            print(f"No EXIF data found in {image_path}.")

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
image_file = "files/ADDE0FAC-1B94-41DC-9DC0-E3306F11B730_1_102_o.jpeg"  # Replace with the path to your image file
extract_exif_data(image_file)
