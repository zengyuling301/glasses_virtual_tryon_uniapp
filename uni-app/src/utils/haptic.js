/**
 * 换款轻反馈：短震动（15ms），替代轻音效；H5 / App 均兼容。
 */
export function playSwitchFeedback() {
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      navigator.vibrate(15)
      return
    }
    const ret = uni.vibrateShort({
      type: 'light',
      fail: () => {},
    })
    if (ret && typeof ret.catch === 'function') {
      ret.catch(() => {})
    }
  } catch (_) {
    /* ignore */
  }
}
