from enum import Enum

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
