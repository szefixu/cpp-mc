// physics.js
import { WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH } from './config.js';
// BlockType will be passed or imported if BlockType definition is also in this file or a central place
// For now, assume BlockType is passed to functions that need it.

export function isBlockSolid(x, y, z, worldData, BlockType) {
    if (x < 0 || x >= WORLD_WIDTH || y < 0 || y >= WORLD_HEIGHT || z < 0 || z >= WORLD_DEPTH) {
        return true; // Treat out-of-bounds as solid to prevent falling out of world
    }
    const blockId = worldData[Math.floor(x)][Math.floor(y)][Math.floor(z)];
    // Ensure getBlockTypeById is used if blockId itself isn't enough,
    // but here we just care about EMPTY vs. NOT_EMPTY
    // Assuming BlockType.EMPTY.id is well-defined and accessible
    return blockId !== BlockType.EMPTY.id;
}

export function checkCollision(playerPos, playerAABB, worldData, BlockType) {
    // playerPos is the center of the AABB.
    // playerAABB is an array [width, height, depth].
    const halfWidth = playerAABB[0] / 2;
    const halfHeight = playerAABB[1] / 2;
    const halfDepth = playerAABB[2] / 2;

    // Calculate player AABB min and max world coordinates
    const playerMinX = playerPos.x - halfWidth;
    const playerMaxX = playerPos.x + halfWidth;
    const playerMinY = playerPos.y - halfHeight; // Bottom of player
    const playerMaxY = playerPos.y + halfHeight; // Top of player
    const playerMinZ = playerPos.z - halfDepth;
    const playerMaxZ = playerPos.z + halfDepth;

    // Get the range of blocks to check (integer coordinates)
    // Add a small epsilon to correctly capture blocks when player is aligned with grid
    const minBlockX = Math.floor(playerMinX + 0.00001);
    const maxBlockX = Math.floor(playerMaxX - 0.00001);
    const minBlockY = Math.floor(playerMinY + 0.00001);
    const maxBlockY = Math.floor(playerMaxY - 0.00001);
    const minBlockZ = Math.floor(playerMinZ + 0.00001);
    const maxBlockZ = Math.floor(playerMaxZ - 0.00001);

    for (let bx = minBlockX; bx <= maxBlockX; bx++) {
        for (let by = minBlockY; by <= maxBlockY; by++) {
            for (let bz = minBlockZ; bz <= maxBlockZ; bz++) {
                if (isBlockSolid(bx, by, bz, worldData, BlockType)) {
                    // This simplified check assumes that if any block within the player's AABB range
                    // (defined by its min/max integer coordinates) is solid, a collision occurs.
                    // This is generally true for grid-based worlds where player AABB is block-aligned or larger.
                    // A more precise AABB vs. AABB check (as commented in the prompt)
                    // would be needed if player AABB was smaller than a block or for non-grid worlds.
                    return true; // Collision
                }
            }
        }
    }
    return false; // No collision
}
