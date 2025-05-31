// worldGenerator.js
import { WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH } from './config.js';
// BlockType will be passed as an argument to generateWorld, or imported if preferred
// For this subtask, let's assume BlockType is passed.

export function generateWorld(worldData, BlockType) {
    console.log("Generating world...");
    const groundLevel = Math.floor(WORLD_HEIGHT / 3); // Similar to original Python version

    for (let x = 0; x < WORLD_WIDTH; x++) {
        for (let z = 0; z < WORLD_DEPTH; z++) {
            // Fill with dirt up to groundLevel
            for (let y = 0; y < groundLevel; y++) {
                worldData[x][y][z] = BlockType.DIRT.id;
            }
            // Place grass on top of dirt
            if (groundLevel < WORLD_HEIGHT) { // Ensure groundLevel is within bounds
                 worldData[x][groundLevel][z] = BlockType.GRASS.id;
            }
            // The rest above groundLevel remains BlockType.EMPTY.id as initialized
        }
    }

    // Example of adding a few stone blocks like in the original, for variety
    // Ensure these are within bounds based on config.js
    if (WORLD_WIDTH > 5 && WORLD_HEIGHT > (groundLevel + 3) && WORLD_DEPTH > 5) {
        try { // Add try-catch for safety if groundLevel is too high relative to WORLD_HEIGHT
            worldData[1][groundLevel + 1][1] = BlockType.STONE.id;
            worldData[2][groundLevel + 1][2] = BlockType.STONE.id;
            worldData[2][groundLevel + 2][2] = BlockType.STONE.id;
        } catch (e) {
            console.warn("Could not place example stone blocks due to world height/groundLevel config:", e);
        }
    }
    console.log("World generation complete. Ground level:", groundLevel);
    // console.log("Example worldData[0][groundLevel][0]:", worldData[0][groundLevel][0]); // Should be GRASS
    // console.log("Example worldData[0][0][0]:", worldData[0][0][0]); // Should be DIRT
}
