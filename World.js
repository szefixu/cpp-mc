// World.js
// Ensure THREE is available globally or passed/imported if this becomes a class
if (typeof window.THREE === 'undefined') {
    console.error("World.js: THREE global not found.");
    throw new Error("THREE.js not loaded for World.js");
}
const THREE = window.THREE;

import { WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH } from './config.js';
import { generateWorld as populateWorldData } from './worldGenerator.js'; // Renamed for clarity

export let worldData = []; // Initialize as empty, initWorld will populate
export const blockMeshes = {};
export const materialsCache = {};

export function initWorld(BlockTypeRef) {
    worldData.length = 0; // Clear array if re-initializing
    for (let x = 0; x < WORLD_WIDTH; x++) {
        worldData[x] = new Array(WORLD_HEIGHT);
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            worldData[x][y] = new Array(WORLD_DEPTH).fill(BlockTypeRef.EMPTY.id);
        }
    }
    populateWorldData(worldData, BlockTypeRef); // generateWorld from worldGenerator.js populates worldData
    console.log("World.js: World initialized and generated.");
}

export function renderWorld(scene, blockGeometryRef, atlasTextureRef, BlockTypeRef, getBlockTypeByIdRef, ATLAS_NUM_TEXTURES_REF) {
    // Clear existing block meshes from the scene
    for (const key in blockMeshes) {
        scene.remove(blockMeshes[key]);
        // Materials are cached, so don't dispose them here.
        // Texture maps cloned for materials are also part of cached materials.
    }
    for (const prop of Object.getOwnPropertyNames(blockMeshes)) { // Clear the tracking object
        delete blockMeshes[prop];
    }

    let defaultMaterial = materialsCache['default_fallback'];
    // Check if atlasTextureRef or its image is not available for the textureFailed condition
    const textureFailed = !atlasTextureRef || !atlasTextureRef.image;

    if (textureFailed && !defaultMaterial) {
        console.warn("World.js: Using default material due to texture atlas issue (first time).");
        defaultMaterial = new THREE.MeshStandardMaterial({ color: 0xcccccc });
        materialsCache['default_fallback'] = defaultMaterial;
    }

    for (let x = 0; x < WORLD_WIDTH; x++) {
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            for (let z = 0; z < WORLD_DEPTH; z++) {
                const blockId = worldData[x][y][z];
                const blockType = getBlockTypeByIdRef(blockId);

                if (blockType.id !== BlockTypeRef.EMPTY.id && blockType.atlasIndex !== -1) {
                    let materialToUse = materialsCache[blockId];

                    if (!materialToUse) {
                        if (textureFailed) {
                            materialToUse = defaultMaterial;
                        } else {
                            const textureHeightRatio = 1 / ATLAS_NUM_TEXTURES_REF;
                            const newTextureForMaterial = atlasTextureRef.clone();
                            newTextureForMaterial.needsUpdate = true;
                            const vOffset = (ATLAS_NUM_TEXTURES_REF - 1 - blockType.atlasIndex) * textureHeightRatio;
                            newTextureForMaterial.offset.set(0, vOffset);
                            newTextureForMaterial.repeat.set(1, textureHeightRatio);

                            materialToUse = new THREE.MeshStandardMaterial({ map: newTextureForMaterial });
                            materialsCache[blockId] = materialToUse;
                        }
                    }

                    if (materialToUse) {
                        const mesh = new THREE.Mesh(blockGeometryRef, materialToUse);
                        mesh.position.set(x, y, z);
                        mesh.isWorldBlock = true;
                        scene.add(mesh);
                        blockMeshes[`${x}_${y}_${z}`] = mesh;
                    }
                }
            }
        }
    }
    // console.log("World.js: World rendering. Meshes:", Object.keys(blockMeshes).length);
}

export function addBlockToWorld(x, y, z, blockId, scene, blockGeometryRef, atlasTextureRef, BlockTypeRef, getBlockTypeByIdRef, ATLAS_NUM_TEXTURES_REF) {
    if (x<0||x>=WORLD_WIDTH||y<0||y>=WORLD_HEIGHT||z<0||z>=WORLD_DEPTH) {
        console.warn("World.js: Attempted to place block out of bounds:", x,y,z);
        return false;
    }
    if (worldData[x][y][z] !== BlockTypeRef.EMPTY.id) {
        // console.warn("World.js: Attempted to place block in occupied space:", x,y,z);
        return false;
    }

    worldData[x][y][z] = blockId;
    const blockType = getBlockTypeByIdRef(blockId);
    if (blockType.id === BlockTypeRef.EMPTY.id || blockType.atlasIndex === -1) {
        console.warn("World.js: Attempted to add invalid block type:", blockType.name);
        return false;
    }

    let materialToUse = materialsCache[blockId];
    if (!materialToUse) {
        const textureFailed = !atlasTextureRef || !atlasTextureRef.image;
        if (textureFailed) {
            materialToUse = materialsCache['default_fallback'] ||
                            (materialsCache['default_fallback'] = new THREE.MeshStandardMaterial({ color: 0x999999 }));
        } else {
            const textureHeightRatio = 1 / ATLAS_NUM_TEXTURES_REF;
            const newTextureForMaterial = atlasTextureRef.clone();
            newTextureForMaterial.needsUpdate = true;
            const vOffset = (ATLAS_NUM_TEXTURES_REF - 1 - blockType.atlasIndex) * textureHeightRatio;
            newTextureForMaterial.offset.set(0, vOffset);
            newTextureForMaterial.repeat.set(1, textureHeightRatio);
            materialToUse = new THREE.MeshStandardMaterial({ map: newTextureForMaterial });
            materialsCache[blockId] = materialToUse;
        }
    }

    if (materialToUse) {
        const mesh = new THREE.Mesh(blockGeometryRef, materialToUse);
        mesh.position.set(x, y, z);
        mesh.isWorldBlock = true;
        scene.add(mesh);
        blockMeshes[`${x}_${y}_${z}`] = mesh;
        // console.log(`World.js: Placed ${blockType.name} at ${x},${y},${z}`);
        return true;
    }
    console.warn("World.js: Failed to obtain material for block:", blockType.name);
    return false;
}

export function removeBlockFromWorld(x, y, z, scene, BlockTypeRef) { // Added BlockTypeRef for EMPTY check
    if (x >= 0 && x < WORLD_WIDTH && y >= 0 && y < WORLD_HEIGHT && z >= 0 && z < WORLD_DEPTH) {
        const brokenBlockId = worldData[x][y][z];
        if (brokenBlockId !== BlockTypeRef.EMPTY.id) { // Check against passed BlockTypeRef
            // console.log(`World.js: Removing block at ${x},${y},${z}`);
            worldData[x][y][z] = BlockTypeRef.EMPTY.id;
            const meshKey = `${x}_${y}_${z}`;
            const mesh = blockMeshes[meshKey];
            if (mesh) {
                scene.remove(mesh);
                // Material and its map are from cache, not disposed here.
            }
            delete blockMeshes[meshKey]; // Remove from our tracking object
            return brokenBlockId; // Return the ID of the block that was broken
        }
    }
    // console.warn(`World.js: No block to remove at ${x},${y},${z} or out of bounds.`);
    return null; // No block was broken or out of bounds
}
