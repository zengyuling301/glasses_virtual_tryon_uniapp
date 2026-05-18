/**
 * 已佩戴眼镜检测：FrameFind（ONNX）+ 与预览一致的镜像裁切
 * 提交测算时由后端 /api/analyze 再校验。
 */

import { drawVideoToCanvas, H5_MIRROR_FRONT_PREVIEW } from './h5Camera.js'

const GLASSES_MSG = '请摘下眼镜或墨镜'
const GLASSES_SUB = '检测到镜框特征，摘掉后框会变绿'

const CDN_MODEL_URL = 'https://cdn.framefind.moraxh.dev/models/glasses/v1/glasses.onnx'

const DISABLE_GUARD =
  typeof import.meta !== 'undefined' &&
  import.meta.env &&
  String(import.meta.env.VITE_DISABLE_GLASSES_GUARD || '') === '1'

const CHECK_INTERVAL_MS = 100
/** 库内平滑后判定线（官方 0.35，召回优先） */
const DEFAULT_THRESHOLD = 0.26
const DEFAULT_SMOOTHING = 3
/** 即时判定（单帧） */
const HIT_PROB = 0.22
const PEAK_TRIGGER = 0.28
const LATCH_RING = 12
const UNLATCH_RING = 5
/** 一旦超过即「锁定戴眼镜」，避免低头/反光时 p 骤降导致绿框闪现 */
const LATCH_ON_P = 0.38
const LATCH_ON_PEAK = 0.32
const LATCH_HOLD_MS = 1800
/** 解除：只看最近几帧，避免历史 peak 拖很久 */
const UNLATCH_P = 0.18
const UNLATCH_RECENT_PEAK = 0.24
const UNLATCH_STREAK = 5

let _detector = null
let _offscreen = null
let _mirrorCanvas = null
let _modelBlobUrl = null
let _loadPromise = null
let _lastCheckAt = 0
let _lastDetected = false
let _probRing = []
let _glassesLatched = false
let _latchUntil = 0
let _unlatchStreak = 0

function envNum(key, fallback) {
  const v = import.meta.env?.[key]
  if (v === undefined || v === '') return fallback
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

function resolveLocalModelUrl() {
  if (typeof window === 'undefined') return '/static/models/framefind/glasses.onnx'
  return `${window.location.origin}/static/models/framefind/glasses.onnx`
}

function resolveModelCandidates() {
  const fromEnv = import.meta.env?.VITE_FRAMEFIND_MODEL_URL
  if (fromEnv) return [String(fromEnv)]
  return [resolveLocalModelUrl(), CDN_MODEL_URL]
}

function resolveWasmPaths() {
  const fromEnv = import.meta.env?.VITE_ONNX_WASM_PATH
  if (fromEnv) return String(fromEnv).replace(/\/?$/, '/')
  return 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.26.0/dist/'
}

function mirrorLandmarks(lmNorm) {
  return lmNorm.map((p) => ({ x: 1 - p.x, y: p.y, z: p.z ?? 0 }))
}

function ensureMirrorCanvas(w, h) {
  if (!_mirrorCanvas) {
    _mirrorCanvas = document.createElement('canvas')
  }
  if (_mirrorCanvas.width !== w || _mirrorCanvas.height !== h) {
    _mirrorCanvas.width = w
    _mirrorCanvas.height = h
  }
  return _mirrorCanvas
}

async function fetchModelBlobUrl() {
  const candidates = resolveModelCandidates()
  let lastErr = null
  for (const url of candidates) {
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const buf = await res.arrayBuffer()
      if (buf.byteLength < 1024) throw new Error(`过小 (${buf.byteLength} B)`)
      const head = new Uint8Array(buf, 0, 8)
      const asText = String.fromCharCode(...head)
      if (asText.includes('<')) throw new Error('返回了 HTML')
      const blobUrl = URL.createObjectURL(new Blob([buf], { type: 'application/octet-stream' }))
      return { blobUrl, sourceUrl: url }
    } catch (e) {
      lastErr = e
      console.warn('[glassesGuard] model fetch failed', url, e.message || e)
    }
  }
  throw lastErr || new Error('无可用 FrameFind 模型地址')
}

