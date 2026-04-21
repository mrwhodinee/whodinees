import React, { useState } from 'react'
import BeforeAfterSlider from './BeforeAfterSlider'
import Model3DViewer from './Model3DViewer'

const MATERIAL_OPTIONS = [
  { key: 'plastic', label: 'Plastic', price_key: 'plastic' },
  { key: 'silver', label: 'Silver', price_key: 'silver' },
  { key: 'gold_14k_yellow', label: 'Gold', price_key: 'gold_14k_yellow' },
  { key: 'platinum', label: 'Platinum', price_key: 'platinum' },
]

export default function EnhancedShowcase({ photo, model, glbUrl, label, pricing }) {
  const [selectedMaterial, setSelectedMaterial] = useState('silver')
  const [viewMode, setViewMode] = useState('slider') // 'slider' or '3d'

  const isPreciousMetal = selectedMaterial !== 'plastic'
  const materialPricing = pricing?.materials?.[selectedMaterial]

  return (
    <div className="enhanced-showcase-item">
      <div className="showcase-viewer">
        {viewMode === 'slider' ? (
          <BeforeAfterSlider beforeImg={photo} afterImg={model} label={label} />
        ) : (
          glbUrl ? (
            <Model3DViewer 
              modelUrl={glbUrl} 
              material={selectedMaterial}
              showParticles={isPreciousMetal}
            />
          ) : (
            <div style={{ 
              width: '100%', 
              height: '400px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              backgroundColor: '#f5f5f5',
              borderRadius: '12px',
              color: '#999'
            }}>
              3D model not available
            </div>
          )
        )}
      </div>

      <div className="view-mode-toggle" style={{ 
        display: 'flex', 
        gap: '8px', 
        marginTop: '12px',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => setViewMode('slider')}
          className={viewMode === 'slider' ? 'active' : ''}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: viewMode === 'slider' ? '2px solid #8a5cff' : '1px solid #ddd',
            backgroundColor: viewMode === 'slider' ? '#f9f7ff' : '#fff',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          Compare
        </button>
        <button
          onClick={() => setViewMode('3d')}
          className={viewMode === '3d' ? 'active' : ''}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: viewMode === '3d' ? '2px solid #8a5cff' : '1px solid #ddd',
            backgroundColor: viewMode === '3d' ? '#f9f7ff' : '#fff',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          3D View
        </button>
      </div>

      <div className="material-switcher" style={{ 
        marginTop: '16px',
        display: 'flex',
        gap: '8px',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        {MATERIAL_OPTIONS.map(mat => (
          <button
            key={mat.key}
            onClick={() => setSelectedMaterial(mat.key)}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              border: selectedMaterial === mat.key ? '2px solid #8a5cff' : '1px solid #ddd',
              backgroundColor: selectedMaterial === mat.key ? '#8a5cff' : '#fff',
              color: selectedMaterial === mat.key ? '#fff' : '#333',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              transition: 'all 0.2s'
            }}
          >
            {mat.label}
          </button>
        ))}
      </div>

      {materialPricing && (
        <div className="pricing-estimate" style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: '#f9f7ff',
          borderRadius: '8px',
          textAlign: 'center',
          fontSize: '14px',
          color: '#5a527a'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            Estimated value in {MATERIAL_OPTIONS.find(m => m.key === selectedMaterial)?.label} today:
          </div>
          <div style={{ fontSize: '20px', fontWeight: '700', color: '#8a5cff' }}>
            ${materialPricing.typical_total}
          </div>
          {materialPricing.spot_price_per_gram > 0 && (
            <div style={{ fontSize: '12px', marginTop: '4px', color: '#999' }}>
              Live spot price: ${materialPricing.spot_price_per_gram}/g
            </div>
          )}
        </div>
      )}

      <div className="showcase-caption" style={{ 
        marginTop: '12px',
        textAlign: 'center',
        fontSize: '16px',
        fontWeight: '600',
        color: '#333'
      }}>
        {label}
      </div>
    </div>
  )
}
