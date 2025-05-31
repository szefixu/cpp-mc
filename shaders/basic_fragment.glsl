#version 330 core

in vec3 Normal;
in vec2 TexCoord;
// in float AoFactor; // Temporarily removed
in vec3 FragPos; // Fragment position in world space

out vec4 FragColor;

uniform sampler2D textureSampler;  // Texture atlas
uniform vec3 lightDir;             // Light direction (world space, normalized)
uniform float ambientStrength;
// uniform float diffuseStrength; // Assuming diffuseStrength = 1.0 for now

void main() {
    // Ambient light
    vec3 ambient = ambientStrength * vec3(1.0, 1.0, 1.0); // Assuming light color is white

    // Diffuse light
    vec3 norm = normalize(Normal);
    float diff = max(dot(norm, normalize(lightDir)), 0.0);
    vec3 diffuse = diff * vec3(1.0, 1.0, 1.0); // Assuming light color is white

    // Combine lighting, modulated by texture color
    // AO factor multiplication is temporarily removed
    vec4 texColor = texture(textureSampler, TexCoord);
    vec3 lighting = (ambient + diffuse); // * AoFactor; // AO Temporarily removed
    FragColor = vec4(lighting * texColor.rgb, texColor.a);
}
