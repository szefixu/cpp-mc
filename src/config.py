import math

# World dimensions
WORLD_WIDTH = 30
WORLD_HEIGHT = 20 
WORLD_DEPTH = 30

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
