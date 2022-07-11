import * as fop from '@fiftyone/plugins'
import React, {useState, useRef, useEffect, Fragment} from 'react'
import { Canvas, ThreeEvent, useFrame, useLoader, useThree } from '@react-three/fiber'
import {PCDLoader} from 'three/examples/jsm/loaders/PCDLoader'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

THREE.Object3D.DefaultUp = new THREE.Vector3(0,0,1)



function generateTexture(gradients: [number, string][]) {
	var size = 512;


	// create canvas
	const canvas = document.createElement( 'canvas' );
	canvas.width = size;
	canvas.height = size;

	// get context
	const context = canvas.getContext( '2d' );

	// draw gradient
	context.rect( 0, 0, size, size );
	const gradient = context.createLinearGradient( 0, 0, 0, size );
  for (const g of gradients) {
    gradient.addColorStop(...g);
  }
	context.fillStyle = gradient;
	context.fill();

	return canvas;
}

const deg2rad = degrees => degrees * (Math.PI / 180);

function PointCloudMesh({points}) {
  const gradientMap = React.useMemo(() => new THREE.CanvasTexture(generateTexture([
    [0, '#38fffc'],
    [0.5, '#ff7a38'],
    [1, '#ffffff']
  ])), [])

  var heatVertex = `
    uniform float maxZ;
    uniform float minZ;
    varying vec2 vUv;
    varying float hValue;

    float remap ( float minval, float maxval, float curval ) {
      return ( curval - minval ) / ( maxval - minval );
    }

    void main() {
      vUv = uv;
      vec3 pos = position;
      hValue = remap(minZ, maxZ, pos.z);

      vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);

      gl_PointSize = 10. * (1. / - mvPosition.z);
      gl_Position = projectionMatrix * mvPosition;
    }
  `;
  var heatFragment = `
    uniform sampler2D gradientMap;
    varying float hValue;

    void main() {
      float v = clamp(hValue, 0., 1.);
      vec3 col = texture2D(gradientMap, vec2(0, v)).rgb;
      gl_FragColor = vec4(col, 1.);
    }
  `;

  const geo = points.geometry;
  geo.computeBoundingBox();
  const groundOffset = -2.1;

  return (
    <primitive scale={1} object={points} rotation={[0, 0, deg2rad(90)]}>
      {/* <pointsMaterial color={'white'} size={0.0001} /> */}
      <shaderMaterial
        {...{
          uniforms: {
            minZ: {value: groundOffset}, // geo.boundingBox.min.z
            maxZ: {value: geo.boundingBox.max.z},
            gradientMap: {value: gradientMap}
          },
          vertexShader: heatVertex,
          fragmentShader: heatFragment
        }}
      />
    </primitive>
  )
}

function Cuboid({dimensions, opacity, rotation_y, location, selected, onClick}) {
  const [x, y, z] = location
  const x2 = x
  const y2 = y - (0.5 * dimensions[1])
  const z2 = z
  const loc = [
    x2,
    y2,
    z2
  ]

  const geo = React.useMemo(() => new THREE.BoxGeometry(...dimensions), [])
  return (
    <Fragment>
      <mesh position={loc} rotation={[0, rotation_y + Math.PI / 2, 0]}>
        <lineSegments>
          <edgesGeometry args={[geo]} attach="geometry" />
          <lineBasicMaterial attach="material" lineWidth={8} color={selected ? 'orange' : 'green'} />
        </lineSegments>
      </mesh>
      <mesh onClick={onClick} position={loc} rotation={[0, rotation_y + Math.PI / 2, 0]}>
        <boxGeometry args={dimensions} />
        <meshBasicMaterial transparent={true} opacity={opacity * 0.5} color={selected ? 'orange' : 'green'} />
      </mesh>
    </Fragment>
  )
}

function Polyline({opacity, points3d, selected, onClick}) {
  const geo = React.useMemo(() => new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 10, 0)
  ]), [])

  return (
    <line>
      <primitive object={geo} attach="geometry" />
      <lineBasicMaterial attach="material" color="#ff0000" />
    </line>
  )
}

function CameraSetup() {
  const camera = useThree(state => state.camera)
  const settings = fop.usePluginSettings('point-clouds')

  React.useLayoutEffect(() => {
    if (settings.defaultCameraPosition) {
      camera.position.set(
        settings.defaultCameraPosition.x,
        settings.defaultCameraPosition.y,
        settings.defaultCameraPosition.z
      )
    } else {
      camera.position.set(0, 0, 1)
    }
    camera.rotation.set(0, 0, 0)
    camera.updateProjectionMatrix()
  }, [camera])
  return <OrbitControls makeDefault autoRotateSpeed={2.5} zoomSpeed={0.5} />
}

export function PointCloud({api = {}, filePrefix = '/plugins/point-clouds/example_data/'} = {}) {
  const {
    getSampleSrc,
    sample,
    onSelectLabel,
    state,
    useState,
  } = api as any

  // NOTE: "pcd_filepath" should come from a plugin setting
  // instead of being hardcoded
  const modal = true
  const src = getSampleSrc(sample.pcd_filepath)
  const points = useLoader(PCDLoader, src)
  const selectedLabels = useState(state.selectedLabels)
  const pathFilter = useState(state.pathFilter(modal))
  const labelAlpha = useState(state.alpha(modal))

  const overlays = load3dOverlays(sample, selectedLabels)
    // hardcoding the field name is wrong
    .filter(l => pathFilter('ground_truth', l))

  const handleSelect = (label) => {
    console.log({label})
    onSelectLabel({detail: {id: label._id, field: 'detections'}})
  }
  
  console.log(sample.polylines)

  return (
    <Canvas>
      <CameraSetup />
      <mesh rotation={[deg2rad(90), deg2rad(180), deg2rad(180)]}>
        {overlays.filter(o => o._cls === 'Detection').map(label => <Cuboid opacity={labelAlpha} {...label} onClick={() => handleSelect(label)} />)}
      </mesh>
      {overlays.filter(o => o._cls === 'Polyline' && o.points3d).map(label => <Polyline opacity={labelAlpha} {...label} onClick={() => handleSelect(label)} />)}
      <PointCloudMesh points={points} />
      <axesHelper />
    </Canvas>
  )
}

function load3dOverlays(sample, selectedLabels) {
  let overlays = [];
  const labels = Array.isArray(sample) ? sample : Object.values(sample)
  for (const label of labels) {
    if (!label) {
      continue;
    }

    // Note: this logic is not quite right
    // this is hardcoded to match the kitti dataset
    // it should change to be dataset agnostic!

    if (RENDERABLE.includes(label._cls)) {
      overlays.push({
        ...label,
        selected: label._id in selectedLabels
      })
    } else if (RENDERABLE_LIST.includes(label._cls)) {
      overlays = [...overlays, ...load3dOverlays(label[label._cls.toLowerCase()], selectedLabels)]
    } 
  }

  return overlays;
}

const RENDERABLE = ['Detection', 'Polyline']
const RENDERABLE_LIST = ['Detections', 'Polylines']