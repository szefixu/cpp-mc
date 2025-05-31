// Ensure THREE is loaded globally from CDN
if (typeof window.THREE === 'undefined') {
    console.error('main.js: THREE global object not found. Make sure Three.js (CDN) is loaded before this script.');
    document.body.innerHTML = '<div style="font-family: sans-serif; text-align: center; padding: 2em;">' +
                              '<h1 style="color:red;">Error: THREE.js library not loaded.</h1>' +
                              '<p>Please ensure Three.js is included, usually via a script tag in your HTML, before `main.js`.</p>' +
                              '</div>';
    throw new Error("THREE.js not loaded, cannot initialize application.");
}
const THREE = window.THREE; // Use the global THREE object directly

import { PointerLockControls } from './PointerLockControls.js';
import { WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH, PLAYER_AABB_DIMS, GRAVITY, JUMP_STRENGTH } from './config.js';
import { BlockType, getBlockTypeById, ATLAS_NUM_TEXTURES } from './BlockType.js';
import { generateWorld } from './worldGenerator.js';
import { checkCollision } from './physics.js';

console.log("Three.js version (from global):", THREE.REVISION);

let scene, camera, renderer, controls;
let worldData;
const blockMeshes = {};
let atlasTexture;
const blockGeometry = new THREE.BoxGeometry(1, 1, 1);
const materialsCache = {}; // Cache for materials per block type

let playerVelocity = new THREE.Vector3();
let isOnGround = false;
const moveSpeed = 5.0;
const keysPressed = {
    'w': false, 'a': false, 's': false, 'd': false,
    'W': false, 'A': false, 'S': false, 'D': false,
    'ArrowUp': false, 'ArrowLeft': false, 'ArrowDown': false, 'ArrowRight': false,
    ' ': false, 'Spacebar': false
};

let raycaster;
let targetBlockWireframe;
let targetedBlock = null;

const MAX_STACK = 64;
let playerInventory = {};
let hotbarSlots = [
    BlockType.GRASS.id,
    BlockType.DIRT.id,
    BlockType.STONE.id,
    BlockType.WOOD.id,
];
let currentHotbarIndex = 0;

let fpsLastTime = 0;
let frameCount = 0;
let fpsDisplayElement;


function getCurrentPlaceBlockTypeId() {
    if (currentHotbarIndex >= 0 && currentHotbarIndex < hotbarSlots.length) {
        return hotbarSlots[currentHotbarIndex];
    }
    return null;
}

function updateHotbarDisplay() {
    for (let i = 0; i < hotbarSlots.length; i++) {
        const slotElement = document.getElementById(`slot-${i}`);
        if (slotElement) {
            const blockIdInSlot = hotbarSlots[i];
            if (blockIdInSlot === null || blockIdInSlot === undefined) {
                slotElement.innerHTML = `
                    <div class="slot-name">--</div>
                    <div class="slot-quantity">(0)</div>
                `;
            } else {
                const blockType = getBlockTypeById(blockIdInSlot);
                const quantity = playerInventory[blockIdInSlot] || 0;

                slotElement.innerHTML = `
                    <div class="slot-name">${blockType.name ? blockType.name.substring(0,4).toUpperCase() : '??'}</div>
                    <div class="slot-quantity">(${quantity})</div>
                `;
            }

            if (i === currentHotbarIndex) {
                slotElement.classList.add('selected');
            } else {
                slotElement.classList.remove('selected');
            }
        }
    }
}


