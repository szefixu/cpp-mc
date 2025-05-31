// Main JavaScript file for the Minecraft clone
import * as THREE from 'three';
import { PointerLockControls } from './PointerLockControls.js';
import { WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH, PLAYER_AABB_DIMS, GRAVITY, JUMP_STRENGTH } from './config.js';
import { BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES } from './BlockType.js';
import { generateWorld } from './worldGenerator.js';
import { checkCollision } from './physics.js';

// Ensure Three.js is loaded
if (typeof THREE === 'undefined') {
    console.error("Three.js has not been loaded. Please include it in your HTML or check import.");
} else {
    console.log("Three.js version:", THREE.REVISION);
}

let scene, camera, renderer, controls;
let worldData;
const blockMeshes = {};
let atlasTexture;

const blockGeometry = new THREE.BoxGeometry(1, 1, 1);

// Player state variables
let playerVelocity = new THREE.Vector3(); // Initialize player velocity
let isOnGround = false;

const moveSpeed = 5.0; // Units per second
const keysPressed = {
    'w': false, 'a': false, 's': false, 'd': false,
    'W': false, 'A': false, 'S': false, 'D': false,
    'ArrowUp': false, 'ArrowLeft': false, 'ArrowDown': false, 'ArrowRight': false,
    ' ': false, // Spacebar for jump
    'Spacebar': false // Some browsers might report "Spacebar"
};

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB);

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100.0);
    // Initial camera Y position needs to allow space to fall to ground if starting mid-air
    // Let's set it a bit above the center of the world height to demonstrate gravity.
    camera.position.set(WORLD_WIDTH / 2, WORLD_HEIGHT / 2 + 3, WORLD_DEPTH / 2);


    worldData = new Array(WORLD_WIDTH);
    for (let x = 0; x < WORLD_WIDTH; x++) {
        worldData[x] = new Array(WORLD_HEIGHT);
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            worldData[x][y] = new Array(WORLD_DEPTH).fill(BlockType.EMPTY.id);
        }
    }
    generateWorld(worldData, BlockType);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(WORLD_WIDTH, WORLD_HEIGHT * 1.5, WORLD_DEPTH);
    scene.add(directionalLight);

    controls = new PointerLockControls(camera, renderer.domElement);
    const blocker = document.getElementById('blocker');
    const instructions = document.getElementById('instructions');
    if (instructions && blocker) {
        instructions.addEventListener('click', function () { controls.lock(); });
        controls.addEventListener('lock', function () {
            instructions.style.display = 'none';
            blocker.style.display = 'none';
        });
        controls.addEventListener('unlock', function () {
            blocker.style.display = 'block';
            instructions.style.display = '';
        });
    }

    document.addEventListener('keydown', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) {
            keysPressed[event.key] = true;
        }
        // Map "Spacebar" to " " for consistency if browser reports it differently
        if (event.key === 'Spacebar') {
            keysPressed[' '] = true;
        }
        // Prevent spacebar from scrolling the page if controls are active
        if (event.key === ' ' && controls.isLocked) {
            event.preventDefault();
        }
    });
    document.addEventListener('keyup', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) {
            keysPressed[event.key] = false;
        }
        if (event.key === 'Spacebar') {
            keysPressed[' '] = false;
        }
    });

    const textureLoader = new THREE.TextureLoader();
    atlasTexture = textureLoader.load(
        'textures/atlas.png',
        () => {
            console.log("Texture atlas loaded.");
            if (atlasTexture) {
                atlasTexture.magFilter = THREE.NearestFilter;
                atlasTexture.minFilter = THREE.NearestFilter;
            }
            renderWorldFromData();
            animate();
        },
        undefined,
        (err) => {
            console.error('Error loading texture atlas:', err);
            renderWorldFromData();
            animate();
        }
    );

    window.addEventListener('resize', onWindowResize, false);
}

function getPlayerAABBCenter(cameraPosition) {
    return new THREE.Vector3(
        cameraPosition.x,
        cameraPosition.y - (PLAYER_AABB_DIMS[1] / 2) + (PLAYER_AABB_DIMS[1] * 0.1),
        cameraPosition.z
    );
}

function getPlayerFeetPosition(cameraPosition) {
    const aabbCenterY = getPlayerAABBCenter(cameraPosition).y;
    return new THREE.Vector3(cameraPosition.x, aabbCenterY - PLAYER_AABB_DIMS[1] / 2, cameraPosition.z);
}


