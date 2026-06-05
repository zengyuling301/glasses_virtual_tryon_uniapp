const FACE = 'tryon_face_path'
const METRICS = 'tryon_metrics'
const RECS = 'tryon_recommendations'
const TRYON_CACHE = 'tryon_image_cache'
const CAPTURE_MODE = 'tryon_capture_mode'

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

/** 拍照模式：depth（有景深无参照物）| reference（无景深须持参照物） */
export function setCaptureMode(mode) {
  uni.setStorageSync(CAPTURE_MODE, mode)
}

export function getCaptureMode() {
  return uni.getStorageSync(CAPTURE_MODE) || 'depth'
}

export function clearSession() {
  uni.removeStorageSync(FACE)
  uni.removeStorageSync(METRICS)
  uni.removeStorageSync(RECS)
  uni.removeStorageSync(TRYON_CACHE)
  uni.removeStorageSync(CAPTURE_MODE)
}