function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB);

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100.0);
    camera.position.set(WORLD_WIDTH / 2, WORLD_HEIGHT / 2 + 3, WORLD_DEPTH / 2);

    fpsDisplayElement = document.getElementById('fps-counter');
    if (!fpsDisplayElement) {
        console.warn("FPS display element 'fps-counter' not found in HTML.");
    }
    fpsLastTime = performance.now();

    raycaster = new THREE.Raycaster();
    raycaster.far = 7;

    const wireframeGeo = new THREE.BoxGeometry(1.01, 1.01, 1.01);
    const wireframeMat = new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.7 });
    targetBlockWireframe = new THREE.Mesh(wireframeGeo, wireframeMat);
    targetBlockWireframe.visible = false;
    scene.add(targetBlockWireframe);

    worldData = new Array(WORLD_WIDTH);
    for (let x = 0; x < WORLD_WIDTH; x++) {
        worldData[x] = new Array(WORLD_HEIGHT);
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            worldData[x][y] = new Array(WORLD_DEPTH).fill(BlockType.EMPTY.id);
        }
    }
    generateWorld(worldData, BlockType);

    playerInventory[BlockType.GRASS.id] = 20;
    playerInventory[BlockType.DIRT.id] = 20;
    playerInventory[BlockType.STONE.id] = 20;
    playerInventory[BlockType.WOOD.id] = 10;
    playerInventory[BlockType.LEAVES.id] = 5;
    updateHotbarDisplay();

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    renderer.domElement.addEventListener('mousedown', onMouseDown, false);

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
        controls.addEventListener('lock', function () { instructions.style.display = 'none'; blocker.style.display = 'none'; });
        controls.addEventListener('unlock', function () { blocker.style.display = 'block'; instructions.style.display = ''; });
    }
    document.addEventListener('keydown', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) keysPressed[event.key] = true;
        if (event.key === 'Spacebar') keysPressed[' '] = true;
        if ((event.key === ' ' || event.key === 'Spacebar') && controls.isLocked) event.preventDefault();

        if (controls.isLocked) {
            const keyNum = parseInt(event.key);
            if (!isNaN(keyNum) && keyNum >= 1 && keyNum <= hotbarSlots.length) {
                currentHotbarIndex = keyNum - 1;
                updateHotbarDisplay();
            }
        }
    });
    document.addEventListener('keyup', (event) => {
        if (keysPressed.hasOwnProperty(event.key)) keysPressed[event.key] = false;
        if (event.key === 'Spacebar') keysPressed[' '] = false;
    });

    const textureLoader = new THREE.TextureLoader();
    atlasTexture = textureLoader.load(
        'textures/atlas.png',
        () => {
            console.log("Texture atlas loaded for world rendering.");
            if (atlasTexture) {
                 atlasTexture.magFilter = THREE.NearestFilter;
                 atlasTexture.minFilter = THREE.NearestFilter;
            }
            renderWorldFromData(); // Initial world render
            animate();
        },
        undefined,
        (err) => {
            console.error('Error loading texture atlas. Blocks may be untextured or default.', err);
            renderWorldFromData(true); // Render with fallback
            animate();
        }
    );
    window.addEventListener('resize', onWindowResize, false);
}

function renderWorldFromData(textureFailed = false) {
    // Clear existing block meshes from the scene
    for (const key in blockMeshes) {
        scene.remove(blockMeshes[key]);
        // Material and map are from cache, so don't dispose them here.
        // The cache itself would handle disposal if a material type is no longer needed at all.
    }
    for (const prop of Object.getOwnPropertyNames(blockMeshes)) { // Clear the tracking object
        delete blockMeshes[prop];
    }

    let defaultMaterial = materialsCache['default_fallback'];
    if (textureFailed && !defaultMaterial) { // Create default material once if texture failed and not cached
        console.warn("Using default material due to texture atlas issue (first time).");
        defaultMaterial = new THREE.MeshStandardMaterial({ color: 0xcccccc });
        materialsCache['default_fallback'] = defaultMaterial;
    }

    for (let x = 0; x < WORLD_WIDTH; x++) {
        for (let y = 0; y < WORLD_HEIGHT; y++) {
            for (let z = 0; z < WORLD_DEPTH; z++) {
                const blockId = worldData[x][y][z];
                const blockType = getBlockTypeById(blockId);

                if (blockType.id !== BlockType.EMPTY.id && blockType.atlasIndex !== -1) {
                    let materialToUse = materialsCache[blockId];

                    if (!materialToUse) { // Material not in cache yet for this blockId
                        if (textureFailed || !atlasTexture || !atlasTexture.image) {
                            materialToUse = defaultMaterial; // Use the shared default material
                            // No need to cache defaultMaterial under blockId, it's under 'default_fallback'
                        } else {
                            const textureHeightRatio = 1 / ATLAS_NUM_TEXTURES;
                            // Each material *type* gets its own texture clone for offset/repeat
                            const newTextureForMaterial = atlasTexture.clone();
                            newTextureForMaterial.needsUpdate = true;
                            const vOffset = (ATLAS_NUM_TEXTURES - 1 - blockType.atlasIndex) * textureHeightRatio;
                            newTextureForMaterial.offset.set(0, vOffset);
                            newTextureForMaterial.repeat.set(1, textureHeightRatio);

                            materialToUse = new THREE.MeshStandardMaterial({ map: newTextureForMaterial });
                            materialsCache[blockId] = materialToUse; // Cache this new material
                        }
                    }

                    if (materialToUse) {
                        const mesh = new THREE.Mesh(blockGeometry, materialToUse);
                        mesh.position.set(x, y, z);
                        mesh.isWorldBlock = true;
                        scene.add(mesh);
                        blockMeshes[`${x}_${y}_${z}`] = mesh;
                    }
                }
            }
        }
    }
    // console.log("World rendering with cached materials. Meshes:", Object.keys(blockMeshes).length);
}

