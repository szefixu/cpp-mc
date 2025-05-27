from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL import sizeof, GLfloat # For VAO configuration
import ctypes # For VAO configuration
import pygame
import numpy as np
import math

from .assets import (std_cube_vertices, std_cube_faces, face_normals, tex_coords, cube_edges,
                     get_interleaved_cube_vertex_data, create_vbo, ATLAS_UV_COORDINATES) # Added VBO functions and ATLAS_UV_COORDINATES
from .config import LIGHT_DIRECTION, AMBIENT_LIGHT_STRENGTH, WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH 
from .world_management import is_block_solid 
from .block_type import BlockType, BLOCK_COLORS 
from .shader_utils import create_shader_program # For loading shaders

# Module-level variables for rendering pipeline
texture_atlas_id = None
cube_vbo_id = None
cube_vertex_count = 0 # Set by init_generic_cube_vbo
shader_program_id = None
cube_vao_id = None
uniform_locations = {}

# --- Old Utility Functions (to be commented out/removed) ---

# def dot_product(vec1, vec2):
#     return sum(a * b for a, b in zip(vec1, vec2))

# def get_vertex_ao_factor(v_world_x, v_world_y, v_world_z): # Calculates AO factor for a vertex
#     num_occluders = 0
#     for sx_offset in [-0.5, 0.5]:
#         for sy_offset in [-0.5, 0.5]:
#             for sz_offset in [-0.5, 0.5]:
#                 check_x = math.floor(v_world_x + sx_offset)
#                 check_y = math.floor(v_world_y + sy_offset)
#                 check_z = math.floor(v_world_z + sz_offset)
#                 if is_block_solid(check_x, check_y, check_z):
#                     num_occluders += 1
#     ao_factor = 1.0 - num_occluders * 0.075 
#     return max(0.3, ao_factor) 

# --- VBO Initialization (already exists) ---
def init_generic_cube_vbo():
    """
    Initializes a generic VBO for cube rendering.
    The VBO will contain interleaved vertex data (pos, normal, uv, ao).
    Returns the VBO ID and vertex count.
    """
    global cube_vbo_id, cube_vertex_count # Use global to modify module-level variables

    vertex_data = get_interleaved_cube_vertex_data()
    if vertex_data is None or vertex_data.size == 0:
        print("Error: Failed to get interleaved cube vertex data.")
        cube_vbo_id = 0 # Ensure it's marked as invalid
        cube_vertex_count = 0
        return cube_vbo_id, cube_vertex_count

    cube_vbo_id = create_vbo(vertex_data)
    if not cube_vbo_id: # create_vbo returns 0 on failure
        print("CRITICAL: Failed to create generic cube VBO.")
        cube_vertex_count = 0
    else:
        # 8 floats per vertex (3 pos, 3 normal, 2 uv) since AO is removed for now
        # Number of vertices = total floats / floats per vertex
        cube_vertex_count = len(vertex_data) // 8 
        if cube_vertex_count != 36:
             print(f"Warning: Expected 36 vertices for cube VBO, but got {cube_vertex_count} from data length {len(vertex_data)}. Stride is 8 floats.")
        # print(f"Generic Cube VBO Initialized. ID: {cube_vbo_id}, Vertex Count: {cube_vertex_count}")
    
    return cube_vbo_id, cube_vertex_count

