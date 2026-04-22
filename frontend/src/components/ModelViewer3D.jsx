import React, { useEffect, useRef, useState } from 'react'

/**
 * Premium 3D Model Viewer Component
 * 
 * Wraps Google's model-viewer web component with proper error handling,
 * loading states, and fallbacks for a premium user experience.
 */
export default function ModelViewer3D({ 
  glbUrl, 
  posterUrl, 
  alt = '3D Model',
  height = '400px',
  autoRotate = true,
  className = ''
}) {
  const viewerRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scriptLoaded, setScriptLoaded] = useState(false)

  // Load model-viewer script
  useEffect(() => {
    // Check if already loaded
    if (window.customElements && window.customElements.get('model-viewer')) {
      setScriptLoaded(true)
      return
    }

    // Check if script tag already exists
    if (document.querySelector('script[src*="model-viewer"]')) {
      // Script is loading, wait for it
      const checkLoaded = setInterval(() => {
        if (window.customElements && window.customElements.get('model-viewer')) {
          setScriptLoaded(true)
          clearInterval(checkLoaded)
        }
      }, 100)
      return () => clearInterval(checkLoaded)
    }

    // Load the script
    const script = document.createElement('script')
    script.type = 'module'
    script.src = 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js'
    script.async = true
    
    script.onload = () => {
      console.log('Model-viewer script loaded')
      setScriptLoaded(true)
    }
    
    script.onerror = () => {
      console.error('Failed to load model-viewer script')
      setError('Failed to load 3D viewer component')
    }
    
    document.head.appendChild(script)

    return () => {
      // Don't remove script on unmount - keep it for other instances
    }
  }, [])

  // Attach event listeners once script is loaded
  useEffect(() => {
    if (!scriptLoaded || !viewerRef.current) return

    const viewer = viewerRef.current

    const handleLoad = () => {
      console.log('Model loaded successfully')
      setLoading(false)
      setError(null)
    }

    const handleError = (event) => {
      console.error('Model loading error:', event.detail)
      setLoading(false)
      setError(event.detail?.message || 'Failed to load 3D model')
    }

    const handleProgress = (event) => {
      const progress = Math.round(event.detail.totalProgress * 100)
      console.log(`Loading progress: ${progress}%`)
    }

    viewer.addEventListener('load', handleLoad)
    viewer.addEventListener('error', handleError)
    viewer.addEventListener('progress', handleProgress)

    return () => {
      viewer.removeEventListener('load', handleLoad)
      viewer.removeEventListener('error', handleError)
      viewer.removeEventListener('progress', handleProgress)
    }
  }, [scriptLoaded])

  if (!scriptLoaded) {
    return (
      <div 
        className={className}
        style={{
          height,
          background: '#f4f0ff',
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: '1rem'
        }}
      >
        <div className="spinner" />
        <div style={{ color: 'var(--ink-soft)', fontSize: '0.9rem' }}>
          Loading 3D viewer...
        </div>
      </div>
    )
  }

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
      <model-viewer
        ref={viewerRef}
        src={glbUrl}
        alt={alt}
        poster={posterUrl || ''}
        camera-controls
        touch-action="pan-y"
        auto-rotate={autoRotate ? '' : undefined}
        auto-rotate-delay="1000"
        rotation-per-second="30deg"
        shadow-intensity="1"
        exposure="1"
        environment-image="neutral"
        loading="eager"
        reveal="auto"
        style={{
          width: '100%',
          height,
          background: '#f4f0ff',
          borderRadius: 12
        }}
      >
        {loading && (
          <div
            slot="poster"
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(244, 240, 255, 0.9)',
              borderRadius: 12
            }}
          >
            <div className="spinner" />
          </div>
        )}
      </model-viewer>
      
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
