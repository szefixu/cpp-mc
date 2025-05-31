// Player.js
if (typeof window.THREE === 'undefined') {
    console.error("Player.js: THREE global not found.");
    throw new Error("THREE.js not loaded for Player.js");
}
const THREE = window.THREE; // Ensure THREE is available

export class Player {
    constructor(camera, controls, initialPosition, config, keysPressedRef) {
        this.camera = camera;
        this.controls = controls;
        this.config = config; // { GRAVITY, JUMP_STRENGTH, PLAYER_AABB_DIMS, moveSpeed }

        this.velocity = new THREE.Vector3();
        this.isOnGround = false;
        this.keysPressed = keysPressedRef; // Reference to keysPressed object from main/input handler

        if (initialPosition) {
            this.camera.position.copy(initialPosition);
        } else {
            // Default initial position if none provided, though main.js should provide one
            this.camera.position.set(0, this.config.PLAYER_AABB_DIMS[1] * 0.9, 0);
        }

        // Pre-allocate vectors for performance in update loop
        this.forwardVector = new THREE.Vector3();
        this.rightVector = new THREE.Vector3();
        this.worldMoveVector = new THREE.Vector3();
        this.nextVerticalCameraPos = new THREE.Vector3();
        this.xOnlyMove = new THREE.Vector3();
        this.zOnlyMove = new THREE.Vector3();
    }

    getPlayerAABBCenter(cameraPosition) {
        // Assumes cameraPosition is the eye level of the player
        // Player AABB center Y = camera Y - PlayerHeight * (eyeHeightRatio - 0.5)
        // Where eyeHeightRatio is how far up the AABB the eyes are (e.g., 0.9 for 90% up from bottom)
        // AABB_Center_Y = camera.y - PLAYER_AABB_DIMS[1] * (0.9 - 0.5)
        // AABB_Center_Y = camera.y - PLAYER_AABB_DIMS[1] * 0.4
        return new THREE.Vector3(
            cameraPosition.x,
            cameraPosition.y - this.config.PLAYER_AABB_DIMS[1] * 0.4,
            cameraPosition.z
        );
    }

