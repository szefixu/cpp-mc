import os
from PIL import Image, ImageDraw

# Directory for textures
TEXTURE_DIR = "textures"
TEXTURE_SIZE = 64 # Pixels

def ensure_textures_directory():
    """Ensures the textures directory exists."""
    if not os.path.exists(TEXTURE_DIR):
        os.makedirs(TEXTURE_DIR)
        print(f"Created directory: {TEXTURE_DIR}")

def create_solid_color_texture(filename, color, size=(TEXTURE_SIZE, TEXTURE_SIZE)):
    """
    Creates a PNG image file of a solid color if it doesn't already exist.

    Args:
        filename (str): The name of the file to save (e.g., "grass.png").
        color (tuple): An RGB tuple for the color (e.g., (0, 128, 0)).
        size (tuple): A tuple for the image size (width, height).
    """
    ensure_textures_directory()
    filepath = os.path.join(TEXTURE_DIR, filename)

    if os.path.exists(filepath):
        print(f"Texture {filepath} already exists. Skipping creation.")
        return

    try:
        img = Image.new("RGB", size, color)
        img.save(filepath, "PNG")
        print(f"Successfully created texture: {filepath}")
    except Exception as e:
        print(f"Error creating texture {filename}: {e}")

def generate_texture_atlas():
    """
    Generates individual solid color textures (if they don't exist)
    and then combines them into a texture atlas.
    Calculates and prints UV coordinates for each texture in the atlas.
    """
    ensure_textures_directory()

    # 1. Define source textures and their properties
    # These are the individual textures that will form the atlas.
    # The 'filename' will be saved in TEXTURE_DIR.
    # The 'color' is used if the file needs to be generated.
    # The 'name' is the key for UV coordinates.
    source_textures_data = [
        {'name': 'grass', 'filename': 'grass.png', 'color': (0, 128, 0)},
        {'name': 'dirt', 'filename': 'dirt.png', 'color': (139, 69, 19)},
        {'name': 'stone', 'filename': 'stone.png', 'color': (128, 128, 128)},
        {'name': 'wood', 'filename': 'wood.png', 'color': (160, 82, 45)},
        {'name': 'leaves', 'filename': 'leaves.png', 'color': (0, 100, 0)}
    ]

    print("\nStep 1: Ensuring individual textures exist...")
    for tex_data in source_textures_data:
        create_solid_color_texture(tex_data['filename'], tex_data['color'])

    # 2. Define atlas layout and dimensions
    grid_cols = 3
    grid_rows = 2 # To accommodate 5 textures, leaving one slot empty
    atlas_width = TEXTURE_SIZE * grid_cols
    atlas_height = TEXTURE_SIZE * grid_rows
    
    atlas_image = Image.new("RGB", (atlas_width, atlas_height))
    atlas_uvs = {}

    print("\nStep 2: Generating texture atlas...")
    for i, tex_data in enumerate(source_textures_data):
        name = tex_data['name']
        filepath = os.path.join(TEXTURE_DIR, tex_data['filename'])
        
        try:
            source_img = Image.open(filepath)
            if source_img.size != (TEXTURE_SIZE, TEXTURE_SIZE):
                print(f"Warning: Texture {filepath} is not {TEXTURE_SIZE}x{TEXTURE_SIZE}. Resizing.")
                source_img = source_img.resize((TEXTURE_SIZE, TEXTURE_SIZE))
        except FileNotFoundError:
            print(f"Error: Source texture {filepath} not found after attempting creation. Skipping.")
            continue
        except Exception as e:
            print(f"Error opening or resizing {filepath}: {e}. Skipping.")
            continue

        # Calculate position in the grid
        col = i % grid_cols
        row = i // grid_cols

        # Calculate pixel offset for pasting
        x_offset = col * TEXTURE_SIZE
        y_offset = row * TEXTURE_SIZE
        
        atlas_image.paste(source_img, (x_offset, y_offset))
        print(f"Pasted {name} at ({x_offset}, {y_offset})")

        # Calculate UV coordinates (normalized)
        u_min = col / grid_cols
        v_min = row / grid_rows # OpenGL typically has (0,0) at bottom-left, Pillow at top-left.
                               # For now, let's assume standard image coordinates for UVs (top-left origin).
                               # If OpenGL needs bottom-left origin for V, this might need adjustment (e.g., 1.0 - v_max, 1.0 - v_min).
                               # For now, this is consistent with how textures are usually mapped.
        u_max = (col + 1) / grid_cols
        v_max = (row + 1) / grid_rows
        
        atlas_uvs[name] = (u_min, v_min, u_max, v_max)

    # Save the atlas
    atlas_filepath = os.path.join(TEXTURE_DIR, "atlas.png")
    try:
        atlas_image.save(atlas_filepath, "PNG")
        print(f"\nSuccessfully created texture atlas: {atlas_filepath}")
    except Exception as e:
        print(f"Error saving texture atlas {atlas_filepath}: {e}")

    # Print UV coordinates
    print("\nCalculated UV Coordinates (u_min, v_min, u_max, v_max):")
    for name, uvs in atlas_uvs.items():
        print(f"  '{name}': ({uvs[0]:.4f}, {uvs[1]:.4f}, {uvs[2]:.4f}, {uvs[3]:.4f})")
    
    # For direct copy-paste into code if needed:
    print("\nUV Dictionary for copy-pasting:")
    print("atlas_uv_coords = {")
    for name, uvs in atlas_uvs.items():
        print(f"    '{name}': ({uvs[0]:.6f}, {uvs[1]:.6f}, {uvs[2]:.6f}, {uvs[3]:.6f}),")
    print("}")


if __name__ == "__main__":
    generate_texture_atlas()