# --- Shader and VAO Initialization ---
def init_rendering_pipeline():
    global shader_program_id, cube_vao_id, uniform_locations, cube_vbo_id, cube_vertex_count

    # Load and compile shaders, create shader program
    try:
        shader_program_id = create_shader_program("shaders/basic_vertex.glsl", "shaders/basic_fragment.glsl")
        if not shader_program_id:
            raise Exception("Failed to create shader program.")
    except Exception as e:
        print(f"CRITICAL: Rendering pipeline initialization failed during shader program creation: {e}")
        # Potentially fall back to old rendering or exit
        return False

    # Get uniform locations
    uniform_locations['model'] = glGetUniformLocation(shader_program_id, "model")
    uniform_locations['view'] = glGetUniformLocation(shader_program_id, "view")
    uniform_locations['projection'] = glGetUniformLocation(shader_program_id, "projection")
    uniform_locations['textureSampler'] = glGetUniformLocation(shader_program_id, "textureSampler")
    uniform_locations['lightDir'] = glGetUniformLocation(shader_program_id, "lightDir")
    uniform_locations['ambientStrength'] = glGetUniformLocation(shader_program_id, "ambientStrength")
    uniform_locations['uv_offset_scale'] = glGetUniformLocation(shader_program_id, "uv_offset_scale")
    # uniform_locations['vertex_ao_factors_array'] = glGetUniformLocation(shader_program_id, "vertex_ao_factors_array") # AO temporarily removed

    # Create and configure VAO
    cube_vao_id = glGenVertexArrays(1)
    glBindVertexArray(cube_vao_id)

    glBindBuffer(GL_ARRAY_BUFFER, cube_vbo_id) # VBO is already populated by init_generic_cube_vbo

    # Vertex attribute pointers (stride is 8 floats: 3 Pos, 3 Norm, 2 UV)
    stride = 8 * sizeof(GLfloat)
    # Position (loc 0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    # Normal (loc 1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * sizeof(GLfloat)))
    glEnableVertexAttribArray(1)
    # Texture Coords (loc 2)
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * sizeof(GLfloat)))
    glEnableVertexAttribArray(2)
    # AO Factor (loc 3) - attribute is disabled in shader and data removed from VBO for now

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    
    print("Rendering pipeline initialized (Shaders, VAO).")
    return shader_program_id, cube_vao_id


# --- Texture Loading and Text Rendering ---

def load_main_texture_atlas():
    """Loads the main texture atlas and stores its ID."""
    global texture_atlas_id
    texture_atlas_id = load_texture("textures/atlas.png")
    if texture_atlas_id is None:
        print("CRITICAL: Failed to load texture atlas 'textures/atlas.png'. Game may not render correctly.")
    # else:
        # print(f"Texture atlas loaded successfully. ID: {texture_atlas_id}")
    return texture_atlas_id

def load_texture(filename):
    try:
        surf = pygame.image.load(filename); data = pygame.image.tostring(surf, 'RGBA', True)
        w, h = surf.get_width(), surf.get_height()
    except Exception as e: print(f"Error loading texture {filename}: {e}"); return None
    tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tex_id

def text_to_texture(text, font, color=(255, 255, 255)):
    text_surface = font.render(text, True, color); text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_width(), text_surface.get_height()
    tex_id = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    return tex_id, width, height

# --- Frustum Culling ---

def get_frustum_planes():
    mvm = np.array(glGetDoublev(GL_MODELVIEW_MATRIX)).reshape(4,4, order='F') 
    pm = np.array(glGetDoublev(GL_PROJECTION_MATRIX)).reshape(4,4, order='F')  
    clip_matrix_col_major = np.dot(pm, mvm) 
    clip_matrix = clip_matrix_col_major.T 

    planes = []
    planes.append(clip_matrix[3] + clip_matrix[0]) # Left
    planes.append(clip_matrix[3] - clip_matrix[0]) # Right
    planes.append(clip_matrix[3] + clip_matrix[1]) # Bottom
    planes.append(clip_matrix[3] - clip_matrix[1]) # Top
    planes.append(clip_matrix[3] + clip_matrix[2]) # Near
    planes.append(clip_matrix[3] - clip_matrix[2]) # Far

    normalized_planes = []
    for plane in planes:
        magnitude = np.sqrt(plane[0]**2 + plane[1]**2 + plane[2]**2)
        if magnitude == 0: 
            normalized_planes.append(plane) 
            continue
        normalized_planes.append(plane / magnitude)
    return normalized_planes

def is_block_in_frustum(block_world_x, block_world_y, block_world_z, frustum_planes):
    half_extent = 0.5 
    for plane in frustum_planes:
        nx, ny, nz, d_plane = plane[0], plane[1], plane[2], plane[3]
        r_eff = half_extent * (abs(nx) + abs(ny) + abs(nz))
        dist_center_to_plane = nx * block_world_x + ny * block_world_y + nz * block_world_z + d_plane
        if dist_center_to_plane < -r_eff:
            return False
    return True

# --- Object Drawing Functions ---

