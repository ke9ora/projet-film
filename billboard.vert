attribute vec3 instanceOffset;
attribute float instanceScale;

out vec2 vUv;

void main() {

    vUv = uv;

    // position du centre du billboard en view space
    vec4 mvCenter = modelViewMatrix * vec4(instanceOffset, 1.0);

    float dist = length(mvCenter.xyz);

    // scale dépendant de la distance
    float scale = instanceScale / dist;

    if (scale < 0.002) {
        gl_Position = vec4(2.0);
        return;
    }
    // billboard face caméra → on décale en X/Y uniquement
    vec3 billboardPos = mvCenter.xyz +
        vec3(position.x * scale, position.y * scale, 0.0);

    gl_Position = projectionMatrix * vec4(billboardPos, 1.0);
}
