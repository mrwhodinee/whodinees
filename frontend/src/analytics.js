/**
 * Google Analytics 4 event tracking utilities
 * 
 * Custom conversion events for Whodinees e-commerce funnel
 */
import ReactGA from 'react-ga4'

/**
 * Track when customer begins photo upload
 * @param {string} petType - Type of pet (dog, cat, other)
 */
export const trackUploadStarted = (petType = 'unknown') => {
  ReactGA.event('upload_started', {
    event_category: 'engagement',
    event_label: petType,
    pet_type: petType
  })
  console.log('[GA4] upload_started:', petType)
}

/**
 * Track when Meshy returns a successful model
 * @param {string} portraitId - Portrait ID
 * @param {number} taskId - Meshy task ID
 */
export const trackModelGenerated = (portraitId, taskId) => {
  ReactGA.event('model_generated', {
    event_category: 'conversion',
    event_label: `portrait_${portraitId}`,
    portrait_id: portraitId,
    task_id: taskId
  })
  console.log('[GA4] model_generated:', portraitId, taskId)
}

/**
 * Track when customer picks a material
 * @param {string} material - Material selected (plastic, silver, gold, platinum)
 * @param {number} price - Price in USD
 */
export const trackMaterialSelected = (material, price) => {
  ReactGA.event('material_selected', {
    event_category: 'engagement',
    event_label: material,
    material: material,
    value: price,
    currency: 'USD'
  })
  console.log('[GA4] material_selected:', material, price)
}

/**
 * Track when customer proceeds to Stripe checkout
 * @param {string} portraitId - Portrait ID
 * @param {string} material - Material selected
 * @param {number} price - Total price in USD
 */
export const trackCheckoutStarted = (portraitId, material, price) => {
  ReactGA.event('begin_checkout', {
    event_category: 'ecommerce',
    value: price,
    currency: 'USD',
    items: [{
      item_id: `portrait_${portraitId}`,
      item_name: `Custom Pet Portrait - ${material}`,
      item_category: 'Portraits',
      item_variant: material,
      price: price,
      quantity: 1
    }]
  })
  console.log('[GA4] begin_checkout:', portraitId, material, price)
}

/**
 * Track when Stripe payment confirms
 * @param {string} orderId - Order ID
 * @param {string} material - Material selected
 * @param {number} price - Total price in USD
 * @param {number} materialCost - Material cost breakdown
 * @param {number} designFee - Design fee
 */
export const trackOrderCompleted = (orderId, material, price, materialCost, designFee) => {
  ReactGA.event('purchase', {
    event_category: 'ecommerce',
    transaction_id: orderId,
    value: price,
    currency: 'USD',
    tax: 0,
    shipping: 0,
    items: [{
      item_id: `order_${orderId}`,
      item_name: `Custom Pet Portrait - ${material}`,
      item_category: 'Portraits',
      item_variant: material,
      price: price,
      quantity: 1
    }]
  })
  console.log('[GA4] purchase:', orderId, material, price)
}

/**
 * Track when upload starts but never completes
 * @param {string} portraitId - Portrait ID
 * @param {string} stage - Stage where they dropped off
 */
export const trackUploadAbandoned = (portraitId, stage) => {
  ReactGA.event('upload_abandoned', {
    event_category: 'abandonment',
    event_label: stage,
    portrait_id: portraitId,
    stage: stage
  })
  console.log('[GA4] upload_abandoned:', portraitId, stage)
}

/**
 * Track page views (automatic with router, but can be called manually)
 * @param {string} path - Page path
 * @param {string} title - Page title
 */
export const trackPageView = (path, title) => {
  ReactGA.send({ hitType: 'pageview', page: path, title: title })
  console.log('[GA4] pageview:', path, title)
}
