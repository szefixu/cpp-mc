import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from enum import Enum
import numpy as np

# Block Types Enum
class BlockType(Enum):
    EMPTY = 0
    GRASS = 1
    DIRT = 2
    STONE = 3
    WOOD = 4 
    LEAVES = 5

# Block Colors for Hotbar (RGB)
BLOCK_COLORS = {
    BlockType.GRASS: (0, 150, 0),
    BlockType.DIRT: (139, 69, 19),
    BlockType.STONE: (128, 128, 128),
    BlockType.WOOD: (160, 82, 45),
    BlockType.LEAVES: (0, 100, 0)
}

# World dimensions
WORLD_WIDTH = 10
WORLD_HEIGHT = 10 
WORLD_DEPTH = 10

# Player AABB dimensions (width, height, depth)
PLAYER_AABB_DIMS = (0.6, 1.8, 0.6) 

# Physics Constants
GRAVITY = 0.015
JUMP_STRENGTH = 0.23

# Lighting Constants
LIGHT_DIRECTION_RAW = (0.8, 1.0, 0.6) # Raw direction
light_mag = math.sqrt(sum(v*v for v in LIGHT_DIRECTION_RAW))
LIGHT_DIRECTION = [v / light_mag for v in LIGHT_DIRECTION_RAW] # Normalized
AMBIENT_LIGHT_STRENGTH = 0.4

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

# Global world_data variable
world_data = [[[BlockType.EMPTY.value for _ in range(WORLD_DEPTH)] for _ in range(WORLD_HEIGHT)] for _ in range(WORLD_WIDTH)]

def is_block_solid(x, y, z):
    global world_data, WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH
    if not (0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT and 0 <= z < WORLD_DEPTH):
        return False 
    return world_data[x][y][z] != BlockType.EMPTY.value

def get_vertex_ao_factor(v_world_x, v_world_y, v_world_z): # This function will be unused temporarily
    num_occluders = 0
    for sx_offset in [-0.5, 0.5]:
        for sy_offset in [-0.5, 0.5]:
            for sz_offset in [-0.5, 0.5]:
                check_x = math.floor(v_world_x + sx_offset)
                check_y = math.floor(v_world_y + sy_offset)
                check_z = math.floor(v_world_z + sz_offset)
                if is_block_solid(check_x, check_y, check_z):
                    num_occluders += 1
    ao_factor = 1.0 - num_occluders * 0.075 
    return max(0.3, ao_factor) 

def dot_product(vec1, vec2):
    return sum(a * b for a, b in zip(vec1, vec2))

def check_collision(player_center_pos, player_dims):
    global world_data, WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH
    player_half_dims = [d / 2 for d in player_dims]
    player_min_c = [player_center_pos[i] - player_half_dims[i] for i in range(3)]
    player_max_c = [player_center_pos[i] + player_half_dims[i] for i in range(3)]
    min_bx = max(0, math.floor(player_min_c[0] - 0.01)); max_bx = min(WORLD_WIDTH - 1, math.ceil(player_max_c[0] +0.01)) 
    min_by = max(0, math.floor(player_min_c[1] - 0.01)); max_by = min(WORLD_HEIGHT - 1, math.ceil(player_max_c[1] +0.01)) 
    min_bz = max(0, math.floor(player_min_c[2] - 0.01)); max_bz = min(WORLD_DEPTH - 1, math.ceil(player_max_c[2] +0.01)) 
    collided_block_y_top = -1
    for bx in range(int(min_bx), int(max_bx) +1):
        for by in range(int(min_by), int(max_by) + 1):
            for bz in range(int(min_bz), int(max_bz) + 1):
                if world_data[bx][by][bz] != BlockType.EMPTY.value:
                    block_min_c = [bx - 0.5, by - 0.5, bz - 0.5]; block_max_c = [bx + 0.5, by + 0.5, bz + 0.5]
                    collision_x = player_min_c[0] < block_max_c[0] and player_max_c[0] > block_min_c[0]
                    collision_y = player_min_c[1] < block_max_c[1] and player_max_c[1] > block_min_c[1]
                    collision_z = player_min_c[2] < block_max_c[2] and player_max_c[2] > block_min_c[2]
                    if collision_x and collision_y and collision_z:
                        if collision_y: collided_block_y_top = block_max_c[1]
                        return True, collided_block_y_top 
    return False, None