# def draw_cube_at(pos_x, pos_y, pos_z, current_block_texture_id): 
#     """Old immediate mode drawing function for a single cube. Fully Commented Out."""
#     # This function used glBegin/glEnd and is replaced by draw_block_glsl.
#     # AO logic was also embedded here.
#     # glPushMatrix(); glTranslatef(float(pos_x), float(pos_y), float(pos_z))
#     # if current_block_texture_id: glBindTexture(GL_TEXTURE_2D, current_block_texture_id); glEnable(GL_TEXTURE_2D)
#     # else: glDisable(GL_TEXTURE_2D)
# 
#     # # --- AO Calculation Start (Old) ---
#     # vertex_ao_factors = []
#     # for local_vx, local_vy, local_vz in std_cube_vertices:
#     #     world_vx = pos_x + local_vx; world_vy = pos_y + local_vy; world_vz = pos_z + local_vz
#     #     # vertex_ao_factors.append(get_vertex_ao_factor(world_vx, world_vy, world_vz)) # get_vertex_ao_factor is commented
#     # # --- AO Calculation End (Old) ---
# 
#     # for face_idx, face_vertex_indices in enumerate(std_cube_faces):
#     #     face_normal = face_normals[face_idx]
#     #     # diffuse_factor = max(0, dot_product(face_normal, LIGHT_DIRECTION)) # dot_product is commented
#     #     diffuse_factor = 0.7 # Example fixed diffuse factor
#     #     brightness_from_sun = AMBIENT_LIGHT_STRENGTH + diffuse_factor * (1.0 - AMBIENT_LIGHT_STRENGTH)
#     #     
#     #     glBegin(GL_QUADS)
#     #     for i, vertex_index in enumerate(face_vertex_indices):
#     #         # ao_factor = vertex_ao_factors[vertex_index] # Old AO
#     #         ao_factor = 1.0 # No AO for now
#     #         final_brightness = brightness_from_sun * ao_factor
#     #         glColor3f(final_brightness, final_brightness, final_brightness)
#     #         glTexCoord2fv(tex_coords[i])
#     #         glVertex3fv(std_cube_vertices[vertex_index])
#     #     glEnd()
# 
#     # if current_block_texture_id: glBindTexture(GL_TEXTURE_2D, 0)
#     # glPopMatrix()

def draw_block_glsl(block_world_x, block_world_y, block_world_z, block_type_enum, view_matrix, projection_matrix):
    global shader_program_id, cube_vao_id, texture_atlas_id, uniform_locations, cube_vertex_count

    if not shader_program_id or not cube_vao_id or not cube_vbo_id: # Ensure VBO is also checked
        print("Error: Shader, VAO, or VBO not initialized for draw_block_glsl.")
        return

    glUseProgram(shader_program_id)
    glBindVertexArray(cube_vao_id)

    # Set Model Matrix
    model_m = np.identity(4, dtype=np.float32)
    model_m[3,0:3] = [block_world_x, block_world_y, block_world_z]
    glUniformMatrix4fv(uniform_locations['model'], 1, GL_FALSE, model_m)

    # Set View and Projection Matrices (passed as arguments)
    glUniformMatrix4fv(uniform_locations['view'], 1, GL_FALSE, view_matrix)
    glUniformMatrix4fv(uniform_locations['projection'], 1, GL_FALSE, projection_matrix)

    # Set Texture Atlas Sampler
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_atlas_id)
    glUniform1i(uniform_locations['textureSampler'], 0)

    # Set Lighting Uniforms
    glUniform3fv(uniform_locations['lightDir'], 1, LIGHT_DIRECTION)
    glUniform1f(uniform_locations['ambientStrength'], AMBIENT_LIGHT_STRENGTH)

    # Set UV Transform Uniforms
    block_name = block_type_enum.name.lower()
    uv_coords = ATLAS_UV_COORDINATES.get(block_name)
    if uv_coords:
        u_min, v_min, u_max, v_max = uv_coords
        uv_offset = [u_min, v_min]
        uv_scale = [u_max - u_min, v_max - v_min]
        glUniform4f(uniform_locations['uv_offset_scale'], uv_offset[0], uv_offset[1], uv_scale[0], uv_scale[1])
    else:
        # Default to full texture if not found (or a specific part like stone)
        glUniform4f(uniform_locations['uv_offset_scale'], 0.0, 0.0, 1.0, 1.0)
        print(f"Warning: UV coordinates for block type '{block_name}' not found in ATLAS_UV_COORDINATES. Using default UVs.")

    # Draw the cube
    glDrawArrays(GL_TRIANGLES, 0, cube_vertex_count) # cube_vertex_count should be 36

    glBindVertexArray(0)
    glUseProgram(0)


