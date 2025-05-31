// main.js (Refactored)
// Ensure THREE is loaded
if (typeof window.THREE === 'undefined') {
    document.body.innerHTML = '<div style="font-family: sans-serif; text-align: center; padding: 2em;">' +
                              '<h1 style="color:red;">Error: THREE.js library not loaded.</h1>' +
                              '<p>Please ensure Three.js is included, usually via a script tag in your HTML, before `main.js`.</p>' +
                              '</div>';
    throw new Error("THREE.js not loaded");
}
const THREE = window.THREE;

import { PointerLockControls } from './PointerLockControls.js';
import *  as GameConfig from './config.js'; // Using all exports from config.js
import { BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES } from './BlockType.js';
import { checkCollision } from './physics.js'; // Still needed by Player via main

import * as World from './World.js'; // Import World module (World.worldData, World.blockMeshes, etc.)
import { Player } from './Player.js'; // Import Player class

console.log("Three.js version (from global):", THREE.REVISION);

// --- Global/Module Variables for main.js ---
let scene, camera, renderer, controls;
let player; // Player instance
const blockGeometry = new THREE.BoxGeometry(1, 1, 1); // Shared geometry for blocks
let atlasTexture; // Loaded atlas texture

// UI and Inventory State (candidates for UI.js)
const MAX_STACK = 64;
let playerInventory = {};
let hotbarSlots = [
    BlockType.GRASS.id,
    BlockType.DIRT.id,
    BlockType.STONE.id,
    BlockType.WOOD.id
];
let currentHotbarIndex = 0;

// Input State (passed to Player instance, updated by listeners in main.js)
const keysPressed = {
    'w': false, 'a': false, 's': false, 'd': false, 'W': false, 'A': false, 'S': false, 'D': false,
    'ArrowUp': false, 'ArrowLeft': false, 'ArrowDown': false, 'ArrowRight': false,
    ' ': false, 'Spacebar': false
};

// Targeting State (candidate for Targeting.js or similar)
let raycaster, targetBlockWireframe, targetedBlock = null;

// FPS Counter State (candidate for UI.js)
let fpsLastTime = 0, frameCount = 0, fpsDisplayElement;


function getCurrentPlaceBlockTypeId() {
    if (currentHotbarIndex >= 0 && currentHotbarIndex < hotbarSlots.length) {
        return hotbarSlots[currentHotbarIndex];
    }
    return null;
}

function updateHotbarDisplay() {
    hotbarSlots.forEach((slotBlockId, i) => {
        const slotElement = document.getElementById(`slot-${i}`);
        if(slotElement) {
            let name = '--';
            let quantity = 0;
            if (slotBlockId !== null && slotBlockId !== undefined) {
                const blockType = getBlockTypeById(slotBlockId);
                name = blockType.name ? blockType.name.substring(0,4).toUpperCase() : '??';
                quantity = playerInventory[slotBlockId] || 0;
            }
            slotElement.innerHTML = `<div class="slot-name">${name}</div><div class="slot-quantity">(${quantity})</div>`;
            if (i === currentHotbarIndex) slotElement.classList.add('selected');
            else slotElement.classList.remove('selected');
        }
    });
}


