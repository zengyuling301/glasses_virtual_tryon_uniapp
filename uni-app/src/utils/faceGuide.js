/**
 * H5 实时人脸对齐引导（MediaPipe Face Landmarker，与后端同系 478 点模型）
 */

const WASM_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.17/wasm'
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task'

const LM_RIGHT_OUTER = 33
const LM_LEFT_OUTER = 263
const LM_RIGHT_INNER = 133
const LM_LEFT_INNER = 362
const LM_NOSE = 1

/** 阈值（可按业务标定） */
const MIN_IPD_PX = 28
const MAX_IPD_FRAC = 0.38
const MIN_IPD_FRAC = 0.1
const MAX_ROLL_DEG = 14
const MAX_YAW_NORM = 0.14
const MAX_CENTER_OFF_X = 0.14
const MAX_CENTER_OFF_Y = 0.18

let landmarker = null
let initPromise = null

function pt(lm, i) {
  return lm[i]
}

function irisCentersNorm(lm) {
  if (lm.length > 473) {
    let pl = { x: 0, y: 0 }
    let pr = { x: 0, y: 0 }
    for (let i = 0; i < 5; i++) {
      pl.x += lm[468 + i].x
      pl.y += lm[468 + i].y
      pr.x += lm[473 + i].x
      pr.y += lm[473 + i].y
    }
    pl.x /= 5
    pl.y /= 5
    pr.x /= 5
    pr.y /= 5
    if (pl.x < pr.x) {
      const t = pl
      pl = pr
      pr = t
    }
    return { pr, pl }
  }
  let pr = pt(lm, LM_RIGHT_INNER)
  let pl = pt(lm, LM_LEFT_INNER)
  if (pr.x > pl.x) {
    const t = pr
    pr = pl
    pl = t
  }
  return { pr, pl }
}

function headRollDeg(lm) {
  let pr = pt(lm, LM_RIGHT_OUTER)
  let pl = pt(lm, LM_LEFT_OUTER)
  if (pr.x > pl.x) {
    const t = pr
    pr = pl
    pl = t
  }
  const dx = pl.x - pr.x
  const dy = pl.y - pr.y
  return Math.abs((Math.atan2(dy, dx) * 180) / Math.PI)
}

function yawAsymmetry(lm) {
  const pr = pt(lm, LM_RIGHT_OUTER)
  const pl = pt(lm, LM_LEFT_OUTER)
  const mid = { x: (pr.x + pl.x) / 2, y: (pr.y + pl.y) / 2 }
  const nose = pt(lm, LM_NOSE)
  const inter = Math.hypot(pl.x - pr.x, pl.y - pr.y) || 1e-6
  return Math.abs(nose.x - mid.x) / inter
}

/**
 * @param {Array<{x:number,y:number,z:number}>} lm 归一化关键点
 * @param {number} vw 视频宽 px
 * @param {number} vh 视频高 px
 */
export function assessFaceAlignment(lm, vw, vh) {
  const hints = []
  const minSide = Math.min(vw, vh)

  const { pr, pl } = irisCentersNorm(lm)
  const ipdPx = Math.hypot((pl.x - pr.x) * vw, (pl.y - pr.y) * vh)

  const nose = pt(lm, LM_NOSE)
  const cx = nose.x - 0.5
  const cy = nose.y - 0.42

  if (ipdPx < MIN_IPD_PX) {
    hints.push('请靠近一些')
  }
  if (ipdPx > MAX_IPD_FRAC * minSide) {
    hints.push('请离远一些')
  }
  if (ipdPx < MIN_IPD_FRAC * minSide) {
    hints.push('请靠近一些')
  }
  if (headRollDeg(lm) > MAX_ROLL_DEG) {
    hints.push('脸请摆正')
  }
  if (yawAsymmetry(lm) > MAX_YAW_NORM) {
    hints.push('请正面面对镜头')
  }
  if (Math.abs(cx) > MAX_CENTER_OFF_X) {
    hints.push('请将面部移至框中央')
  }
  if (Math.abs(cy) > MAX_CENTER_OFF_Y) {
    hints.push(cy > 0 ? '请略微抬头' : '请略微低头')
  }

  const ok = hints.length === 0
  return {
    ok,
    hints,
    hintMain: ok ? '已对准，请点击下方拍摄' : hints[0] || '请调整姿势',
    hintSub: ok ? '点击后将开始 3 秒倒计时' : hints.slice(1).join(' · ') || '对准后框变绿',
    ipdPx: Math.round(ipdPx),
  }
}

export async function initFaceLandmarker(modelUrl = MODEL_URL) {
  if (landmarker) return landmarker
  if (initPromise) return initPromise

  initPromise = (async () => {
    const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')
    const vision = await FilesetResolver.forVisionTasks(WASM_CDN)
    landmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: modelUrl,
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numFaces: 1,
      minFaceDetectionConfidence: 0.5,
      minFacePresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    })
    return landmarker
  })()

  try {
    return await initPromise
  } catch (e) {
    initPromise = null
    throw e
  }
}

export function closeFaceLandmarker() {
  if (landmarker) {
    try {
      landmarker.close()
    } catch (_) {}
    landmarker = null
  }
  initPromise = null
}

/**
 * 启动视频帧检测循环
 * @returns {{ stop: () => void }}
 */
export function startVideoGuideLoop(video, onState) {
  let raf = 0
  let lastTs = -1
  let loading = false

  const tick = async () => {
    raf = requestAnimationFrame(tick)
    if (!video || video.readyState < 2 || !landmarker) return
    if (loading) return

    const ts = performance.now()
    if (ts === lastTs) return
    lastTs = ts

    loading = true
    try {
      const result = landmarker.detectForVideo(video, ts)
      const vw = video.videoWidth
      const vh = video.videoHeight
      if (!result.faceLandmarks || !result.faceLandmarks.length) {
        onState({
          ok: false,
          hints: ['no_face'],
          hintMain: '请将面部置于框内',
          hintSub: '保持正面、光线均匀',
          ipdPx: 0,
        })
        return
      }
      onState(assessFaceAlignment(result.faceLandmarks[0], vw, vh))
    } catch (_) {
      /* 单帧失败忽略 */
    } finally {
      loading = false
    }
  }

  raf = requestAnimationFrame(tick)

  return {
    stop() {
      if (raf) cancelAnimationFrame(raf)
      raf = 0
    },
  }
}
