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

# Texture coordinates
tex_coords = ((0, 0), (1, 0), (1, 1), (0, 1)) # Standard for a quad