    update(deltaTime, worldDataRef, BlockTypeRef, checkCollisionFunc) {
        if (!this.controls.isLocked) {
            if (!this.isOnGround && this.velocity.y < 0) { // Only apply gravity if falling and unlocked
                this.velocity.y -= (this.config.GRAVITY / 2) * deltaTime;
                // Terminal velocity for unlocked state
                if (this.velocity.y < -this.config.JUMP_STRENGTH) {
                    this.velocity.y = -this.config.JUMP_STRENGTH;
                }

                const verticalDelta = this.velocity.y * deltaTime;
                this.nextVerticalCameraPos.copy(this.camera.position);
                this.nextVerticalCameraPos.y += verticalDelta;

                if(!checkCollisionFunc(this.getPlayerAABBCenter(this.nextVerticalCameraPos), this.config.PLAYER_AABB_DIMS, worldDataRef, BlockTypeRef)) {
                    this.camera.position.y += verticalDelta;
                } else if (verticalDelta < 0) { // Hit something while falling unlocked
                    // Simplified snap to ground for unlocked state
                    const feetAtCollision = this.getPlayerAABBCenter(this.nextVerticalCameraPos).y - this.config.PLAYER_AABB_DIMS[1] / 2;
                    const snappedFeetY = Math.floor(feetAtCollision + 0.0001) + 1.0;
                    const snappedAABBCenterY = snappedFeetY + this.config.PLAYER_AABB_DIMS[1] / 2;
                    this.camera.position.y = snappedAABBCenterY + this.config.PLAYER_AABB_DIMS[1] * 0.4; // Back to eye level
                    this.velocity.y = 0;
                    this.isOnGround = true;
                }
                // Crude boundary check
                if (this.camera.position.y < -20) this.camera.position.y = -20;
            } else if (this.isOnGround) {
                this.velocity.y = 0; // Ensure no residual velocity if on ground and unlocked
            }
            return; // No further movement updates if not locked
        }

        // --- Vertical Movement (Gravity and Jump) ---
        if (this.isOnGround && (this.keysPressed[' '] || this.keysPressed['Spacebar'])) {
            this.velocity.y = this.config.JUMP_STRENGTH;
            this.isOnGround = false;
        }

        this.velocity.y -= this.config.GRAVITY * deltaTime;
        const verticalDelta = this.velocity.y * deltaTime;

        this.nextVerticalCameraPos.copy(this.camera.position);
        this.nextVerticalCameraPos.y += verticalDelta;
        const nextVerticalAABBCenter = this.getPlayerAABBCenter(this.nextVerticalCameraPos);

        if (checkCollisionFunc(nextVerticalAABBCenter, this.config.PLAYER_AABB_DIMS, worldDataRef, BlockTypeRef)) {
            if (this.velocity.y <= 0) { // Falling or on ground and tried to move down
                const feetPosAtCollision = this.getPlayerAABBCenter(this.nextVerticalCameraPos).y - this.config.PLAYER_AABB_DIMS[1] / 2;
                const snappedFeetY = Math.floor(feetPosAtCollision + 0.0001) + 1.0; // Ensure slightly above block
                const aabbCenterYFromSnappedFeet = snappedFeetY + this.config.PLAYER_AABB_DIMS[1] / 2;
                this.camera.position.y = aabbCenterYFromSnappedFeet + this.config.PLAYER_AABB_DIMS[1] * 0.4; // Back to eye level
                this.velocity.y = 0;
                this.isOnGround = true;
            } else { // Moving upwards and hit something (ceiling)
                this.velocity.y = 0;
                // Optionally snap to ceiling, for now just stop.
            }
        } else {
            this.camera.position.y += verticalDelta;
            this.isOnGround = false; // In the air
        }

        // --- Horizontal Movement ---
        const speed = this.config.moveSpeed * deltaTime;
        this.worldMoveVector.set(0,0,0); // Reset move vector

        this.camera.getWorldDirection(this.forwardVector);
        this.forwardVector.y = 0;
        this.forwardVector.normalize();

        this.rightVector.crossVectors(this.camera.up, this.forwardVector).normalize();

        let inputMoveX = 0;
        let inputMoveZ = 0;

        if (this.keysPressed['w']||this.keysPressed['W']||this.keysPressed['ArrowUp']) inputMoveZ = -1;
        if (this.keysPressed['s']||this.keysPressed['S']||this.keysPressed['ArrowDown']) inputMoveZ = 1;
        if (this.keysPressed['a']||this.keysPressed['A']||this.keysPressed['ArrowLeft']) inputMoveX = -1;
        if (this.keysPressed['d']||this.keysPressed['D']||this.keysPressed['ArrowRight']) inputMoveX = 1;

        if (inputMoveX !== 0 || inputMoveZ !== 0) {
            this.worldMoveVector.addScaledVector(this.forwardVector, inputMoveZ);
            this.worldMoveVector.addScaledVector(this.rightVector, inputMoveX);

            this.worldMoveVector.normalize().multiplyScalar(speed); // Normalize after combining, then scale

            const nextHorizontalPos = this.camera.position.clone().add(this.worldMoveVector);
            const nextHorizontalAABBCenter = this.getPlayerAABBCenter(nextHorizontalPos);

            if (!checkCollisionFunc(nextHorizontalAABBCenter, this.config.PLAYER_AABB_DIMS, worldDataRef, BlockTypeRef)) {
                this.camera.position.add(this.worldMoveVector);
            } else {
                // Sliding logic
                if (inputMoveX !== 0) {
                    this.xOnlyMove.set(this.worldMoveVector.x,0,0);
                    if(this.xOnlyMove.lengthSq() > 0.000001 && !checkCollisionFunc(this.getPlayerAABBCenter(this.camera.position.clone().add(this.xOnlyMove)),this.config.PLAYER_AABB_DIMS,worldDataRef,BlockTypeRef)) {
                        this.camera.position.add(this.xOnlyMove);
                    }
                }
                if (inputMoveZ !== 0) {
                    this.zOnlyMove.set(0,0,this.worldMoveVector.z);
                    // Check against current camera position, which might have been updated by X-only move
                    if(this.zOnlyMove.lengthSq() > 0.000001 && !checkCollisionFunc(this.getPlayerAABBCenter(this.camera.position.clone().add(this.zOnlyMove)),this.config.PLAYER_AABB_DIMS,worldDataRef,BlockTypeRef)) {
                        this.camera.position.add(this.zOnlyMove);
                    }
                }
            }
        }
    }
}
