import React, { useEffect, useRef, useState } from 'react'

/**
 * Premium 3D Model Viewer Component
 * 
 * Uses direct DOM manipulation to create model-viewer element
 * for maximum compatibility with the web component.
 */
export default function ModelViewer3D({ 
  glbUrl, 
  posterUrl, 
  alt = '3D Model',
  height = '400px',
  autoRotate = true,
  className = ''
}) {
  const containerRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const [modelLoaded, setModelLoaded] = useState(false)
  const glbUrlRef = useRef(glbUrl)  // Store URL in ref to prevent re-renders

  useEffect(() => {
    // Only create viewer once - never recreate after loaded
    if (modelLoaded || !glbUrl) return
    if (!containerRef.current) return

    let mounted = true
    let checkInterval = null

    // Wait for model-viewer web component to be registered
    const createViewer = () => {
      if (!mounted || !containerRef.current) return

      console.log('🎨 Creating model-viewer element...')
      console.log('GLB URL:', glbUrl)
      console.log('Poster URL:', posterUrl)
      
      const viewer = document.createElement('model-viewer')
      viewer.setAttribute('src', glbUrl)
      viewer.setAttribute('alt', alt)
      if (posterUrl) viewer.setAttribute('poster', posterUrl)
      viewer.setAttribute('camera-controls', '')
      viewer.setAttribute('touch-action', 'pan-y')
      if (autoRotate) {
        viewer.setAttribute('auto-rotate', '')
        viewer.setAttribute('auto-rotate-delay', '1000')
        viewer.setAttribute('rotation-per-second', '30deg')
      }
      viewer.setAttribute('shadow-intensity', '1')
      viewer.setAttribute('exposure', '1')
      viewer.setAttribute('environment-image', 'neutral')
      viewer.style.width = '100%'
      viewer.style.height = height
      viewer.style.background = '#f4f0ff'
      viewer.style.borderRadius = '12px'

      viewer.addEventListener('load', () => {
        console.log('✅ Model loaded successfully!')
        if (mounted) {
          setLoading(false)
          setError(null)
          setModelLoaded(true)  // Mark as loaded - never recreate
        }
      })

      viewer.addEventListener('error', (e) => {
        console.error('❌ Model loading error:', e)
        if (mounted) {
          setLoading(false)
          setError('Failed to load 3D model')
        }
      })

      viewer.addEventListener('progress', (e) => {
        const prog = Math.round(e.detail.totalProgress * 100)
        if (mounted) setProgress(prog)
        if (prog % 10 === 0) console.log(`📊 Loading: ${prog}%`)
      })

      containerRef.current.innerHTML = ''
      containerRef.current.appendChild(viewer)
    }

    // Check if model-viewer is already registered
    if (window.customElements && window.customElements.get('model-viewer')) {
      console.log('✅ model-viewer already registered')
      createViewer()
    } else {
      console.log('⏳ Waiting for model-viewer to register...')
      // Poll for registration
      checkInterval = setInterval(() => {
        if (window.customElements && window.customElements.get('model-viewer')) {
          console.log('✅ model-viewer registered!')
          clearInterval(checkInterval)
          createViewer()
        }
      }, 50)

      // Timeout after 30 seconds (mobile can be slow)
      setTimeout(() => {
        if (checkInterval) {
          clearInterval(checkInterval)
          if (mounted && !containerRef.current?.querySelector('model-viewer')) {
            console.error('❌ model-viewer script failed to load')
            setLoading(false)
            setError('3D viewer failed to load')
          }
        }
      }, 30000)
    }

    return () => {
      mounted = false
      if (checkInterval) clearInterval(checkInterval)
      // DO NOT clear innerHTML on cleanup - keep viewer alive
      // Only clear if component is truly unmounting (which shouldn't happen)
    }
  }, [])  // Empty deps - run once on mount, never re-run

  if (error) {
    return (
      <div 
        className={className}
        style={{
          height,
          background: '#fff3e0',
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: '0.5rem',
          padding: '2rem',
          textAlign: 'center'
        }}
      >
        {posterUrl && (
          <img 
            src={posterUrl} 
            alt={alt}
            style={{
              maxWidth: '100%',
              maxHeight: '60%',
              borderRadius: 8,
              marginBottom: '1rem'
            }}
          />
        )}
        <div style={{ color: 'var(--ink)', fontSize: '0.9rem', fontWeight: 600 }}>
          3D viewer unavailable
        </div>
        <div style={{ color: 'var(--ink-soft)', fontSize: '0.85rem' }}>
          {posterUrl ? 'Preview image shown above' : error}
        </div>
      </div>
    )
  }

  return (
    <div className={className} style={{ position: 'relative' }}>
      <div 
        ref={containerRef} 
        style={{ 
          position: 'relative',
          minHeight: height 
        }}
      >
        {loading && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(244, 240, 255, 0.95)',
              borderRadius: 12,
              zIndex: 10,
              gap: '1rem'
            }}
          >
            <div className="spinner" />
            <div style={{ color: 'var(--ink-soft)', fontSize: '0.9rem' }}>
              {progress > 0 ? `Loading 3D model... ${progress}%` : 'Initializing...'}
            </div>
          </div>
        )}
      </div>
      
      {!loading && !error && (
        <div
          style={{
            textAlign: 'center',
            marginTop: '0.75rem',
            fontSize: '0.85rem',
            color: 'var(--ink-soft)'
          }}
        >
          ⤾ Drag to rotate • Scroll to zoom • Two-finger to pan
        </div>
      )}
    </div>
  )
}
