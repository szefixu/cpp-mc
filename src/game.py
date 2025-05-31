import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL import glDeleteBuffers, glGetDoublev, glDeleteProgram, glDeleteVertexArrays # For VBO, matrix, shader/VAO cleanup & ops
import math
from enum import Enum
import numpy as np
from .config import *
from .block_type import BlockType, BLOCK_COLORS
# from .assets import std_cube_vertices, std_cube_faces, face_normals, cube_edges, tex_coords # Removed, as these are used by rendering.py
from .world_management import world_data, is_block_solid, generate_world
from .rendering import (load_main_texture_atlas, get_frustum_planes, is_block_in_frustum, 
                        draw_wireframe_cube_at, draw_hotbar, draw_fps_counter, # draw_cube_at removed
                        init_generic_cube_vbo, init_rendering_pipeline, draw_block_glsl) # Added VBO/Shader pipeline functions

# Note: std_cube_vertices etc. from assets are used by rendering functions.
# The 'assets' import is correctly placed within rendering.py.

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

# All rendering functions have been moved to src/rendering.py

def main():
    global world_data, current_selected_block_type 
    pygame.init(); pygame.font.init() 
    clock = pygame.time.Clock() # Initialize Pygame Clock
    ui_font = pygame.font.Font(None, 24) 
    display_width, display_height = 800, 600
    pygame.display.set_mode((display_width, display_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Voxel Engine - Mouse Look Review") 
    glClearColor(0.5,0.7,1.0,1.0); glEnable(GL_DEPTH_TEST); glEnable(GL_CULL_FACE); glCullFace(GL_BACK); glShadeModel(GL_SMOOTH)

    generate_world() # Initialize the world using the new function

    player_inventory = { BlockType.DIRT.value: 50, BlockType.STONE.value: 30, BlockType.GRASS.value: 10, BlockType.WOOD.value: 5 }
    hotbar_slots = [BlockType.GRASS, BlockType.DIRT, BlockType.STONE, BlockType.WOOD] 
    current_hotbar_selection_index = 0; current_selected_block_type = hotbar_slots[0].value 
    
    # ground_level is now internal to generate_world, but camera_pos needs it or an equivalent
    # For camera positioning, let's assume ground_level is still relevant if needed,
    # or adjust camera_pos based on a known spawn height from generate_world if it changes.
    # The current camera_pos uses ground_level from config, which is fine if generate_world also uses it.
    # Actually, ground_level was defined locally in main() before, and now implicitly in generate_world().
    # For camera_pos, we need a consistent way to determine player spawn height.
    # The current camera_pos uses `ground_level` which is now defined in `generate_world` and not directly here.
    # Let's assume player spawns relative to WORLD_HEIGHT // 3 for now.
    # This was: ground_level + PLAYER_AABB_DIMS[1]/2.0 + 1.0
    # Let's make it: (WORLD_HEIGHT // 3) + PLAYER_AABB_DIMS[1]/2.0 + 1.0

    # Load the main texture atlas
    atlas_id_for_cleanup = load_main_texture_atlas()
    # The block_texture_ids dictionary and loop for individual textures are removed.
    # draw_cube_at will now use the global texture_atlas_id from rendering.py

    # Initialize Generic Cube VBO
    vbo_id_for_cleanup, _ = init_generic_cube_vbo() 

    # Initialize Shader and VAO pipeline
    shader_program_id_for_cleanup, vao_id_for_cleanup = init_rendering_pipeline()
    if not shader_program_id_for_cleanup or not vao_id_for_cleanup:
        print("Failed to initialize rendering pipeline. Exiting.")
        # Cleanup already initialized resources
        if atlas_id_for_cleanup: glDeleteTextures(1, [atlas_id_for_cleanup])
        if vbo_id_for_cleanup: glDeleteBuffers(1, [vbo_id_for_cleanup])
        # Shader program and VAO might have been partially created, try cleanup if IDs exist
        if shader_program_id_for_cleanup: glDeleteProgram(shader_program_id_for_cleanup)
        if vao_id_for_cleanup: glDeleteVertexArrays(1, [vao_id_for_cleanup])
        pygame.quit()
        return # Or raise an exception
    
    glMatrixMode(GL_PROJECTION); gluPerspective(45, (display_width/display_height), 0.1, 100.0); glMatrixMode(GL_MODELVIEW)
    camera_pos = [WORLD_WIDTH/2.0, (WORLD_HEIGHT // 3) + PLAYER_AABB_DIMS[1]/2.0 + 1.0, WORLD_DEPTH/2.0] 
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
        frustum_planes = get_frustum_planes() # This still uses fixed-function matrix state
        
        # Get current matrices for shader-based rendering
        # glGetDoublev returns column-major matrices, which GLSL mat * vec expects. No transpose needed.
        projection_matrix = np.array(glGetDoublev(GL_PROJECTION_MATRIX), dtype=np.float32)
        view_matrix = np.array(glGetDoublev(GL_MODELVIEW_MATRIX), dtype=np.float32)

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        for x in range(WORLD_WIDTH):
            for y in range(WORLD_HEIGHT):
                for z in range(WORLD_DEPTH):
                    block_type_value = world_data[x][y][z]
                    if block_type_value != BlockType.EMPTY.value:
                        if is_block_in_frustum(x, y, z, frustum_planes): # Frustum culling re-enabled
                            current_block_type_enum = BlockType(block_type_value)
                            draw_block_glsl(x, y, z, current_block_type_enum, view_matrix, projection_matrix)
        
        # Old wireframe and UI still use immediate mode logic for now
        if targeted_block_info and targeted_block_info[0]: draw_wireframe_cube_at(*targeted_block_info[0])
        draw_hotbar(display_width,display_height,ui_font,hotbar_slots,player_inventory,current_hotbar_selection_index)
        
        # Calculate and draw FPS
        clock.tick() 
        fps = clock.get_fps()
        draw_fps_counter(fps, ui_font, display_width, display_height)
        
        pygame.display.flip() # pygame.time.wait(10) removed
    
    # Cleanup loaded textures
    if atlas_id_for_cleanup:
        glDeleteTextures(1, [atlas_id_for_cleanup])
    
    # Cleanup VBO
    if vbo_id_for_cleanup:
        glDeleteBuffers(1, [vbo_id_for_cleanup])
    
    # Cleanup Shader Program and VAO
    if shader_program_id_for_cleanup:
        glDeleteProgram(shader_program_id_for_cleanup)
    if vao_id_for_cleanup:
        glDeleteVertexArrays(1, [vao_id_for_cleanup])

    if pygame.font.get_init(): pygame.font.quit() # Quit font module
    pygame.quit()

if __name__ == "__main__":
    main()