/**
 * 在「与预览一致」的坐标系里推理（CSS 镜像时翻转画面 + 翻转关键点）
 */
async function detectOnFrame(video, lmNorm) {
  const vw = video.videoWidth
  const vh = video.videoHeight

  if (H5_MIRROR_FRONT_PREVIEW) {
    const canvas = ensureMirrorCanvas(vw, vh)
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    drawVideoToCanvas(ctx, video, vw, vh, { mirror: true })
    return _detector.detectFromCanvas(canvas, mirrorLandmarks(lmNorm))
  }

  return _detector.detectFromVideoFrame(video, _offscreen, lmNorm)
}

function pushProbSample(p) {
  _probRing.push(p)
  while (_probRing.length > LATCH_RING) {
    _probRing.shift()
  }
}

function latchPeakValue() {
  return _probRing.length ? Math.max(..._probRing) : 0
}

/** 解除判定用短窗口 peak，不沿用 16 帧历史 */
function recentPeakValue() {
  const tail = _probRing.slice(-UNLATCH_RING)
  return tail.length ? Math.max(...tail) : 0
}

function updateDetectedState(p, frameGlasses) {
  const hitProb = envNum('VITE_FRAMEFIND_HIT_PROB', HIT_PROB)
  const peakTrig = envNum('VITE_FRAMEFIND_PEAK', PEAK_TRIGGER)
  const latchP = envNum('VITE_FRAMEFIND_LATCH_P', LATCH_ON_P)
  const latchPeak = envNum('VITE_FRAMEFIND_LATCH_PEAK', LATCH_ON_PEAK)
  const unlatchP = envNum('VITE_FRAMEFIND_UNLATCH_P', UNLATCH_P)
  const unlatchRecentPeak = envNum('VITE_FRAMEFIND_UNLATCH_PEAK', UNLATCH_RECENT_PEAK)
  const holdMs = envNum('VITE_FRAMEFIND_LATCH_MS', LATCH_HOLD_MS)

  const peak = latchPeakValue()
  const recentPeak = recentPeakValue()
  const instant = frameGlasses || p >= hitProb || peak >= peakTrig
  const strong = frameGlasses || p >= latchP || peak >= latchPeak

  if (strong) {
    _glassesLatched = true
    _latchUntil = performance.now() + holdMs
    _unlatchStreak = 0
    _lastDetected = true
    return
  }

  if (_glassesLatched) {
    const inHold = performance.now() < _latchUntil
    const relatch =
      frameGlasses || p >= hitProb || recentPeak >= peakTrig || p >= latchP
    if (inHold || relatch) {
      _unlatchStreak = 0
      _lastDetected = true
      return
    }

    const lowNow = p < unlatchP && recentPeak < unlatchRecentPeak
    if (lowNow) {
      _unlatchStreak += 1
    } else {
      _unlatchStreak = 0
    }

    if (_unlatchStreak >= UNLATCH_STREAK) {
      _glassesLatched = false
      _latchUntil = 0
      _probRing = _probRing.filter((v) => v < 0.35)
      _lastDetected = instant
      return
    }

    _lastDetected = true
    return
  }

  _lastDetected = instant
}