def get_targeted_block(camera_pos, yaw, pitch, max_distance=5.0, step_size=0.05):
    global world_data
    rad_yaw = math.radians(yaw); rad_pitch = math.radians(pitch)
    dx = -math.sin(rad_yaw) * math.cos(rad_pitch); dy = math.sin(rad_pitch); dz = -math.cos(rad_yaw) * math.cos(rad_pitch)
    current_pos = list(camera_pos)
    for _ in range(int(max_distance / step_size)):
        prev = (int(current_pos[0] + 0.5), int(current_pos[1] + 0.5), int(current_pos[2] + 0.5))
        current_pos[0] += dx*step_size; current_pos[1] += dy*step_size; current_pos[2] += dz*step_size
        bx, by, bz = int(current_pos[0] + 0.5), int(current_pos[1] + 0.5), int(current_pos[2] + 0.5)
        if not (0<=bx<WORLD_WIDTH and 0<=by<WORLD_HEIGHT and 0<=bz<WORLD_DEPTH): continue
        if world_data[bx][by][bz] != BlockType.EMPTY.value:
            if prev and (0<=prev[0]<WORLD_WIDTH and 0<=prev[1]<WORLD_HEIGHT and 0<=prev[2]<WORLD_DEPTH):
                return ((bx,by,bz), prev)
            return ((bx,by,bz), None)
    return None

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

def get_frustum_planes():
    # PyOpenGL often returns matrices as flat arrays; reshape if necessary.
    # Matrices are typically column-major in OpenGL.
    
    # Get ModelView and Projection matrices
    mvm = np.array(glGetDoublev(GL_MODELVIEW_MATRIX)).reshape(4,4, order='F') # Fortran order for column-major
    pm = np.array(glGetDoublev(GL_PROJECTION_MATRIX)).reshape(4,4, order='F')  # Fortran order for column-major
    
    # Compute the clip matrix (Projection * ModelView)
    clip_matrix_col_major = np.dot(pm, mvm) 
    # Transpose to row-major for easier plane extraction, where each row is a plane (a,b,c,d)
    clip_matrix = clip_matrix_col_major.T 

    planes = []
    # Left plane:    clip_row_3 + clip_row_0
    planes.append(clip_matrix[3] + clip_matrix[0])
    # Right plane:   clip_row_3 - clip_row_0
    planes.append(clip_matrix[3] - clip_matrix[0])
    # Bottom plane:  clip_row_3 + clip_row_1
    planes.append(clip_matrix[3] + clip_matrix[1])
    # Top plane:     clip_row_3 - clip_row_1
    planes.append(clip_matrix[3] - clip_matrix[1])
    # Near plane:    clip_row_3 + clip_row_2
    planes.append(clip_matrix[3] + clip_matrix[2])
    # Far plane:     clip_row_3 - clip_row_2
    planes.append(clip_matrix[3] - clip_matrix[2])

    normalized_planes = []
    for plane in planes:
        # Normalize the plane: (a,b,c,d) / sqrt(a^2+b^2+c^2)
        magnitude = np.sqrt(plane[0]**2 + plane[1]**2 + plane[2]**2)
        if magnitude == 0: # Avoid division by zero, though unlikely with valid matrices
            normalized_planes.append(plane) # Should not happen
            continue
        normalized_planes.append(plane / magnitude)
    return normalized_planes

def is_block_in_frustum(block_world_x, block_world_y, block_world_z, frustum_planes):
    # Block center is (block_world_x, block_world_y, block_world_z)
    # Block half-extent (radius of sorts for AABB check)
    half_extent = 0.5 
    for plane in frustum_planes:
        nx, ny, nz, d_plane = plane[0], plane[1], plane[2], plane[3]
        
        # Calculate effective radius of AABB projected onto plane normal
        # This is sum of projections of half-extents onto the normal's axes
        r_eff = half_extent * (abs(nx) + abs(ny) + abs(nz))
        
        # Calculate distance from cube center to plane
        dist_center_to_plane = nx * block_world_x + ny * block_world_y + nz * block_world_z + d_plane
        
        # If distance is less than negative effective radius, cube is entirely outside this plane
        if dist_center_to_plane < -r_eff:
            return False # Cube is entirely outside this plane (on the "negative" side)
            
    return True # Cube is not entirely outside any plane (it's visible or intersecting)

