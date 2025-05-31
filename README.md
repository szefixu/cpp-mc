# PyVoxel Engine

A simple voxel sandbox game written in Python, Pygame, and PyOpenGL, demonstrating basic 3D rendering and interaction in a block-based world.

## Current Features

*   Basic voxel world: Place and remove blocks of different types.
*   Player movement: Standard WASD for horizontal movement, mouse for looking, Space to jump.
*   Block Textures: Distinct colors for different block types (Grass, Dirt, Stone, Wood, Leaves).
*   Hotbar: Select different block types for placement.
*   Raycasting: Accurate block selection for interaction.
*   Performance Optimizations:
    *   Frustum Culling: Only renders blocks within the camera's view.
*   Visual Enhancements:
    *   Vertex-based Ambient Occlusion: Adds depth and shading to block corners.
    *   FPS Counter: Displays current frames per second.
*   Modular Code Structure: Recently refactored for better organization.

## How to Run

### Dependencies

*   Python 3.x
*   Pygame (`pip install pygame`)
*   PyOpenGL (`pip install PyOpenGL PyOpenGL_accelerate`)
*   NumPy (`pip install numpy`)
*   Pillow (`pip install Pillow`) (used by a script to generate textures, and for texture loading)

### Command

To run the game, navigate to the project's root directory in your terminal and execute:

```bash
python main.py
```

## Planned Improvements

*   Further code refactoring (e.g., class-based entity system).
*   Advanced rendering techniques using shaders (GLSL) for better lighting and effects.
*   More complex and diverse world generation.
*   Expanded inventory and crafting systems.