let lastTime = performance.now();
function animate(time) {
    requestAnimationFrame(animate);
    const currentTime = time || performance.now();
    let deltaTime = (currentTime - lastTime) / 1000;
    lastTime = currentTime;
    deltaTime = Math.min(deltaTime, 0.1); // Clamp deltaTime to prevent large jumps

    if (controls.isLocked === true) {
        // --- Vertical Movement (Gravity and Jump) ---
        if (isOnGround && (keysPressed[' '] || keysPressed['Spacebar'])) {
            playerVelocity.y = JUMP_STRENGTH;
            isOnGround = false;
        }

        playerVelocity.y -= GRAVITY * deltaTime;
        const verticalDelta = playerVelocity.y * deltaTime;

        const tempNextCameraPos = camera.position.clone();
        tempNextCameraPos.y += verticalDelta;
        const nextVerticalAABBCenter = getPlayerAABBCenter(tempNextCameraPos);

        if (checkCollision(nextVerticalAABBCenter, PLAYER_AABB_DIMS, worldData, BlockType)) {
            if (playerVelocity.y <= 0) { // Falling or on ground and tried to move down
                // Player hit the ground. Attempt to snap.
                // The goal is to place player's feet exactly on top of the block they landed on.
                // AABB_feet_Y = Math.floor(AABB_feet_Y_after_potential_move)
                // AABB_center_Y = AABB_feet_Y + PLAYER_AABB_DIMS[1]/2
                // Camera_Y = AABB_center_Y + PLAYER_AABB_DIMS[1]/2 - eyeOffset (0.1 * H)
                const feetAtCollision = getPlayerFeetPosition(tempNextCameraPos).y;
                const snappedFeetY = Math.floor(feetAtCollision + 0.0001) +1; // +1 to be on top of the block hit. Add epsilon for flooring.

                const snappedAABBCenterY = snappedFeetY + PLAYER_AABB_DIMS[1] / 2;
                camera.position.y = snappedAABBCenterY + (PLAYER_AABB_DIMS[1] / 2) - (PLAYER_AABB_DIMS[1] * 0.1);

                playerVelocity.y = 0;
                isOnGround = true;
            } else { // Moving upwards and hit something (ceiling)
                playerVelocity.y = 0;
                // Optionally snap to ceiling, similar to ground. For now, just stop.
            }
        } else {
            camera.position.y += verticalDelta;
            isOnGround = false; // In the air
        }

        // --- Horizontal Movement ---
        const currentSpeed = moveSpeed * deltaTime; // Renamed from 'speed' to avoid conflict
        const worldMoveVector = new THREE.Vector3();

        const forward = new THREE.Vector3();
        camera.getWorldDirection(forward);
        forward.y = 0;
        forward.normalize();

        const right = new THREE.Vector3();
        right.crossVectors(camera.up, forward).normalize();

        let inputMoveX = 0;
        let inputMoveZ = 0;

        if (keysPressed['w'] || keysPressed['W'] || keysPressed['ArrowUp']) inputMoveZ = -1;
        if (keysPressed['s'] || keysPressed['S'] || keysPressed['ArrowDown']) inputMoveZ = 1;
        if (keysPressed['a'] || keysPressed['A'] || keysPressed['ArrowLeft']) inputMoveX = -1;
        if (keysPressed['d'] || keysPressed['D'] || keysPressed['ArrowRight']) inputMoveX = 1;

        if (inputMoveX !== 0 || inputMoveZ !== 0) {
            worldMoveVector.addScaledVector(forward, inputMoveZ); // Note: inputMoveZ is -1 for W, 1 for S
            worldMoveVector.addScaledVector(right, inputMoveX);   // Note: inputMoveX is -1 for A, 1 for D

            worldMoveVector.normalize().multiplyScalar(currentSpeed);

            const nextHorizontalPos = camera.position.clone().add(worldMoveVector);
            const nextHorizontalAABBCenter = getPlayerAABBCenter(nextHorizontalPos);

            if (!checkCollision(nextHorizontalAABBCenter, PLAYER_AABB_DIMS, worldData, BlockType)) {
                camera.position.add(worldMovevector);
            } else {
                // Sliding logic: test X and Z components separately
                const xOnlyMove = new THREE.Vector3(worldMoveVector.x, 0, 0);
                if (inputMoveX !== 0 && xOnlyMove.lengthSq() > 0.00001) {
                    const nextXPos = camera.position.clone().add(xOnlyMove);
                    if (!checkCollision(getPlayerAABBCenter(nextXPos), PLAYER_AABB_DIMS, worldData, BlockType)) {
                        camera.position.add(xOnlyMove);
                    }
                }

                // Test Z against potentially X-modified position
                const zOnlyMove = new THREE.Vector3(0, 0, worldMoveVector.z);
                if (inputMoveZ !== 0 && zOnlyMove.lengthSq() > 0.00001) {
                    const nextZPos = camera.position.clone().add(zOnlyMove); // Use current camera pos
                    if (!checkCollision(getPlayerAABBCenter(nextZPos), PLAYER_AABB_DIMS, worldData, BlockType)) {
                        camera.position.add(zOnlyMove);
                    }
                }
            }
        }
    } else {
        if (!isOnGround && playerVelocity.y < 0) { // If not locked and falling
             // Apply some gravity so player doesn't float if they unlock mid-air
            playerVelocity.y -= (GRAVITY / 2) * deltaTime;
            const verticalDeltaWhenUnlocked = playerVelocity.y * deltaTime;
            const tempNextCamPosUnlocked = camera.position.clone();
            tempNextCamPosUnlocked.y += verticalDeltaWhenUnlocked;
            const nextVertAABBCenterUnlocked = getPlayerAABBCenter(tempNextCamPosUnlocked);

            if (!checkCollision(nextVertAABBCenterUnlocked, PLAYER_AABB_DIMS, worldData, BlockType)) {
                camera.position.y += verticalDeltaWhenUnlocked;
            } else {
                // Simplified snap/stop for unlocked state
                 const feetAtCollision = getPlayerFeetPosition(tempNextCamPosUnlocked).y;
                 const snappedFeetY = Math.floor(feetAtCollision + 0.0001) +1;
                 const snappedAABBCenterY = snappedFeetY + PLAYER_AABB_DIMS[1] / 2;
                 camera.position.y = snappedAABBCenterY + (PLAYER_AABB_DIMS[1] / 2) - (PLAYER_AABB_DIMS[1] * 0.1);
                 playerVelocity.y = 0;
                 isOnGround = true; // Effectively landed
            }
        } else if (isOnGround) {
            playerVelocity.y = 0; // Ensure no residual velocity if on ground and unlocked
        }
    }
    renderer.render(scene, camera);
}