function addBlock(x, y, z, blockId) {
    if (x < 0 || x >= WORLD_WIDTH || y < 0 || y >= WORLD_HEIGHT || z < 0 || z >= WORLD_DEPTH) {
        console.warn("Attempted to place block out of bounds:", x, y, z);
        return false;
    }
    if (worldData[x][y][z] !== BlockType.EMPTY.id) {
        // console.warn("Attempted to place block in an occupied space:", x, y, z);
        return false;
    }

    worldData[x][y][z] = blockId;
    const blockType = getBlockTypeById(blockId);
    if (blockType.id === BlockType.EMPTY.id || blockType.atlasIndex === -1) {
        console.warn("Attempted to place an invalid block type:", blockType.name);
        return false;
    }

    let materialToUse = materialsCache[blockId];
    if (!materialToUse) { // Material not in cache, create and cache it
        if (!atlasTexture || !atlasTexture.image) { // Texture loading failed or not ready
            materialToUse = materialsCache['default_fallback'] ||
                            (materialsCache['default_fallback'] = new THREE.MeshStandardMaterial({ color: 0x999999 }));
        } else {
            const textureHeightRatio = 1 / ATLAS_NUM_TEXTURES;
            const newTextureForMaterial = atlasTexture.clone();
            newTextureForMaterial.needsUpdate = true;
            const vOffset = (ATLAS_NUM_TEXTURES - 1 - blockType.atlasIndex) * textureHeightRatio;
            newTextureForMaterial.offset.set(0, vOffset);
            newTextureForMaterial.repeat.set(1, textureHeightRatio);
            materialToUse = new THREE.MeshStandardMaterial({ map: newTextureForMaterial });
            materialsCache[blockId] = materialToUse;
        }
    }

    if (materialToUse) {
        const mesh = new THREE.Mesh(blockGeometry, materialToUse);
        mesh.position.set(x, y, z);
        mesh.isWorldBlock = true;
        scene.add(mesh);
        blockMeshes[`${x}_${y}_${z}`] = mesh;
        return true; // Successfully added
    }
    console.warn("Failed to obtain material for block:", blockType.name);
    return false; // Material creation failed
}

function onMouseDown(event) {
    if (!controls.isLocked || !targetedBlock) return;

    const currentPlaceId = getCurrentPlaceBlockTypeId();

    if (event.button === 0) { // Left click - Breaking
        const { mesh } = targetedBlock;
        const x = Math.round(mesh.position.x);
        const y = Math.round(mesh.position.y);
        const z = Math.round(mesh.position.z);

        if (x >= 0 && x < WORLD_WIDTH && y >= 0 && y < WORLD_HEIGHT && z >= 0 && z < WORLD_DEPTH) {
            const brokenBlockId = worldData[x][y][z];
            if (brokenBlockId !== BlockType.EMPTY.id) {
                worldData[x][y][z] = BlockType.EMPTY.id;
                scene.remove(mesh);
                // Material and map are from cache, do not dispose them here.
                delete blockMeshes[`${x}_${y}_${z}`];

                playerInventory[brokenBlockId] = (playerInventory[brokenBlockId] || 0) + 1;
                if (playerInventory[brokenBlockId] > MAX_STACK) playerInventory[brokenBlockId] = MAX_STACK;
                updateHotbarDisplay();
            }
            targetBlockWireframe.visible = false;
            targetedBlock = null;
        }
    } else if (event.button === 2) { // Right click - Placing
        if (currentPlaceId === null || currentPlaceId === BlockType.EMPTY.id) return;
        const currentQuantity = playerInventory[currentPlaceId] || 0;
        if (currentQuantity <= 0) return;

        const { mesh: targetMesh, faceNormal } = targetedBlock;
        const newBlockPos = new THREE.Vector3().copy(targetMesh.position).add(faceNormal);
        const placeX = Math.round(newBlockPos.x);
        const placeY = Math.round(newBlockPos.y);
        const placeZ = Math.round(newBlockPos.z);

        const newBlockAABBMin = new THREE.Vector3(placeX - 0.5, placeY - 0.5, placeZ - 0.5);
        const newBlockAABBMax = new THREE.Vector3(placeX + 0.5, placeY + 0.5, placeZ + 0.5);
        const playerAABBCenter = getPlayerAABBCenter(camera.position);
        const playerAABBMin = new THREE.Vector3(playerAABBCenter.x-PLAYER_AABB_DIMS[0]/2, playerAABBCenter.y-PLAYER_AABB_DIMS[1]/2, playerAABBCenter.z-PLAYER_AABB_DIMS[2]/2);
        const playerAABBMax = new THREE.Vector3(playerAABBCenter.x+PLAYER_AABB_DIMS[0]/2, playerAABBCenter.y+PLAYER_AABB_DIMS[1]/2, playerAABBCenter.z+PLAYER_AABB_DIMS[2]/2);
        const collidesWithPlayer = (newBlockAABBMax.x > playerAABBMin.x && newBlockAABBMin.x < playerAABBMax.x && newBlockAABBMax.y > playerAABBMin.y && newBlockAABBMin.y < playerAABBMax.y && newBlockAABBMax.z > playerAABBMin.z && newBlockAABBMin.z < playerAABBMax.z);

        if (collidesWithPlayer) {
            console.warn("Cannot place block: position would collide with player.");
            return;
        }

        if (addBlock(placeX, placeY, placeZ, currentPlaceId)) {
             playerInventory[currentPlaceId]--;
             updateHotbarDisplay();
        }
    }
}

