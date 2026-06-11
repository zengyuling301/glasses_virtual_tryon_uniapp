const FACE = 'tryon_face_path'
const METRICS = 'tryon_metrics'
const RECS = 'tryon_recommendations'
const TRYON_CACHE = 'tryon_image_cache'
const CAPTURE_MODE = 'tryon_capture_mode'
const REF_CALIB_DATA = 'tryon_ref_calib_data'

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

/** 参照物标定数据（reference 模式拍照时写入，上传时携带） */
export function setRefCalibData(data) {
  uni.setStorageSync(REF_CALIB_DATA, data || null)
}

export function getRefCalibData() {
  return uni.getStorageSync(REF_CALIB_DATA) || null
}

export function clearSession() {
  uni.removeStorageSync(FACE)
  uni.removeStorageSync(METRICS)
  uni.removeStorageSync(RECS)
  uni.removeStorageSync(TRYON_CACHE)
  // CAPTURE_MODE 与 REF_CALIB_DATA 为流程级数据，由 P0/P1 控制生命周期，不在此处清除
}

