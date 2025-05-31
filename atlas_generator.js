// JavaScript snippet to generate a 5-color vertical strip texture atlas (16x80)
// and output its base64 data URL.

function generateAtlas() {
    const canvasWidth = 16;
    const canvasHeight = 80;
    const textureBlockHeight = 16; // Each texture is 16x16

    const colors = [
        'green',       // Index 0 (Top, for GRASS)
        'brown',       // Index 1 (for DIRT)
        'gray',        // Index 2 (for STONE)
        'saddlebrown', // Index 3 (for WOOD)
        'darkgreen'    // Index 4 (Bottom, for LEAVES)
    ];

    // Create an offscreen canvas
    const canvas = document.createElement('canvas');
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    const ctx = canvas.getContext('2d');

    if (!ctx) {
        console.error("Could not get 2D context from canvas. This script might not work in this environment.");
        return;
    }

    // Draw each colored block
    colors.forEach((color, index) => {
        ctx.fillStyle = color;
        const yPosition = index * textureBlockHeight;
        ctx.fillRect(0, yPosition, canvasWidth, textureBlockHeight);
    });

    // Get the data URL
    const dataURL = canvas.toDataURL('image/png');

    // Output the data URL and instructions
    console.log('--- Generated Texture Atlas ---');
    console.log('Your data URL is: ' + dataURL);
    console.log('');
    console.log('To save this atlas:');
    console.log('1. Most modern browser consoles will display the data URL as a link or show an image preview.');
    console.log('2. Right-click the link or the image preview.');
    console.log('3. Select "Save Image As..." (or similar option).');
    console.log('4. Save the file as "atlas.png" into the "textures/" directory of your project.');
    console.log('--- End of Atlas Generation ---');

    // For easier testing, you can also display the image on the current page (if run in a browser)
    // const img = document.createElement('img');
    // img.src = dataURL;
    // img.style.border = "1px solid black";
    // img.style.width = (canvasWidth * 5) + "px"; // Magnify for better viewing
    // img.style.height = (canvasHeight * 5) + "px";
    // img.style.imageRendering = "pixelated"; // Keep it sharp
    // document.body.prepend(img); // Add to top of body
    // const p = document.createElement('p');
    // p.textContent = "Generated Atlas Preview (magnified 5x):";
    // document.body.prepend(p);
}

// Immediately call the function if this script is run standalone.
// If pasting into a console, you can just call generateAtlas();
generateAtlas();
