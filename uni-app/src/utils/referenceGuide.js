/**
 * 参照物检测引导模块（W1 占位版）
 *
 * 用于 reference 模式下引导用户放置参照物并确认就绪。
 * W1 版本为手动确认方式（用户点击参照物框区域触发），
 * W2 将替换为真实检测逻辑（MediaPipe Object Detection 或 OpenCV 传统视觉）。
 *
 * 调用方式：
 *   const refGuide = startReferenceGuide(video, onState)
 *   // 用户交互后调用 refGuide.manualConfirm() 标记参照物已就绪
 *   // 离开页面时调用 refGuide.stop()
 */

/**
 * 启动参照物引导（W1 占位版：不启动实际检测循环，由 P1 页面 UI 交互驱动状态）
 *
 * @param {HTMLVideoElement} _video - 视频元素（W1 暂未使用，W2 接入真实检测时需要）
 * @param {Function} onState - 状态回调: (state) => void
 *   state 结构：{ refDetected: boolean, refCalibData: Object|null, hints: string[] }
 * @returns {{ stop: Function, manualConfirm: Function, reset: Function }}
 */
export function startReferenceGuide(_video, onState) {
  let active = true

  /**
   * 手动确认参照物已放置到位
   * 由 P1 页面的 onRefManualConfirm() 调用
   */
  const manualConfirm = () => {
    if (!active) return
    onState({
      refDetected: true,
      refCalibData: {
        method: 'manual',    // 标识为手动确认（W1 占位）
        type: 'card',        // 参照物类型：银行卡/标定卡
        confirmedAt: Date.now(),
      },
      hints: [],
    })
  }

  /**
   * 重置参照物状态（参照物移出画面或需重新拍摄时调用）
   */
  const reset = () => {
    if (!active) return
    onState({
      refDetected: false,
      refCalibData: null,
      hints: ['请将参照物置于框内'],
    })
  }

  /**
   * 停止引导（页面卸载时调用，释放资源）
   * W1 无需释放资源；W2 接入检测模型后在此处停止检测循环
   */
  const stop = () => {
    active = false
  }

  return { stop, manualConfirm, reset }
}

/**
 * 预定义的参照物类型配置（供 UI 展示和后续算法匹配使用）
 *
 * W1 仅用于展示文案和图标提示；
 * W2 算法侧将根据 type 加载对应的模板/模型进行检测。
 */
export const REFERENCE_TYPES = {
  card: {
    name: '银行卡',
    desc: '标准银行卡尺寸 85.6×54mm',
    icon: '💳',
    color: '#1a6dff',
  },
  ruler: {
    name: '标定尺',
    desc: '专用标定卡/直尺',
    icon: '📏',
    color: '#22c55e',
  },
}

/**
 * 默认使用的参照物类型
 * 可在甲方确认规格后修改此值
 */
export const DEFAULT_REFERENCE_TYPE = 'card'
