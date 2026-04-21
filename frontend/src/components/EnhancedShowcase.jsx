import React, { useState } from 'react'
import BeforeAfterSlider from './BeforeAfterSlider'

const MATERIAL_OPTIONS = [
  { key: 'plastic', label: 'Plastic', price_key: 'plastic' },
  { key: 'silver', label: 'Silver', price_key: 'silver' },
  { key: 'gold_14k_yellow', label: 'Gold', price_key: 'gold_14k_yellow' },
  { key: 'platinum', label: 'Platinum', price_key: 'platinum' },
]

export default function EnhancedShowcase({ photo, model, glbUrl, label, pricing }) {
  const [selectedMaterial, setSelectedMaterial] = useState('silver')
  // Always use slider mode since we don't have GLB files yet

  const isPreciousMetal = selectedMaterial !== 'plastic'
  const materialPricing = pricing?.materials?.[selectedMaterial]

  return (
    <div className="enhanced-showcase-item">
      <div className="showcase-viewer">
        <BeforeAfterSlider beforeImg={photo} afterImg={model} label={label} />
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
