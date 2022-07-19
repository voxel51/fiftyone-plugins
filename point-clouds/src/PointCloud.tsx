import * as fop from '@fiftyone/plugins'
import React, {useState, useRef, useEffect, Fragment} from 'react'
import { Canvas, ThreeEvent, useFrame, useLoader, useThree } from '@react-three/fiber'
import {PCDLoader} from 'three/examples/jsm/loaders/PCDLoader'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import styled from "styled-components"
import ColorLensIcon from '@mui/icons-material/ColorLens';
import * as pcState from './state'
import * as recoil from 'recoil'
// import * as fos from '@fiftyone/state'
import {ShadeByIntensity, ShadeByZ} from './shaders'

THREE.Object3D.DefaultUp = new THREE.Vector3(0,0,1)




const deg2rad = degrees => degrees * (Math.PI / 180);

function PointCloudMesh({colorBy, points}) {
  const geo = points.geometry;
  geo.computeBoundingBox();
  const gradients = [
    [0, '#38fffc'],
    [0.5, '#ff7a38'],
    [1, '#ffffff']
  ]

  React.useEffect(() => {

  })

  let material
  switch (colorBy) {
    case 'none':
      material = <pointsMaterial color={'white'} size={0.0001} />
      break
    case 'height':
      material = <ShadeByZ gradients={gradients} minZ={geo.boundingBox.min.z} maxZ={geo.boundingBox.max.z} />
      break
    case 'intensity':
      material = <ShadeByIntensity gradients={gradients} />
      break
  }

  console.log({colorBy})

  return (
    <primitive key={colorBy} scale={1} object={points} rotation={[0, 0, deg2rad(90)]}>
      {material}
    </primitive>
  )
}

// function Polygon({opacity, filled, closed, points3d, color, selected, onClick}) {
//   const points = points3d.map(p => new THREE.Vector2(p[0], p[1]))
//   const shape = React.useMemo(() => new THREE.Shape(points), [])
//   const geo = React.useMemo(() => new THREE.ShapeGeometry(shape), [])
//   const mat = React.useMemo(() => {
//     const m = new THREE.MeshBasicMaterial()
//     m.side = THREE.DoubleSide
//     return m
//   }, [])
//   return (
//     <mesh>
//       <primitive object={geo} attach="geometry" />
//       <primitive object={mat} attach="material" color="green" />
//     </mesh>
//   )
// }

function Cuboid({dimensions, opacity, rotation_y, location, selected, onClick, color}) {
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
        <meshBasicMaterial transparent={true} opacity={opacity * 0.5} color={selected ? 'orange' : color} />
      </mesh>
    </Fragment>
  )
}

function Line({points, color, opacity, onClick}) {
  const geo = React.useMemo(() => new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(...p))), [])

  return (
    <line onClick={onClick}>
      <primitive object={geo} attach="geometry" />
      <lineBasicMaterial attach="material" color={color} />
    </line>
  )
}

