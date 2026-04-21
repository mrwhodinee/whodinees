import React, { useState, useRef, useEffect } from 'react'

export default function BeforeAfterSlider({ beforeImg, afterImg, label }) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef(null)

  const handleMove = (clientX) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = clientX - rect.left
    const percent = Math.min(Math.max((x / rect.width) * 100, 0), 100)
    setSliderPosition(percent)
  }

  const handleMouseDown = () => setIsDragging(true)
  const handleMouseUp = () => setIsDragging(false)

  const handleMouseMove = (e) => {
    if (!isDragging) return
    handleMove(e.clientX)
  }

  const handleTouchMove = (e) => {
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX)
    }
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  return (
    <div 
      ref={containerRef}
      className="before-after-slider"
      onTouchMove={handleTouchMove}
      style={{ position: 'relative', width: '100%', overflow: 'hidden', borderRadius: '12px', cursor: 'ew-resize' }}
    >
      <img src={beforeImg} alt={`${label} original`} style={{ width: '100%', display: 'block' }} />
      
      <div 
        className="after-layer"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          clipPath: `inset(0 ${100 - sliderPosition}% 0 0)`
        }}
      >
        <img src={afterImg} alt={`${label} 3D model`} style={{ width: '100%' }} />
      </div>

      <div 
        className="slider-handle"
        onMouseDown={handleMouseDown}
        onTouchStart={() => setIsDragging(true)}
        onTouchEnd={() => setIsDragging(false)}
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: `${sliderPosition}%`,
          width: '4px',
          backgroundColor: '#fff',
          cursor: 'ew-resize',
          boxShadow: '0 0 8px rgba(0,0,0,0.3)',
          transform: 'translateX(-50%)',
          zIndex: 10
        }}
      >
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '40px',
          height: '40px',
          backgroundColor: '#fff',
          borderRadius: '50%',
          boxShadow: '0 2px 12px rgba(0,0,0,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '20px',
          color: '#8a5cff',
          fontWeight: 'bold'
        }}>
          ⟷
        </div>
      </div>

      <div className="slider-labels" style={{ position: 'absolute', bottom: '12px', left: 0, right: 0, display: 'flex', justifyContent: 'space-between', padding: '0 16px', pointerEvents: 'none' }}>
        <span style={{ backgroundColor: 'rgba(0,0,0,0.6)', color: '#fff', padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>Original Photo</span>
        <span style={{ backgroundColor: 'rgba(138,92,255,0.9)', color: '#fff', padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>3D Model</span>
      </div>
    </div>
  )
}