def draw_wireframe_cube_at(pos_x, pos_y, pos_z):
    glPushMatrix(); glTranslatef(float(pos_x), float(pos_y), float(pos_z))
    glDisable(GL_TEXTURE_2D); glColor3f(0.0,0.0,0.0); glLineWidth(2.0)
    glBegin(GL_LINES)
    for edge in cube_edges:
        for v_idx in edge: glVertex3fv(std_cube_vertices[v_idx])
    glEnd(); glPopMatrix()

# --- UI Drawing Functions ---

def draw_hotbar(screen_width, screen_height, font, hotbar_slots_types, player_inventory, current_selection_idx):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_CULL_FACE); glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    slot_size=50; padding=5; num_slots=len(hotbar_slots_types); hotbar_width=num_slots*slot_size+(num_slots-1)*padding
    start_x=(screen_width-hotbar_width)/2; start_y=20
    
    glColor4f(0.2,0.2,0.2,0.7); glBegin(GL_QUADS); glVertex2f(start_x-padding,start_y-padding); glVertex2f(start_x+hotbar_width+padding,start_y-padding); glVertex2f(start_x+hotbar_width+padding,start_y+slot_size+padding); glVertex2f(start_x-padding,start_y+slot_size+padding); glEnd()
    
    for i, block_type_enum in enumerate(hotbar_slots_types): # block_type_enum is a BlockType instance
        slot_x = start_x+i*(slot_size+padding)
        glColor4f(0.4,0.4,0.4,0.7); glBegin(GL_QUADS); glVertex2f(slot_x,start_y); glVertex2f(slot_x+slot_size,start_y); glVertex2f(slot_x+slot_size,start_y+slot_size); glVertex2f(slot_x,start_y+slot_size); glEnd()
        
        block_color=BLOCK_COLORS.get(block_type_enum,(100,100,100)); glColor3ub(*block_color); inner_pad=5
        glBegin(GL_QUADS); glVertex2f(slot_x+inner_pad,start_y+inner_pad); glVertex2f(slot_x+slot_size-inner_pad,start_y+inner_pad); glVertex2f(slot_x+slot_size-inner_pad,start_y+slot_size-inner_pad); glVertex2f(slot_x+inner_pad,start_y+slot_size-inner_pad); glEnd()
        
        glColor3f(1,1,1); quantity=player_inventory.get(block_type_enum.value,0) # Use .value here
        if quantity > 0:
            qty_tex_id,qty_w,qty_h=text_to_texture(str(quantity),font,(255,255,255))
            glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D,qty_tex_id)
            glBegin(GL_QUADS); glTexCoord2f(0,0); glVertex2f(slot_x+slot_size-qty_w-2,start_y+2); glTexCoord2f(1,0); glVertex2f(slot_x+slot_size-2,start_y+2); glTexCoord2f(1,1); glVertex2f(slot_x+slot_size-2,start_y+qty_h+2); glTexCoord2f(0,1); glVertex2f(slot_x+slot_size-qty_w-2,start_y+qty_h+2); glEnd()
            glDisable(GL_TEXTURE_2D); glDeleteTextures(1,[qty_tex_id])
            
        if i == current_selection_idx:
            glColor4f(1.0,1.0,0.0,0.5); glLineWidth(3.0)
            glBegin(GL_LINE_LOOP); glVertex2f(slot_x-1,start_y-1); glVertex2f(slot_x+slot_size+1,start_y-1); glVertex2f(slot_x+slot_size+1,start_y+slot_size+1); glVertex2f(slot_x-1,start_y+slot_size+1); glEnd()
            glLineWidth(1.0)
            
    glEnable(GL_DEPTH_TEST); glEnable(GL_CULL_FACE); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix(); glDisable(GL_BLEND)

def draw_fps_counter(fps_value, font, screen_width, screen_height):
    fps_text = f"FPS: {fps_value:.0f}"
    fps_tex_id, fps_tex_w, fps_tex_h = text_to_texture(fps_text, font, color=(255, 255, 0))

    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    glDisable(GL_DEPTH_TEST); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, fps_tex_id)

    x_pos = 10; y_pos = screen_height - fps_tex_h - 10
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
    glTexCoord2f(1, 0); glVertex2f(x_pos + fps_tex_w, y_pos)
    glTexCoord2f(1, 1); glVertex2f(x_pos + fps_tex_w, y_pos + fps_tex_h)
    glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + fps_tex_h)
    glEnd()

    glDisable(GL_TEXTURE_2D); glDeleteTextures(1, [fps_tex_id])
    glDisable(GL_BLEND); glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()
