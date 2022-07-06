
import React, {useState, useRef, useEffect, Fragment} from 'react'
import { Canvas, ThreeEvent, useFrame, useLoader, useThree } from '@react-three/fiber'
import {PCDLoader} from 'three/examples/jsm/loaders/PCDLoader'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

THREE.Object3D.DefaultUp = new THREE.Vector3(0,0,1)


const deg2rad = degrees => degrees * (Math.PI / 180);

function PointCloudMesh({points}) {
  return (
    <primitive scale={1} object={points}>
      <pointsMaterial color={'white'} size={0.0001} />
    </primitive>
  )
}

function Cuboid({dimensions, alpha, rotation_y, location, selected, onClick}) {
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
        <meshBasicMaterial transparent={true} opacity={0.18} color={selected ? 'orange' : 'green'} />
      </mesh>
    </Fragment>
  )
}

function CameraSetup() {
  const camera = useThree(state => state.camera)
  React.useEffect(() => {
    console.log('set camera pos')
    camera.position.set(0, 0, 20)
    camera.rotation.set(0, 0, 0)
    camera.updateProjectionMatrix()

    return () => {
      console.log('CameraSetup unmounted')
    }
  }, [])
  return <OrbitControls makeDefault autoRotateSpeed={2.5} zoomSpeed={0.1} />
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
  const src = getSampleSrc(sample.pcd_filepath)
  const points = useLoader(PCDLoader, src)
  const selectedLabels = useState(state.selectedLabels)
  const pathFilter = useState(state.pathFilter(true))

  // ground_truth.detections[0].location
  // ground_truth.detections[0].dimensions
  // ground_truth.detections[0].rotation_y


  // rotation={[deg2rad(-90), 0, deg2rad(90)]}

  const overlays = load3dOverlays(sample, selectedLabels)
    // hardcoding the field name is wrong
    .filter(l => pathFilter('ground_truth', l))

  const handleSelect = (label) => {
    console.log({label})
    onSelectLabel({detail: {id: label._id, field: 'detections'}})
  }

  return (
    <Canvas>
      <CameraSetup />
      <mesh rotation={[deg2rad(90), deg2rad(90), deg2rad(180)]}>
        {overlays.map(label => <Cuboid {...label} onClick={() => handleSelect(label)} />)}
      </mesh>
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

    if (label._cls === 'Detections') {
      overlays = [...overlays, ...load3dOverlays(label.detections, selectedLabels)]
    } else if (label._cls === 'Detection') {
      if (Array.isArray(label.dimensions) && Array.isArray(label.location)) {
        overlays.push({
          ...label,
          selected: label._id in selectedLabels
        })
      }
    }
  }

  return overlays;
}