function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB);
    camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 100.0);

    World.initWorld(BlockType); // Initialize worldData and generate terrain

    const playerInitialPos = new THREE.Vector3(GameConfig.WORLD_WIDTH/2, GameConfig.WORLD_HEIGHT + 5, GameConfig.WORLD_DEPTH/2); // Start higher to fall
    const playerConfig = {
        GRAVITY: GameConfig.GRAVITY,
        JUMP_STRENGTH: GameConfig.JUMP_STRENGTH,
        PLAYER_AABB_DIMS: GameConfig.PLAYER_AABB_DIMS,
        moveSpeed: 5.0 // moveSpeed defined here for Player
    };
    // PointerLockControls now takes document.body instead of renderer.domElement for wider compatibility
    controls = new PointerLockControls(camera, document.body);
    player = new Player(camera, controls, playerInitialPos, playerConfig, keysPressed);

    raycaster = new THREE.Raycaster(); raycaster.far = 7;
    const wireframeGeo = new THREE.BoxGeometry(1.01,1.01,1.01);
    const wireframeMat = new THREE.MeshBasicMaterial({color:0x000000, wireframe:true, transparent:true, opacity:0.7});
    targetBlockWireframe = new THREE.Mesh(wireframeGeo, wireframeMat);
    targetBlockWireframe.visible = false; scene.add(targetBlockWireframe);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);
    renderer.domElement.addEventListener('mousedown', onMouseDown, false);

    const ambientLight = new THREE.AmbientLight(0xffffff,0.6); scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff,0.8);
    directionalLight.position.set(GameConfig.WORLD_WIDTH,GameConfig.WORLD_HEIGHT*1.5,GameConfig.WORLD_DEPTH); scene.add(directionalLight);

    fpsDisplayElement = document.getElementById('fps-counter'); fpsLastTime = performance.now();
    playerInventory = {
        [BlockType.GRASS.id]:20, [BlockType.DIRT.id]:20, [BlockType.STONE.id]:20, [BlockType.WOOD.id]:10,
        [BlockType.LEAVES.id]:5
    };
    updateHotbarDisplay();

    const blocker = document.getElementById('blocker');
    const instructions = document.getElementById('instructions');
    if (instructions && blocker) {
        instructions.addEventListener('click', () => controls.lock());
        controls.addEventListener('lock', () => { instructions.style.display = 'none'; blocker.style.display = 'none'; });
        controls.addEventListener('unlock', () => { blocker.style.display = 'block'; instructions.style.display = ''; });
    }
    document.addEventListener('keydown', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) keysPressed[event.key] = true;
        if (event.key === 'Spacebar') keysPressed[' '] = true;
        if ((event.key === ' ' || event.key === 'Spacebar') && controls.isLocked) event.preventDefault();
        if (controls.isLocked) {
            const keyNum = parseInt(event.key);
            if (!isNaN(keyNum) && keyNum >= 1 && keyNum <= hotbarSlots.length) {
                currentHotbarIndex = keyNum - 1; updateHotbarDisplay();
            }
        }
    });
    document.addEventListener('keyup', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) keysPressed[event.key] = false;
        if (event.key === 'Spacebar') keysPressed[' '] = false;
    });

    window.addEventListener('resize', onWindowResize, false);

    const textureLoader = new THREE.TextureLoader();
    atlasTexture = textureLoader.load('textures/atlas.png',
        () => {
            console.log("main.js: Atlas texture loaded.");
            if(atlasTexture) { atlasTexture.magFilter = THREE.NearestFilter; atlasTexture.minFilter = THREE.NearestFilter; }
            // Pass necessary refs to World.renderWorld
            World.renderWorld(scene, blockGeometry, atlasTexture, BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES);
            animate(); // Start animation loop AFTER textures and initial world render
        },
        undefined,
        (err) => {
            console.error('main.js: Error loading texture atlas.', err);
            // Render world with null texture (will use fallback in World.js)
            World.renderWorld(scene, blockGeometry, null, BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES);
            animate(); // Still start animation loop
        }
    );
}