function getPlayerAABBCenter(cameraPosition) {
    return new THREE.Vector3( cameraPosition.x, cameraPosition.y - PLAYER_AABB_DIMS[1] * 0.4, cameraPosition.z );
}
function getPlayerFeetPosition(cameraPosition) {
    const aabbCenterY = getPlayerAABBCenter(cameraPosition).y;
    return new THREE.Vector3(cameraPosition.x, aabbCenterY - PLAYER_AABB_DIMS[1] / 2, cameraPosition.z);
}

function updateTargetedBlock() {
    if (!raycaster || !camera ) {
        if(targetBlockWireframe) targetBlockWireframe.visible = false;
        targetedBlock = null;
        return;
    }
    if (!controls.isLocked) {
        targetBlockWireframe.visible = false;
        targetedBlock = null;
        return;
    }

    raycaster.setFromCamera({ x: 0, y: 0 }, camera);
    const blockMeshArray = Object.values(blockMeshes);
    if (blockMeshArray.length === 0) {
         targetBlockWireframe.visible = false;
         targetedBlock = null;
         return;
    }
    const intersects = raycaster.intersectObjects(blockMeshArray, false);
    let foundBlockDetails = null;
    if (intersects.length > 0) {
        for (const intersect of intersects) {
            if (intersect.object.isWorldBlock && intersect.distance <= raycaster.far) {
                foundBlockDetails = intersect;
                break;
            }
        }
    }
    if (foundBlockDetails) {
        targetBlockWireframe.position.copy(foundBlockDetails.object.position);
        targetBlockWireframe.visible = true;
        targetedBlock = { mesh: foundBlockDetails.object, point: foundBlockDetails.point, faceNormal: foundBlockDetails.face.normal.clone() };
    } else {
        targetBlockWireframe.visible = false;
        targetedBlock = null;
    }
}

