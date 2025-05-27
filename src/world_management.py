from .block_type import BlockType
from .config import WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH

# Global world_data variable
world_data = [[[BlockType.EMPTY.value for _ in range(WORLD_DEPTH)] for _ in range(WORLD_HEIGHT)] for _ in range(WORLD_WIDTH)]

def generate_world():
    """Generates the initial world terrain."""
    global world_data # Ensure we are modifying the module-level world_data
    
    ground_level = WORLD_HEIGHT // 3
    for x in range(WORLD_WIDTH):
        for z in range(WORLD_DEPTH):
            for y in range(ground_level):
                world_data[x][y][z] = BlockType.DIRT.value
            world_data[x][ground_level][z] = BlockType.GRASS.value
            
    # Manually placed blocks (example features)
    # Ensure these are within the new world bounds if they were close to edges before
    if WORLD_WIDTH > 5 and WORLD_HEIGHT > (ground_level + 3) and WORLD_DEPTH > 5:
        world_data[1][ground_level+1][1] = BlockType.STONE.value
        world_data[2][ground_level+1][2] = BlockType.STONE.value
        world_data[2][ground_level+2][2] = BlockType.STONE.value
        world_data[5][ground_level+1][5] = BlockType.WOOD.value
        world_data[5][ground_level+2][5] = BlockType.WOOD.value
        world_data[5][ground_level+3][5] = BlockType.LEAVES.value
        
        world_data[4][2][4]=BlockType.STONE.value # These might be below ground_level if it's low
        world_data[3][2][4]=BlockType.STONE.value
        world_data[5][2][4]=BlockType.STONE.value
        world_data[4][1][4]=BlockType.STONE.value
        world_data[4][3][4]=BlockType.STONE.value # This one could also be an issue
        world_data[4][2][3]=BlockType.STONE.value
        world_data[4][2][5]=BlockType.STONE.value

def is_block_solid(x, y, z):
    """Checks if a block at the given coordinates is solid (not EMPTY)."""
    # world_data is accessed directly as a module-level global
    # WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH are imported
    if not (0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT and 0 <= z < WORLD_DEPTH):
        return False 
    return world_data[x][y][z] != BlockType.EMPTY.value
