// BlockType.js
export const BlockType = {
    // Order matches assumed vertical atlas: GRASS, DIRT, STONE, WOOD, LEAVES
    // atlasIndex: 0 for top texture (GRASS), 4 for bottom texture (LEAVES)
    // vOffset = (totalTextures - 1 - atlasIndex) * textureHeightRatio
    // textureHeightRatio = 1 / totalTextures
    EMPTY:  { id: 0, name: 'empty', atlasIndex: -1 }, // No texture
    GRASS:  { id: 1, name: 'grass', atlasIndex: 0 },
    DIRT:   { id: 2, name: 'dirt',  atlasIndex: 1 },
    STONE:  { id: 3, name: 'stone', atlasIndex: 2 },
    WOOD:   { id: 4, name: 'wood',  atlasIndex: 3 },
    LEAVES: { id: 5, name: 'leaves',atlasIndex: 4 }
};

export const ATLAS_NUM_TEXTURES = 5; // Total number of textures in the vertical strip

export function getBlockTypeById(id) {
    for (const key in BlockType) {
        if (BlockType[key].id === id) {
            return BlockType[key];
        }
    }
    return BlockType.EMPTY;
}