let animationLoopLastTime = performance.now();
function animate(time) {
    requestAnimationFrame(animate);
    const currentTime = time || performance.now();
    let deltaTime = (currentTime - animationLoopLastTime) / 1000;
    animationLoopLastTime = currentTime;
    deltaTime = Math.min(deltaTime, 0.1);

    frameCount++;
    if (fpsDisplayElement && currentTime >= fpsLastTime + 1000) {
        fpsDisplayElement.textContent = `FPS: ${frameCount}`;
        frameCount = 0;
        fpsLastTime = currentTime;
    }

    updateTargetedBlock();

    if (controls.isLocked === true) {
        if (isOnGround && (keysPressed[' '] || keysPressed['Spacebar'])) { playerVelocity.y = JUMP_STRENGTH; isOnGround = false; }
        playerVelocity.y -= GRAVITY * deltaTime;
        const verticalDelta = playerVelocity.y * deltaTime;
        const nextVerticalCameraPos = camera.position.clone(); nextVerticalCameraPos.y += verticalDelta;
        const nextVerticalAABBCenter = getPlayerAABBCenter(nextVerticalCameraPos);
        if (checkCollision(nextVerticalAABBCenter, PLAYER_AABB_DIMS, worldData, BlockType)) {
            if (playerVelocity.y <= 0) {
                const feetPosAtCollision = getPlayerFeetPosition(nextVerticalCameraPos).y;
                const snappedFeetY = Math.floor(feetPosAtCollision + 0.0001) + 1.0;
                const aabbCenterYFromSnappedFeet = snappedFeetY + PLAYER_AABB_DIMS[1] / 2;
                camera.position.y = aabbCenterYFromSnappedFeet + PLAYER_AABB_DIMS[1] * 0.4;
                playerVelocity.y = 0; isOnGround = true;
            } else { playerVelocity.y = 0; }
        } else { camera.position.y += verticalDelta; isOnGround = false; }

        const speed = moveSpeed * deltaTime;
        const worldMoveVector = new THREE.Vector3();
        const forwardVec = new THREE.Vector3(); camera.getWorldDirection(forwardVec); forwardVec.y = 0; forwardVec.normalize();
        const rightVec = new THREE.Vector3(); rightVec.crossVectors(camera.up, forwardVec).normalize();
        let inputMoveX = 0; let inputMoveZ = 0;
        if (keysPressed['w']||keysPressed['W']||keysPressed['ArrowUp']) { inputMoveZ = -1; }
        if (keysPressed['s']||keysPressed['S']||keysPressed['ArrowDown']) { inputMoveZ = 1; }
        if (keysPressed['a']||keysPressed['A']||keysPressed['ArrowLeft']) { inputMoveX = -1; }
        if (keysPressed['d']||keysPressed['D']||keysPressed['ArrowRight']) { inputMoveX = 1; }

        if (inputMoveX !== 0 || inputMoveZ !== 0) {
            worldMoveVector.addScaledVector(forwardVec, inputMoveZ);
            worldMoveVector.addScaledVector(rightVec, inputMoveX);
            worldMoveVector.normalize().multiplyScalar(speed);
            const nextHorizontalPos = camera.position.clone().add(worldMoveVector);
            if (!checkCollision(getPlayerAABBCenter(nextHorizontalPos), PLAYER_AABB_DIMS, worldData, BlockType)) {
                camera.position.add(worldMoveVector);
            } else {
                if (inputMoveX !== 0) {
                    const xOnlyMove = new THREE.Vector3(worldMoveVector.x,0,0);
                    if(xOnlyMove.lengthSq() > 0.000001 && !checkCollision(getPlayerAABBCenter(camera.position.clone().add(xOnlyMove)),PLAYER_AABB_DIMS,worldData,BlockType)) camera.position.add(xOnlyMove);
                }
                if (inputMoveZ !== 0) {
                    const zOnlyMove = new THREE.Vector3(0,0,worldMoveVector.z);
                    if(zOnlyMove.lengthSq() > 0.000001 && !checkCollision(getPlayerAABBCenter(camera.position.clone().add(zOnlyMove)),PLAYER_AABB_DIMS,worldData,BlockType)) camera.position.add(zOnlyMove);
                }
            }
        }
    } else {
        updateTargetedBlock();
        if (!isOnGround) {
            playerVelocity.y -= (GRAVITY / 2) * deltaTime;
            if (playerVelocity.y < -JUMP_STRENGTH) playerVelocity.y = -JUMP_STRENGTH;
            const verticalDelta = playerVelocity.y * deltaTime;
            const nextVCamPos = camera.position.clone(); nextVCamPos.y += verticalDelta;
            if(!checkCollision(getPlayerAABBCenter(nextVCamPos), PLAYER_AABB_DIMS, worldData, BlockType) || verticalDelta > 0) {
                camera.position.y += verticalDelta;
            } else if (verticalDelta < 0) {
                 const feetPosAtCollision = getPlayerFeetPosition(nextVCamPos).y;
                 const snappedFeetY = Math.floor(feetPosAtCollision + 0.0001) + 1.0;
                 const aabbCenterYFromSnappedFeet = snappedFeetY + PLAYER_AABB_DIMS[1] / 2;
                 camera.position.y = aabbCenterYFromSnappedFeet + PLAYER_AABB_DIMS[1] * 0.4;
                 playerVelocity.y = 0;
                 isOnGround = true;
            }
            if (camera.position.y < -20) camera.position.y = -20;
        } else {
            playerVelocity.y = 0;
        }
    }
    renderer.render(scene, camera);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

if (typeof THREE !== 'undefined' && THREE) {
    init();
}
