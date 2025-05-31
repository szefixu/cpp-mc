#version 330 core

layout (location = 0) in vec3 aPos;          // Vertex position
layout (location = 1) in vec3 aNormal;       // Vertex normal
layout (location = 2) in vec2 aTexCoord;     // Vertex texture coordinate
// layout (location = 3) in float aAoFactor; // Temporarily removed for shader-based rendering

out vec3 Normal;
out vec2 TexCoord;
// out float AoFactor; // Temporarily removed
out vec3 FragPos; // Output fragment position in world space for lighting

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 uv_offset_scale; // u_offset, v_offset, u_scale, v_scale

void main() {
    FragPos = vec3(model * vec4(aPos, 1.0)); // Fragment position in world space
    Normal = mat3(transpose(inverse(model))) * aNormal; // Transform normal to world space
    TexCoord = aTexCoord * uv_offset_scale.zw + uv_offset_scale.xy; // Apply UV transform for atlas
    // AoFactor = aAoFactor; // Temporarily removed
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
