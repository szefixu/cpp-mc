import numpy as np
from OpenGL.GL import glGenBuffers, glBindBuffer, glBufferData, GL_ARRAY_BUFFER, GL_STATIC_DRAW

# Texture Atlas UV Coordinates
# These are EXAMPLE values. In a real scenario, these would come from the
# execution of the texture atlas generation script.
ATLAS_UV_COORDINATES = {
    'grass': (0.0, 0.0, 0.3333333333333333, 0.5),
    'dirt': (0.3333333333333333, 0.0, 0.6666666666666666, 0.5),
    'stone': (0.6666666666666666, 0.0, 1.0, 0.5),
    'wood': (0.0, 0.5, 0.3333333333333333, 1.0),
    'leaves': (0.3333333333333333, 0.5, 0.6666666666666666, 1.0)
    # Add other block types here if they are in the atlas
}

# Standard cube vertices (local coordinates, center is 0,0,0)
std_cube_vertices = [
    (-0.5, -0.5,  0.5),  # 0 (LBF) Left-Bottom-Front
    ( 0.5, -0.5,  0.5),  # 1 (RBF) Right-Bottom-Front
    ( 0.5,  0.5,  0.5),  # 2 (RTF) Right-Top-Front
    (-0.5,  0.5,  0.5),  # 3 (LTF) Left-Top-Front
    (-0.5, -0.5, -0.5),  # 4 (LBB) Left-Bottom-Back
    ( 0.5, -0.5, -0.5),  # 5 (RBB) Right-Bottom-Back
    ( 0.5,  0.5, -0.5),  # 6 (RTB) Right-Top-Back
    (-0.5,  0.5, -0.5)   # 7 (LTB) Left-Top-Back
]
# Faces based on std_cube_vertices (ensure counter-clockwise winding from outside)
std_cube_faces = [
    (0, 1, 2, 3),  # Front face (+Z)
    (5, 4, 7, 6),  # Back face (-Z)
    (4, 0, 3, 7),  # Left face (-X)
    (1, 5, 6, 2),  # Right face (+X)
    (3, 2, 6, 7),  # Top face (+Y)
    (4, 5, 1, 0)   # Bottom face (-Y)
]
# Corresponding normals for std_cube_faces
face_normals = [
    (0, 0, 1),   # Front
    (0, 0, -1),  # Back
    (-1, 0, 0),  # Left
    (1, 0, 0),   # Right
    (0, 1, 0),   # Top
    (0, -1, 0)   # Bottom
]

# Wireframe cube edges
cube_edges = (
    (0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), 
    (0,4), (1,5), (2,6), (3,7)
)

# Texture coordinates (original, per-face, not used with atlas directly for vertices)
# These are standard UVs for a single quad. The atlas UVs will be used to modify these
# or used directly in the shader based on the vertex.
tex_coords = ((0, 0), (1, 0), (1, 1), (0, 1))


def get_interleaved_cube_vertex_data() -> np.ndarray:
    """
    Generates interleaved vertex data for a cube suitable for a VBO.
    Data order: Position (3f), Normal (3f), Texture Coordinate (2f).
    Total 8 floats per vertex. 36 vertices for a cube (6 faces * 2 triangles/face * 3 vertices/triangle).
    AO factor is temporarily removed for shader-based rendering simplification.
    """
    interleaved_data = []
    # default_ao = 1.0 # AO Factor removed for now

    # Standard UV coordinates for a quad's vertices, used for each face.
    # These will be mapped to specific atlas regions later per block type.
    quad_uvs = [
        (0.0, 0.0), # Corresponds to tex_coords[0]
        (1.0, 0.0), # Corresponds to tex_coords[1]
        (1.0, 1.0), # Corresponds to tex_coords[2]
        (0.0, 1.0)  # Corresponds to tex_coords[3]
    ]

    for i, face_vertex_indices in enumerate(std_cube_faces):
        normal = face_normals[i]
        
        # Get the 4 vertices for the current face
        v0_idx, v1_idx, v2_idx, v3_idx = face_vertex_indices
        
        v0_pos = std_cube_vertices[v0_idx]
        v1_pos = std_cube_vertices[v1_idx]
        v2_pos = std_cube_vertices[v2_idx]
        v3_pos = std_cube_vertices[v3_idx]

        # Triangle 1: v0, v1, v2
        interleaved_data.extend([*v0_pos, *normal, *quad_uvs[0]])
        interleaved_data.extend([*v1_pos, *normal, *quad_uvs[1]])
        interleaved_data.extend([*v2_pos, *normal, *quad_uvs[2]])

        # Triangle 2: v0, v2, v3
        interleaved_data.extend([*v0_pos, *normal, *quad_uvs[0]])
        interleaved_data.extend([*v2_pos, *normal, *quad_uvs[2]])
        interleaved_data.extend([*v3_pos, *normal, *quad_uvs[3]])
        
    return np.array(interleaved_data, dtype=np.float32)

def create_vbo(vertex_data: np.ndarray) -> int:
    """
    Creates a VBO and uploads vertex data to it.

    Args:
        vertex_data (np.ndarray): A NumPy array containing the vertex data.

    Returns:
        int: The ID of the created VBO. Returns 0 if VBO creation fails.
    """
    try:
        vbo_id = glGenBuffers(1)
        if not vbo_id:
            print("Error: Failed to generate VBO ID.")
            return 0
            
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0) # Unbind
        return vbo_id
    except Exception as e:
        print(f"Error creating VBO: {e}")
        if vbo_id: # If ID was generated but an error occurred later
            # It's good practice to try to delete it, though context might be lost
            try:
                glDeleteBuffers(1, [vbo_id])
            except:
                pass # Avoid further errors during cleanup
        return 0
