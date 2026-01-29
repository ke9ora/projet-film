precision highp float;

uniform sampler2D map;
varying vec2 vUv;

void main() {

    vec4 color = texture2D(map, vUv);

    // discard des pixels transparents (très important pour la perf)
    if (color.a < 0.1) discard;


    gl_FragColor = color;
}