function renderWorldFromData() {
    if (!atlasTexture || !atlasTexture.image) {
        console.warn("Atlas texture or its image not loaded yet for renderWorldFromData.");
    }
    console.log("Rendering world from worldData using texture atlas...");
    const textureHeightRatio = 1 / ATLAS_NUM_TEXTURES;

    for (let x = 0; x < WORLD_WIDTH; x++) {
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            for (let z = 0; z < WORLD_DEPTH; z++) {
                const blockId = worldData[x][y][z];
                const blockType = getBlockTypeById(blockId);

                if (blockType.id !== BlockType.EMPTY.id && blockType.atlasIndex !== -1) {
                    let materialMap = null;
                    if (atlasTexture && atlasTexture.image) {
                        materialMap = atlasTexture.clone();
                        materialMap.needsUpdate = true;
                        const vOffset = (ATLAS_NUM_TEXTURES - 1 - blockType.atlasIndex) * textureHeightRatio;
                        materialMap.offset.set(0, vOffset);
                        materialMap.repeat.set(1, textureHeightRatio);
                    }
                    const blockMaterial = new THREE.MeshStandardMaterial({ map: materialMap });

                    const mesh = new THREE.Mesh(blockGeometry, blockMaterial);
                    mesh.position.set(x, y, z);
                    scene.add(mesh);
                    blockMeshes[`${x}_${y}_${z}`] = mesh;
                }
            }
        }
    }
    console.log("World rendering with atlas complete. Meshes:", Object.keys(blockMeshes).length);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

if (typeof THREE !== 'undefined') {
    init();
} else {
    const blocker = document.getElementById('blocker');
    const instructions = document.getElementById('instructions');
    if (instructions && blocker) {
        instructions.innerHTML = '<p style="color:red; font-size:20px;">Error: THREE.js library not loaded correctly.<br/>Please check the console for errors.</p>';
        blocker.style.backgroundColor = 'rgba(255,255,255,0.9)';
    }
    console.error("THREE is undefined at init call");
}
