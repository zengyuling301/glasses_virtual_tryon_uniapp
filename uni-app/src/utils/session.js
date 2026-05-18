const FACE = 'tryon_face_path'
const METRICS = 'tryon_metrics'
const RECS = 'tryon_recommendations'
const TRYON_CACHE = 'tryon_image_cache'

export function setFacePath(path) {
  uni.setStorageSync(FACE, path)
}

export function getFacePath() {
  return uni.getStorageSync(FACE) || ''
}

export function setAnalyzeResult(metrics, recommendations) {
  uni.setStorageSync(METRICS, metrics)
  uni.setStorageSync(RECS, recommendations)
}

export function getMetrics() {
  return uni.getStorageSync(METRICS) || null
}

export function getRecommendations() {
  return uni.getStorageSync(RECS) || []
}

export function getTryonCache() {
  return uni.getStorageSync(TRYON_CACHE) || {}
}

export function setTryonCacheEntry(frameId, dataUrl) {
  const c = getTryonCache()
  c[frameId] = dataUrl
  uni.setStorageSync(TRYON_CACHE, c)
}

export function getTryonCacheEntry(frameId) {
  return getTryonCache()[frameId] || ''
}

export function clearSession() {
  uni.removeStorageSync(FACE)
  uni.removeStorageSync(METRICS)
  uni.removeStorageSync(RECS)
  uni.removeStorageSync(TRYON_CACHE)
}

