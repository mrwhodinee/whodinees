import React, { Suspense, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useGLTF } from '@react-three/drei'

function RotatingModel({ modelUrl, material = 'plastic' }) {
  const { scene } = useGLTF(modelUrl)
  const meshRef = useRef()

  // Gentle continuous rotation
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.3
    }
  })

  // Material properties based on selection
  const getMaterialProps = () => {
    switch (material) {
      case 'silver':
        return { metalness: 0.9, roughness: 0.2, color: '#C0C0C0' }
      case 'gold_14k_yellow':
      case 'gold_18k_yellow':
        return { metalness: 0.95, roughness: 0.15, color: '#FFD700' }
      case 'gold_14k_rose':
        return { metalness: 0.9, roughness: 0.2, color: '#E5A A77' }
      case 'gold_14k_white':
        return { metalness: 0.95, roughness: 0.15, color: '#E8E8E8' }
      case 'platinum':
        return { metalness: 0.95, roughness: 0.1, color: '#E5E4E2' }
      default:
        return { metalness: 0.1, roughness: 0.8, color: '#FFFFFF' }
    }
  }

  const matProps = getMaterialProps()

  // Apply material to all meshes in the scene
  scene.traverse((child) => {
    if (child.isMesh) {
      child.material = child.material.clone()
      child.material.metalness = matProps.metalness
      child.material.roughness = matProps.roughness
      child.material.color.set(matProps.color)
    }
  })

  return <primitive ref={meshRef} object={scene} scale={2} />
}

export default function Model3DViewer({ modelUrl, material = 'plastic', showParticles = false }) {
  return (
    <div style={{ width: '100%', height: '400px', position: 'relative', borderRadius: '12px', overflow: 'hidden', backgroundColor: '#1a1a2e' }}>
      {showParticles && <ParticleBackground />}
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <directionalLight position={[-10, -10, -5]} intensity={0.3} />
          <RotatingModel modelUrl={modelUrl} material={material} />
          <OrbitControls enableZoom={false} autoRotate={false} />
        </Suspense>
      </Canvas>
    </div>
  )
}

function ParticleBackground() {
  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'radial-gradient(circle at 50% 50%, rgba(138,92,255,0.1) 0%, transparent 70%)',
      animation: 'shimmer 3s infinite alternate',
      pointerEvents: 'none',
      zIndex: 1
    }} />
  )
}