def draw_cube_at(pos_x, pos_y, pos_z, current_block_texture_id):
    glPushMatrix(); glTranslatef(float(pos_x), float(pos_y), float(pos_z))
    if current_block_texture_id: glBindTexture(GL_TEXTURE_2D, current_block_texture_id); glEnable(GL_TEXTURE_2D)
    else: glDisable(GL_TEXTURE_2D)

    # --- AO Calculation Start (Temporarily Bypassed) ---
    # vertex_ao_factors = []
    # for local_vx, local_vy, local_vz in std_cube_vertices:
    #     world_vx = pos_x + local_vx; world_vy = pos_y + local_vy; world_vz = pos_z + local_vz
    #     vertex_ao_factors.append(get_vertex_ao_factor(world_vx, world_vy, world_vz))
    # --- AO Calculation End ---

    for face_idx, face_vertex_indices in enumerate(std_cube_faces):
        face_normal = face_normals[face_idx]
        diffuse_factor = max(0, dot_product(face_normal, LIGHT_DIRECTION))
        brightness_from_sun = AMBIENT_LIGHT_STRENGTH + diffuse_factor * (1.0 - AMBIENT_LIGHT_STRENGTH)
        
        glBegin(GL_QUADS)
        for i, vertex_index in enumerate(face_vertex_indices):
            # --- AO Application Start (Temporarily Bypassed) ---
            # ao_factor = vertex_ao_factors[vertex_index]
            # final_brightness = brightness_from_sun * ao_factor
            # glColor3f(final_brightness, final_brightness, final_brightness)
            # --- AO Application End ---
            
            # Apply Per-Face Lighting Only
            glColor3f(brightness_from_sun, brightness_from_sun, brightness_from_sun)
            
            glTexCoord2fv(tex_coords[i])
            glVertex3fv(std_cube_vertices[vertex_index])
        glEnd()

    if current_block_texture_id: glBindTexture(GL_TEXTURE_2D, 0) # Unbind only if a texture was bound
    glPopMatrix()

def draw_wireframe_cube_at(pos_x, pos_y, pos_z):
    glPushMatrix(); glTranslatef(float(pos_x), float(pos_y), float(pos_z))
    glDisable(GL_TEXTURE_2D); glColor3f(0.0,0.0,0.0); glLineWidth(2.0)
    glBegin(GL_LINES)
    for edge in cube_edges:
        for v_idx in edge: glVertex3fv(std_cube_vertices[v_idx])
    glEnd(); glPopMatrix()