function onMouseDown(event) {
    if (!controls.isLocked || !targetedBlock) return;
    const currentPlaceId = getCurrentPlaceBlockTypeId();

    if (event.button === 0) { // Breaking
        const { mesh } = targetedBlock;
        const x=Math.round(mesh.position.x), y=Math.round(mesh.position.y), z=Math.round(mesh.position.z);
        // Use World.removeBlockFromWorld
        const brokenBlockId = World.removeBlockFromWorld(x,y,z, scene, BlockType);
        if (brokenBlockId !== null) { // Check if a block was actually broken
            playerInventory[brokenBlockId] = (playerInventory[brokenBlockId] || 0) + 1;
            if (playerInventory[brokenBlockId] > MAX_STACK) playerInventory[brokenBlockId] = MAX_STACK;
            updateHotbarDisplay();
        }
        targetBlockWireframe.visible = false; targetedBlock = null;
    } else if (event.button === 2) { // Placing
        if (currentPlaceId === null || currentPlaceId === BlockType.EMPTY.id) return;
        if ((playerInventory[currentPlaceId] || 0) <= 0) {
            console.log(`No ${getBlockTypeById(currentPlaceId).name} in inventory.`);
            return;
        }

        const { faceNormal, mesh: targetMesh } = targetedBlock;
        const newBlockPos = new THREE.Vector3().copy(targetMesh.position).add(faceNormal); // Use add, not addScaledVector here
        const placeX=Math.round(newBlockPos.x), placeY=Math.round(newBlockPos.y), placeZ=Math.round(newBlockPos.z);

        // Player collision check for placing
        const tempBlockAABBMin = new THREE.Vector3(placeX-0.5, placeY-0.5, placeZ-0.5);
        const tempBlockAABBMax = new THREE.Vector3(placeX+0.5, placeY+0.5, placeZ+0.5);
        const playerAABBCenter = player.getPlayerAABBCenter(camera.position); // Use player method
        const pDims = player.config.PLAYER_AABB_DIMS;
        const pAABBMin = new THREE.Vector3(playerAABBCenter.x-pDims[0]/2, playerAABBCenter.y-pDims[1]/2, playerAABBCenter.z-pDims[2]/2);
        const pAABBMax = new THREE.Vector3(playerAABBCenter.x+pDims[0]/2, playerAABBCenter.y+pDims[1]/2, playerAABBCenter.z+pDims[2]/2);

        if(tempBlockAABBMax.x > pAABBMin.x && tempBlockAABBMin.x < pAABBMax.x &&
           tempBlockAABBMax.y > pAABBMin.y && tempBlockAABBMin.y < pAABBMax.y &&
           tempBlockAABBMax.z > pAABBMin.z && tempBlockAABBMin.z < pAABBMax.z){
            console.warn("Cannot place block: collides with player."); return;
        }

        // Use World.addBlockToWorld
        if (World.addBlockToWorld(placeX,placeY,placeZ, currentPlaceId, scene, blockGeometry, atlasTexture, BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES)) {
            playerInventory[currentPlaceId]--; updateHotbarDisplay();
        }
    }
}

function updateTargetedBlock() {
    if (!raycaster || !camera || !controls.isLocked) {
        if(targetBlockWireframe) targetBlockWireframe.visible = false;
        targetedBlock = null; return;
    }
    raycaster.setFromCamera({ x: 0, y: 0 }, camera);
    const blockMeshArray = Object.values(World.blockMeshes); // Use World.blockMeshes
    if (blockMeshArray.length === 0) {
        if(targetBlockWireframe) targetBlockWireframe.visible = false;
        targetedBlock = null; return;
    }
    const intersects = raycaster.intersectObjects(blockMeshArray, false);
    let foundBlockDetails = null;
    if (intersects.length > 0) {
        for (const intersect of intersects) {
            if (intersect.object.isWorldBlock && intersect.distance <= raycaster.far) {
                foundBlockDetails = intersect; break;
            }
        }
    }
    if (foundBlockDetails) {
        targetBlockWireframe.position.copy(foundBlockDetails.object.position);
        targetBlockWireframe.visible = true;
        targetedBlock = { mesh: foundBlockDetails.object, point: foundBlockDetails.point, faceNormal: foundBlockDetails.face.normal.clone() };
    } else {
        if(targetBlockWireframe) targetBlockWireframe.visible = false;
        targetedBlock = null;
    }
}

let animationLoopLastTime = performance.now();
function animate(time) {
    requestAnimationFrame(animate);
    const currentTime = time || performance.now();
    let deltaTime = (currentTime - animationLoopLastTime) / 1000;
    animationLoopLastTime = currentTime;
    deltaTime = Math.min(deltaTime, 0.1); // Clamp deltaTime

    frameCount++;
    if (fpsDisplayElement && currentTime >= fpsLastTime + 1000) {
        fpsDisplayElement.textContent = `FPS: ${frameCount}`; frameCount = 0; fpsLastTime = currentTime;
    }

    updateTargetedBlock(); // Update targeted block

    if (player) { // Ensure player is initialized
        // Pass World.worldData and checkCollision (from physics.js) to player.update
        player.update(deltaTime, World.worldData, BlockType, checkCollision);
    }

    renderer.render(scene, camera);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

init(); // Start the application
