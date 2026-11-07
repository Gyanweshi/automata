// Greybox previz starter (skills/previz-3d): a street, a car-sized block driving up it, and a drone rise
// that ends looking down the street. 9:16, 24 fps, 5 s. Units are metres; y is up, +z points at the camera.
// Copy this into the shot folder, then change the camera path, the subject path, the lens and the set.
// Verified with raea 0.1.0-canary.2: renders, `raea scene lint` reports 0 errors.
import { AbsoluteFill, Composition, Easing, interpolate, registerRoot, useCurrentFrame, useVideoConfig } from "raea";
import { Entity } from "raea/3d";
import { Camera3d } from "raea/camera";
import { AmbientLight, DirectionalLight } from "raea/light";
import { Cuboid, Mesh3d } from "raea/mesh";
import { StandardMaterial } from "raea/pbr";
import { Transform } from "raea/transform";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const BUILDINGS = Array.from({ length: 12 }, (_, i) => ({ x: i % 2 ? 9 : -9, z: -60 + Math.floor(i / 2) * 12, h: 6 + ((i * 7) % 5) * 3 }));

function Shot() {
  const f = useCurrentFrame();
  const { durationInFrames: n } = useVideoConfig();
  const t = interpolate(f, [0, n - 1], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const carZ = interpolate(f, [0, n - 1], [10, -40], clamp);          // car drives up the street
  const camY = interpolate(t, [0, 1], [1.6, 28]);                         // drone rise
  const camZ = interpolate(t, [0, 1], [18, 6]);
  return (
    <AbsoluteFill style={{ background: "#c9d3dc" }}>
      <Camera3d transform={Transform.fromXyz(0, camY, camZ).lookingAt([0, 0.6, carZ - 4])} projection={{ Perspective: { fov: (50 * Math.PI) / 180 } }} />
      <AmbientLight brightness={300} />
      <DirectionalLight transform={Transform.fromXyz(-20, 30, 10).lookingAt([0, 0, 0])} illuminance={9000} shadow_maps_enabled />
      <Mesh3d name="ground" transform={Transform.fromXyz(0, -0.05, -25)}><Cuboid half_size={[40, 0.05, 60]} /><StandardMaterial base_color="#8a8f94" /></Mesh3d>
      <Mesh3d name="road" transform={Transform.fromXyz(0, 0.01, -25)}><Cuboid half_size={[4, 0.01, 60]} /><StandardMaterial base_color="#3b3e42" /></Mesh3d>
      {BUILDINGS.map((b, i) => (
        <Mesh3d key={i} name={`bldg${i}`} transform={Transform.fromXyz(b.x, b.h / 2, b.z)}><Cuboid half_size={[3.5, b.h / 2, 4.5]} /><StandardMaterial base_color="#d8d4cc" /></Mesh3d>
      ))}
      <Entity transform={Transform.fromXyz(1.6, 0, carZ)}>
        <Mesh3d name="car-body" transform={Transform.fromXyz(0, 0.55, 0)}><Cuboid half_size={[0.95, 0.35, 2.4]} /><StandardMaterial base_color="#111111" metallic={0.6} perceptual_roughness={0.3} /></Mesh3d>
        <Mesh3d name="car-cabin" transform={Transform.fromXyz(0, 1.05, -0.2)}><Cuboid half_size={[0.8, 0.25, 1.2]} /><StandardMaterial base_color="#222831" /></Mesh3d>
      </Entity>
    </AbsoluteFill>
  );
}
registerRoot(() => <Composition id="shot" component={Shot} width={1080} height={1920} fps={24} durationInFrames={120} />);
