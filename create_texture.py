from PIL import Image, ImageDraw

def create_placeholder_texture(filename="placeholder_texture.png", size=(64, 64)):
    """
    Creates a simple placeholder PNG image with a red 'T' on a white background.
    """
    img = Image.new("RGBA", size, "white")
    draw = ImageDraw.Draw(img)

    # Draw a red 'T'
    text_color = "red"
    # Simple 'T' shape with lines
    # Vertical line
    draw.line([(size[0]*0.45, size[1]*0.2), (size[0]*0.45, size[1]*0.8)], fill=text_color, width=int(size[0]*0.1))
    # Horizontal line
    draw.line([(size[0]*0.3, size[1]*0.2), (size[0]*0.6, size[1]*0.2)], fill=text_color, width=int(size[0]*0.1))
    
    img.save(filename)
    print(f"Texture '{filename}' created successfully.")

if __name__ == "__main__":
    create_placeholder_texture()