export async function initGlassesDetector() {
  if (DISABLE_GUARD) return null
  if (_detector) return _detector
  if (_loadPromise) return _loadPromise

  _loadPromise = (async () => {
    const { GlassesDetector } = await import('@framefind/core')
    const { blobUrl, sourceUrl } = await fetchModelBlobUrl()
    _modelBlobUrl = blobUrl

    const detector = new GlassesDetector({
      modelUrl: blobUrl,
      wasmPaths: resolveWasmPaths(),
      autoLandmarks: false,
      threshold: envNum('VITE_FRAMEFIND_THRESHOLD', DEFAULT_THRESHOLD),
      smoothingWindow: envNum('VITE_FRAMEFIND_SMOOTHING', DEFAULT_SMOOTHING),
      inferenceIntervalMs: 0,
      preferGpu: true,
    })
    await detector.load()
    console.info('[glassesGuard] FrameFind ready, model:', sourceUrl, 'mirror:', H5_MIRROR_FRONT_PREVIEW)
    _detector = detector
    _offscreen = document.createElement('canvas')
    return _detector
  })()

  try {
    return await _loadPromise
  } catch (e) {
    _loadPromise = null
    console.warn('[glassesGuard] FrameFind load failed', e)
    throw e
  }
}

export function disposeGlassesDetector() {
  if (_detector) {
    try {
      _detector.dispose()
    } catch (_) {}
    _detector = null
  }
  if (_modelBlobUrl) {
    URL.revokeObjectURL(_modelBlobUrl)
    _modelBlobUrl = null
  }
  _offscreen = null
  _mirrorCanvas = null
  _loadPromise = null
  resetGlassesGuardThrottle()
}

export async function detectGlassesOnVideoAsync(video, lmNorm) {
  if (DISABLE_GUARD) {
    return Promise.resolve({ detected: false, source: 'disabled' })
  }

  const now = performance.now()
  if (now - _lastCheckAt < CHECK_INTERVAL_MS) {
    return Promise.resolve({ detected: _lastDetected, throttled: true, source: 'cache' })
  }
  _lastCheckAt = now

  if (!video?.videoWidth || !video?.videoHeight || !lmNorm?.length) {
    if (!_glassesLatched) {
      _lastDetected = false
      _probRing = []
    }
    return { detected: _lastDetected, source: 'no_face' }
  }

  try {
    if (!_detector) await initGlassesDetector()

    const result = await detectOnFrame(video, lmNorm)
    const p = result?.probability ?? 0
    pushProbSample(p)
    const peak = latchPeakValue()
    const recentPeak = recentPeakValue()

    updateDetectedState(p, !!(result && result.glasses))

    if (import.meta.env?.DEV && import.meta.env?.VITE_FRAMEFIND_DEBUG === '1') {
      console.debug(
        '[glassesGuard]',
        'p=',
        p.toFixed(3),
        'peak=',
        peak.toFixed(3),
        'recent=',
        recentPeak.toFixed(3),
        'lib=',
        !!(result && result.glasses),
        'latched=',
        _glassesLatched,
        'unlatch=',
        _unlatchStreak,
        'hit=',
        _lastDetected
      )
    }

    return {
      detected: _lastDetected,
      probability: p,
      peakProbability: peak,
      recentPeakProbability: recentPeak,
      latched: _glassesLatched,
      faceDetected: result?.faceDetected ?? true,
      source: 'framefind',
    }
  } catch (e) {
    console.warn('[glassesGuard] detect failed', e)
    return { detected: _lastDetected, source: 'error' }
  }
}

export function mergeGlassesIntoGuideState(state, glassesResult) {
  const detected =
    glassesResult && typeof glassesResult.detected === 'boolean'
      ? glassesResult.detected
      : _lastDetected
  if (!detected) {
    return state
  }
  return {
    ...state,
    ok: false,
    hints: [...(state.hints || []), 'glasses'],
    hintMain: GLASSES_MSG,
    hintSub: GLASSES_SUB,
  }
}

export function resetGlassesGuardThrottle() {
  _lastCheckAt = 0
  _lastDetected = false
  _probRing = []
  _glassesLatched = false
  _latchUntil = 0
  _unlatchStreak = 0
  if (_detector) {
    try {
      _detector.resetHistory()
    } catch (_) {}
  }
}
