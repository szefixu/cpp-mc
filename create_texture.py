import os
from PIL import Image, ImageDraw

def create_solid_color_texture(filename, color, size=(64, 64)):
    """
    Creates a PNG image file of a solid color.

    Args:
        filename (str): The name of the file to save (e.g., "grass.png").
        color (tuple): An RGB tuple for the color (e.g., (0, 128, 0)).
        size (tuple): A tuple for the image size (width, height).
    """
    try:
        # Create the 'textures' directory if it doesn't exist
        output_directory = "textures"
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"Created directory: {output_directory}")

        filepath = os.path.join(output_directory, filename)

        # Create a new image with the given size and color
        img = Image.new("RGB", size, color)
        
        # Save the image
        img.save(filepath, "PNG")
        print(f"Successfully created texture: {filepath}")

    except Exception as e:
        print(f"Error creating texture {filename}: {e}")

if __name__ == "__main__":
    textures_to_create = [
        {"filename": "grass.png", "color": (0, 128, 0)},    # Green
        {"filename": "dirt.png", "color": (139, 69, 19)},   # Brown
        {"filename": "stone.png", "color": (128, 128, 128)}, # Gray
        {"filename": "wood.png", "color": (160, 82, 45)},   # Light Brown / Wood
        {"filename": "leaves.png", "color": (0, 100, 0)}    # Darker Green
    ]

    print("Starting texture generation...")
    for texture_info in textures_to_create:
        create_solid_color_texture(
            filename=texture_info["filename"],
            color=texture_info["color"]
        )
    print("Texture generation finished.")
