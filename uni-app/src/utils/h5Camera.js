/**
 * H5 前置摄像头：预览镜像与 canvas 抓帧（与画面一致）
 */

/** 前置预览是否水平翻转（Chrome 默认镜像，翻回真实左右） */
export const H5_MIRROR_FRONT_PREVIEW = true

export function drawVideoToCanvas(ctx, video, width, height, { mirror = H5_MIRROR_FRONT_PREVIEW } = {}) {
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  if (mirror) {
    ctx.translate(width, 0)
    ctx.scale(-1, 1)
  }
  ctx.drawImage(video, 0, 0, width, height)
  ctx.setTransform(1, 0, 0, 1, 0, 0)
}