function Polyline({opacity, filled, closed, points3d, color, selected, onClick}) {
  if (filled) {
    // filled not yet supported
    return null
  }

  return (
    points3d.map(points => <Line points={points} opacity={opacity} color={selected ? 'orange' : color} onClick={onClick} />)
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
      camera.position.set(0, 0, 20)
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
    .filter(l => {
      return pathFilter(l.path.join('.'), l)
    })
    .map(l => {
      // const color = 
      const color = 'green'
      return {...l, color}
    })

  const handleSelect = (label) => {
    console.log({label})
    onSelectLabel({detail: {id: label._id, field: label.path[label.path.length - 1]}})
  }

  const colorBy = recoil.useRecoilValue(pcState.colorBy)
  const [currentAction, setAction] = recoil.useRecoilState(pcState.currentAction)

  return (
    <Container onClick={() => setAction(null)}>
      <Canvas>
        <CameraSetup />
        <mesh rotation={[deg2rad(90), deg2rad(180), deg2rad(180)]}>
          {overlays.filter(o => o._cls === 'Detection').map((label, key) => <Cuboid key={key} opacity={labelAlpha} {...label} onClick={() => handleSelect(label)} />)}
        </mesh>
        {overlays.filter(o => o._cls === 'Polyline' && o.points3d).map((label, key) => <Polyline key={key} opacity={labelAlpha} {...label} onClick={() => handleSelect(label)} />)}
        <PointCloudMesh colorBy={colorBy} points={points} />
        <axesHelper />
      </Canvas>
      <ActionBar />
    </Container>
  )
}

const Container = styled.div`
  height: 100%;
  width: 100%;
  position: relative;
`

const ACTION_BAR_HEIGHT = '3.5em'
const ActionBarContainer = styled.div`
  width: 100%;
  height: ${ACTION_BAR_HEIGHT};
  position: absolute;
  bottom: 0;
  background-color: hsl(210, 11%, 11%);
  border: 1px solid #191c1f;
  box-shadow: 0 8px 15px 0 rgb(0 0 0 / 43%);
`


const ActionPopOver = styled.div`
  width: 100%;
  position: absolute;
  bottom: ${ACTION_BAR_HEIGHT};
  background-color: hsl(210, 11%, 11%);
`


function ActionBar() {
  return (
    <ActionBarContainer>
      <ChooseColorSpace />
    </ActionBarContainer>
  )
}

function ChooseColorSpace() {
  const [open, setOpen] = useState(false)
  const [currentAction, setAction] = recoil.useRecoilState(pcState.currentAction)

  return (
    <Fragment>
      <ColorLensIcon onClick={(e) => {
        setAction('colorBy')
        e.stopPropagation()
        e.preventDefault()
        return false
      }} />
      {currentAction === 'colorBy' && <ColorSpaceChoices />}
    </Fragment>
  )
}

function ColorSpaceChoices() {
  return (
    <ActionPopOver>
      <h4>Color by:</h4>
      {pcState.COLOR_BY_CHOICES.map(p => <Choice {...p} />)}
    </ActionPopOver>
  )
}
function Choice({label, value}) {
  const [current, setCurrent] = recoil.useRecoilState(pcState.colorBy)
  const selected = value === current
  return (
    <div onClick={() => setCurrent(value)}>
      <input type='radio' checked={selected} />
      {label}
    </div>
  )
}

function load3dOverlays(sample, selectedLabels, currentPath = []) {
  let overlays = [];
  const labels = Array.isArray(sample) ? sample : Object.values(sample)
  const labelKeys = Array.isArray(sample) ? null : Object.keys(sample)
  for (let i = 0; i < labels.length; i++) {
    const label = labels[i]
    const labelKey = labelKeys ? labelKeys[i] : ''
    if (!label) {
      continue;
    }

    // Note: this logic is not quite right
    // this is hardcoded to match the kitti dataset
    // it should change to be dataset agnostic!
    if (RENDERABLE.includes(label._cls)) {
      overlays.push({
        ...label,
        path: [...currentPath, labelKey].filter(k => !!k),
        selected: label._id in selectedLabels,
        color: 'green'
      })
    } else if (RENDERABLE_LIST.includes(label._cls)) {
      overlays = [...overlays, ...load3dOverlays(label[label._cls.toLowerCase()], selectedLabels, labelKey ? [...currentPath, labelKey] : [...currentPath])]
    } 
  }

  return overlays;
}

const RENDERABLE = ['Detection', 'Polyline']
const RENDERABLE_LIST = ['Detections', 'Polylines']

function toFlatVectorArray(listOfLists) {
  let vectors = []
  for (const list of listOfLists) {
    const isVector = typeof list[0] === 'number'
    if (isVector) {
      vectors.push(list)
    } else if (Array.isArray(list)) {
      vectors = [...vectors, ...toFlatVectorArray(list)]
    }
  }
  return vectors
}