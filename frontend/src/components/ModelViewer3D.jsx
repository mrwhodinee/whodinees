import React, { useEffect, useState, useRef } from 'react'

/**
 * Premium 3D Model Viewer Component
 * 
 * Renders model-viewer as a React element instead of manual DOM manipulation.
 * This prevents React reconciliation errors.
 */
export default function ModelViewer3D({ 
  glbUrl, 
  posterUrl, 
  alt = '3D Model',
  height = '400px',
  autoRotate = true,
  className = ''
}) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const viewerRef = useRef(null)

  useEffect(() => {
    if (!viewerRef.current || !glbUrl) return

    const viewer = viewerRef.current

    const handleLoad = () => {
      console.log('✅ Model loaded successfully!')
      setLoading(false)
      setError(null)
    }

    const handleError = (e) => {
      console.error('❌ Model loading error:', e)
      setLoading(false)
      setError('Failed to load 3D model')
    }

    const handleProgress = (e) => {
      const prog = Math.round(e.detail.totalProgress * 100)
      setProgress(prog)
      if (prog % 10 === 0) console.log(`📊 Loading: ${prog}%`)
    }

    viewer.addEventListener('load', handleLoad)
    viewer.addEventListener('error', handleError)
    viewer.addEventListener('progress', handleProgress)

    return () => {
      viewer.removeEventListener('load', handleLoad)
      viewer.removeEventListener('error', handleError)
      viewer.removeEventListener('progress', handleProgress)
    }
  }, [glbUrl])

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

  if (!glbUrl) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className={className} style={{ position: 'relative' }}>
      <div style={{ position: 'relative', minHeight: height }}>
        <model-viewer
          ref={viewerRef}
          src={glbUrl}
          alt={alt}
          poster={posterUrl || undefined}
          camera-controls="true"
          touch-action="pan-y"
          auto-rotate={autoRotate ? "true" : undefined}
          auto-rotate-delay="1000"
          rotation-per-second="30deg"
          shadow-intensity="1"
          exposure="1"
          environment-image="neutral"
          style={{
            width: '100%',
            height,
            background: '#f4f0ff',
            borderRadius: '12px'
          }}
        />
        
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