def draw_hotbar(screen_width, screen_height, font, hotbar_slots_types, player_inventory, current_selection_idx):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_CULL_FACE); glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    slot_size=50; padding=5; num_slots=len(hotbar_slots_types); hotbar_width=num_slots*slot_size+(num_slots-1)*padding
    start_x=(screen_width-hotbar_width)/2; start_y=20
    glColor4f(0.2,0.2,0.2,0.7); glBegin(GL_QUADS); glVertex2f(start_x-padding,start_y-padding); glVertex2f(start_x+hotbar_width+padding,start_y-padding); glVertex2f(start_x+hotbar_width+padding,start_y+slot_size+padding); glVertex2f(start_x-padding,start_y+slot_size+padding); glEnd()
    for i, block_type_enum in enumerate(hotbar_slots_types):
        slot_x = start_x+i*(slot_size+padding)
        glColor4f(0.4,0.4,0.4,0.7); glBegin(GL_QUADS); glVertex2f(slot_x,start_y); glVertex2f(slot_x+slot_size,start_y); glVertex2f(slot_x+slot_size,start_y+slot_size); glVertex2f(slot_x,start_y+slot_size); glEnd()
        block_color=BLOCK_COLORS.get(block_type_enum,(100,100,100)); glColor3ub(*block_color); inner_pad=5
        glBegin(GL_QUADS); glVertex2f(slot_x+inner_pad,start_y+inner_pad); glVertex2f(slot_x+slot_size-inner_pad,start_y+inner_pad); glVertex2f(slot_x+slot_size-inner_pad,start_y+slot_size-inner_pad); glVertex2f(slot_x+inner_pad,start_y+slot_size-inner_pad); glEnd()
        glColor3f(1,1,1); quantity=player_inventory.get(block_type_enum.value,0)
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
    fps_tex_id, fps_tex_w, fps_tex_h = text_to_texture(fps_text, font, color=(255, 255, 0)) # Yellow color

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, fps_tex_id)

    x_pos = 10
    y_pos = screen_height - fps_tex_h - 10
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
    glTexCoord2f(1, 0); glVertex2f(x_pos + fps_tex_w, y_pos)
    glTexCoord2f(1, 1); glVertex2f(x_pos + fps_tex_w, y_pos + fps_tex_h)
    glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + fps_tex_h)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glDeleteTextures(1, [fps_tex_id]) # Delete texture as it's recreated each frame
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def main():
    global world_data, current_selected_block_type 
    pygame.init(); pygame.font.init() 
    clock = pygame.time.Clock() # Initialize Pygame Clock
    ui_font = pygame.font.Font(None, 24) 
    display_width, display_height = 800, 600
    pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Voxel Engine - Mouse Look Review") 
    glClearColor(0.5,0.7,1.0,1.0); glEnable(GL_DEPTH_TEST); glEnable(GL_CULL_FACE); glCullFace(GL_BACK); glShadeModel(GL_SMOOTH)

    player_inventory = { BlockType.DIRT.value: 50, BlockType.STONE.value: 30, BlockType.GRASS.value: 10, BlockType.WOOD.value: 5 }
    hotbar_slots = [BlockType.GRASS, BlockType.DIRT, BlockType.STONE, BlockType.WOOD] 
    current_hotbar_selection_index = 0; current_selected_block_type = hotbar_slots[0].value 
    ground_level = 3
    for x in range(WORLD_WIDTH):
        for z in range(WORLD_DEPTH):
            for y in range(ground_level): world_data[x][y][z] = BlockType.DIRT.value
            world_data[x][ground_level][z] = BlockType.GRASS.value
    world_data[1][ground_level+1][1]=BlockType.STONE.value; world_data[2][ground_level+1][2]=BlockType.STONE.value
    world_data[2][ground_level+2][2]=BlockType.STONE.value; world_data[5][ground_level+1][5]=BlockType.WOOD.value
    world_data[5][ground_level+2][5]=BlockType.WOOD.value; world_data[5][ground_level+3][5]=BlockType.LEAVES.value
    world_data[4][2][4]=BlockType.STONE.value; world_data[3][2][4]=BlockType.STONE.value; world_data[5][2][4]=BlockType.STONE.value
    world_data[4][1][4]=BlockType.STONE.value; world_data[4][3][4]=BlockType.STONE.value
    world_data[4][2][3]=BlockType.STONE.value; world_data[4][2][5]=BlockType.STONE.value

    block_texture_ids = {}
    textures_to_load = [
        (BlockType.GRASS, "textures/grass.png"),
        (BlockType.DIRT, "textures/dirt.png"),
        (BlockType.STONE, "textures/stone.png"),
        (BlockType.WOOD, "textures/wood.png"),
        (BlockType.LEAVES, "textures/leaves.png")
    ]
    for block_type_enum, texture_path in textures_to_load:
        tex_id = load_texture(texture_path)
        if tex_id is not None:
            block_texture_ids[block_type_enum] = tex_id
        else:
            print(f"Failed to load texture for {block_type_enum.name} from {texture_path}")
            # Optionally, assign a default placeholder or handle error
            # For now, blocks of this type might not render with texture

    glMatrixMode(GL_PROJECTION); gluPerspective(45, (display_width/display_height), 0.1, 100.0); glMatrixMode(GL_MODELVIEW)
    camera_pos = [WORLD_WIDTH/2.0, ground_level + PLAYER_AABB_DIMS[1]/2.0 + 2.1, WORLD_DEPTH/2.0] 
    camera_yaw, camera_pitch = 0.0, -30.0 
    mouse_sensitivity, move_speed = 0.1, 0.1; player_vertical_velocity = 0.0
    pygame.mouse.set_visible(False); pygame.event.set_grab(True)
    keys_pressed = {k:False for k in (pygame.K_w,pygame.K_s,pygame.K_a,pygame.K_d,pygame.K_SPACE)}
    targeted_block_info = None; running = True
    while running:
        targeted_block_info = get_targeted_block(camera_pos, camera_yaw, camera_pitch)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEMOTION:
                dx,dy=event.rel
                camera_yaw += dx * mouse_sensitivity
                camera_yaw %= 360.0 # Wrap yaw
                camera_pitch += dy * mouse_sensitivity
                camera_pitch = max(-90.0, min(90.0, camera_pitch)) # Clamp pitch
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key in keys_pressed: keys_pressed[event.key] = True
                if pygame.K_1 <= event.key <= pygame.K_4: 
                    idx=event.key-pygame.K_1
                    if idx < len(hotbar_slots): current_hotbar_selection_index=idx; current_selected_block_type=hotbar_slots[idx].value
            if event.type == pygame.KEYUP:
                if event.key in keys_pressed: keys_pressed[event.key] = False
            if event.type == pygame.MOUSEBUTTONDOWN and targeted_block_info:
                hit, prev = targeted_block_info
                if event.button==1 and hit:
                    hx,hy,hz=hit; rtv=world_data[hx][hy][hz]
                    if rtv!=BlockType.EMPTY.value: world_data[hx][hy][hz]=BlockType.EMPTY.value; player_inventory[rtv]=player_inventory.get(rtv,0)+1
                elif event.button==3 and prev:
                    px,py,pz=prev
                    if 0<=px<WORLD_WIDTH and 0<=py<WORLD_HEIGHT and 0<=pz<WORLD_DEPTH and world_data[px][py][pz]==BlockType.EMPTY.value:
                        if player_inventory.get(current_selected_block_type,0)>0:
                            world_data[px][py][pz]=current_selected_block_type; player_inventory[current_selected_block_type]-=1
        
        player_vertical_velocity -= GRAVITY
        og_pos=[camera_pos[0],camera_pos[1]-PLAYER_AABB_DIMS[1]/2.0-0.01,camera_pos[2]]; iog,_=check_collision(og_pos,PLAYER_AABB_DIMS)
        if keys_pressed[pygame.K_SPACE] and iog: player_vertical_velocity = JUMP_STRENGTH
        ry=math.radians(camera_yaw); fvx_=-math.sin(ry); fvz_=-math.cos(ry); svx_=math.cos(ry); svz_=math.sin(ry)
        dph_=[0,0]
        if keys_pressed[pygame.K_w]: dph_[0]+=fvx_; dph_[1]+=fvz_
        if keys_pressed[pygame.K_s]: dph_[0]-=fvx_; dph_[1]-=fvz_
        if keys_pressed[pygame.K_a]: dph_[0]-=svx_; dph_[1]-=svz_
        if keys_pressed[pygame.K_d]: dph_[0]+=svx_; dph_[1]+=svz_
        nrm=math.sqrt(dph_[0]**2+dph_[1]**2)
        if nrm>0: dph_[0]=(dph_[0]/nrm)*move_speed; dph_[1]=(dph_[1]/nrm)*move_speed
        cp_=list(camera_pos); npd_=[cp_[0]+dph_[0], cp_[1]+player_vertical_velocity, cp_[2]+dph_[1]]; anp_=list(cp_)
        tmpx_=[npd_[0],cp_[1],cp_[2]]; cx_,_=check_collision(tmpx_,PLAYER_AABB_DIMS)
        if not cx_: anp_[0]=npd_[0]
        tmpy_=[anp_[0],npd_[1],cp_[2]]; cy_,cby_=check_collision(tmpy_,PLAYER_AABB_DIMS)
        if not cy_: anp_[1]=npd_[1]
        else:
            if player_vertical_velocity<0: player_vertical_velocity=0; anp_[1]=(cby_ if cby_ is not None else round(cp_[1]-PLAYER_AABB_DIMS[1]/2.0)+PLAYER_AABB_DIMS[1]/2.0)+PLAYER_AABB_DIMS[1]/2.0+0.001
            elif player_vertical_velocity>0: player_vertical_velocity=0
        tmpz_=[anp_[0],anp_[1],npd_[2]]; cz_,_=check_collision(tmpz_,PLAYER_AABB_DIMS)
        if not cz_: anp_[2]=npd_[2]
        camera_pos=anp_
            
        glLoadIdentity(); glRotatef(camera_pitch,1,0,0); glRotatef(camera_yaw,0,1,0); glTranslatef(-camera_pos[0],-camera_pos[1],-camera_pos[2])
        
        # Get frustum planes for culling
        frustum_planes = get_frustum_planes()
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        for x in range(WORLD_WIDTH):
            for y in range(WORLD_HEIGHT):
                for z in range(WORLD_DEPTH):
                    block_type_value = world_data[x][y][z]
                    if block_type_value != BlockType.EMPTY.value:
                        # Perform frustum culling check before drawing
                        if is_block_in_frustum(x, y, z, frustum_planes):
                            current_block_type_enum = BlockType(block_type_value)
                            texture_id_for_block = block_texture_ids.get(current_block_type_enum)
                            # Call draw_cube_at with the specific texture ID
                            draw_cube_at(x, y, z, texture_id_for_block)
        if targeted_block_info and targeted_block_info[0]: draw_wireframe_cube_at(*targeted_block_info[0])
        draw_hotbar(display_width,display_height,ui_font,hotbar_slots,player_inventory,current_hotbar_selection_index)
        
        # Calculate and draw FPS
        clock.tick() 
        fps = clock.get_fps()
        draw_fps_counter(fps, ui_font, display_width, display_height)
        
        pygame.display.flip() # pygame.time.wait(10) removed
    
    # Cleanup loaded textures
    for tex_id in block_texture_ids.values():
        if tex_id is not None: # Ensure tex_id is valid before deleting
            glDeleteTextures(1, [tex_id])
    
    if pygame.font.get_init(): pygame.font.quit() # Quit font module
    pygame.quit()

if __name__ == "__main__":
    main()
