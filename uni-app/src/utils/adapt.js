/** 将 MVP 后端 match_status 映射为产品三级适配展示 */

const STATUS_LABEL = {
  MATCH: '精准适配',
  WARN_TOO_NARROW: '勉强可用',
  WARN_TOO_WIDE: '勉强可用',
  LOW_CONFIDENCE: '勉强可用',
}

const STATUS_LEVEL = {
  MATCH: 'fit',
  WARN_TOO_NARROW: 'marginal',
  WARN_TOO_WIDE: 'marginal',
  LOW_CONFIDENCE: 'marginal',
}

const BAND_LABEL = { S: '偏窄', M: '中等', L: '偏宽' }

export function matchStatusLabel(status) {
  return STATUS_LABEL[status] || status || '—'
}

export function adaptLevel(status) {
  return STATUS_LEVEL[status] || 'marginal'
}

export function adaptTagClass(level) {
  if (level === 'fit') return 'tag-fit'
  if (level === 'unfit') return 'tag-unfit'
  return 'tag-marginal'
}

export function bandLabel(band) {
  return BAND_LABEL[band] || band || '—'
}

/** 顶条展示用：MVP 无毫米面宽，用分档 + 推荐镜宽区间示意 */
export function faceSummaryLine(metrics, recommendations) {
  if (!metrics) return '测算中…'
  const band = bandLabel(metrics.band)
  const widths = (recommendations || [])
    .map((r) => r.mm_total_width)
    .filter((w) => typeof w === 'number')
  let range = ''
  if (widths.length) {
    const min = Math.min(...widths)
    const max = Math.max(...widths)
    range = ` · 推荐镜宽约 ${min}–${max} mm`
  }
  return `脸宽分档 ${band}${range}`
}

export function adaptBannerText(frame) {
  if (!frame) return ''
  const level = adaptLevel(frame.match_status)
  if (level === 'fit') return '精准适配 · 与您脸型示意更协调'
  if (frame.match_status === 'WARN_TOO_WIDE') return '镜架偏宽 · 佩戴可能下滑（示意）'
  if (frame.match_status === 'WARN_TOO_NARROW') return '镜架偏窄 · 可能夹脸（示意）'
  return frame.match_message || '勉强可用 · 建议多试几款对比'
}
