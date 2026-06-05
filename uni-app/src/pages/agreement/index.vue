<template>
  <view class="page agreement-page">
    <!-- 顶栏：仅关闭按钮，与P1/P3风格一致 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarPx + 'px' }">
      <text class="nav-back" @tap="onClose">关闭</text>
    </view>

    <!-- 协议标题 -->
    <view class="header">
      <text class="header-title">用户许可协议</text>
      <text class="header-desc">请仔细阅读以下协议，滑到底部后可确认</text>
      <!-- 调试模式提示条 -->
      <view v-if="forceMode" class="debug-bar">
        <text class="debug-text">DEBUG: 强制 {{ forceMode.toUpperCase() }} 模式（跳过真实检测）</text>
        <text class="debug-close" @tap.stop="forceMode = ''">✕</text>
      </view>
    </view>

    <!-- 协议正文滚动区：动态 px 高度，避开 vh+flex 冲突 -->
    <scroll-view
      class="agreement-scroll"
      :style="{ height: scrollViewHeight + 'px' }"
      scroll-y
      scroll-with-animation
      @scrolltolower="onScrollToBottom"
      @scroll="onScroll"
    >
      <view class="agreement-content">
        <text class="section-title">一、服务说明</text>
        <text class="section-body">「开心玉米 AI 试戴」（以下简称"本功能"）是开心玉米 APP 内置的虚拟试戴功能模块。本功能通过人脸关键点检测与 3D 渲染技术，为用户提供眼镜虚拟试戴的视觉参考。</text>
        <text class="section-body">试戴效果为 AI 算法生成的视觉示意，不构成医疗验光建议。实际佩戴舒适度、适配度请以线下验光师或配镜专业人员意见为准。</text>

        <text class="section-title">二、面宽测算说明</text>
        <text class="section-body">本功能通过拍照采集人脸关键点坐标，结合镜框参数计算出面宽分档（S/M/L）与毫米级面宽估算值。该数值为 AI 模型推算结果，存在一定误差范围，不作为验光配镜的绝对依据。</text>
        <text class="section-body">镜片宽度×2 + 中梁宽度的总面宽计算公式为行业通用方法，实际商品适配请参考商品详情页的精确参数。</text>

        <text class="section-title">三、面部数据采集</text>
        <text class="section-body">拍照时本功能将采集您的面部特征点坐标数据（包括但不限于瞳距、面宽轮廓、鼻梁位置等），用于面宽测算与虚拟试戴合成。摄像头预览阶段进行实时人脸检测，但预览画面不会上传至服务器。</text>
        <text class="section-body">面部关键点数据仅在本功能的测算与试戴过程中使用，不会用于其他目的。试戴过程中系统不会对照片进行美颜或滤镜处理，确保面宽测算的准确性。</text>

        <text class="section-title">四、照片存储与隐私</text>
        <text class="section-body">您拍摄的照片将上传至服务器用于面宽分析与试戴图合成。合成完成后，您可选择将试戴效果图保存至本地相册、分享或用于商品下单。服务器端照片仅在试戴会话期间临时保存，会话结束后自动清除。</text>
        <text class="section-body">未经您明确授权，我们不会将您的面部数据或试戴照片用于任何其他目的，不会与第三方共享，不会用于广告推荐或用户画像。</text>

        <text class="section-title">五、摄像头与相册权限</text>
        <text class="section-body">本功能需要访问您的设备摄像头以进行实时拍照，以及访问相册以保存试戴效果图。摄像头仅在您点击「拍照」时激活，不会在后台静默采集。相册写入仅在您主动点击「保存」时执行。</text>
        <text class="section-body">您可以在设备的系统设置中随时关闭这些权限。关闭摄像头权限后，您可使用相册上传已有照片进行试戴。</text>

        <text class="section-title">六、使用限制与免责</text>
        <text class="section-body">本功能要求正面、清晰、无遮挡的自拍照片以获得较准确的测算结果。佩戴眼镜、墨镜或面部有较大面积遮挡时可能导致检测失败或结果偏差较大。</text>
        <text class="section-body">因光线条件、拍摄角度、设备分辨率等因素影响，测算结果可能存在差异。对于因依赖本功能测算结果而产生的任何购买决策，开心玉米不承担法律责任，建议结合线下试戴体验做出最终决定。</text>

        <text class="section-title">七、用户权利</text>
        <text class="section-body">您有权随时停止使用本功能，有权要求删除您的面部数据与历史试戴记录。您可在 APP「我的 → 试戴记录」中查看和管理您的历史记录，或联系客服进行数据清除。</text>
        <text class="section-body">如您对本功能的隐私保护或数据处理有任何疑问，可通过 APP 内「意见反馈」渠道联系我们。</text>

        <!-- 底部大留白确保滚动高度充足 -->
        <view class="scroll-spacer" />
      </view>
    </scroll-view>

    <!-- 底部操作区 -->
    <view class="footer" :style="{ paddingBottom: safeBottom + 'px' }">
      <!-- 滚动提示（未滑到底时显示） -->
      <view v-if="!hasScrolledToBottom" class="scroll-hint">
        <text class="scroll-hint-text">▼ 请继续向下滑动阅读全文 ▼</text>
      </view>

      <!-- 确认按钮 -->
      <button
        class="btn-agree"
        :class="{ 'btn-agree--ready': hasScrolledToBottom, 'btn-agree--loading': detecting }"
        :disabled="!hasScrolledToBottom || detecting"
        @tap="onAgree"
      >
        <text v-if="detecting">正在检测设备能力…</text>
        <text v-else-if="hasScrolledToBottom">已阅读并同意</text>
        <text v-else>请阅读完协议后确认</text>
      </button>

      <text class="legal-text">点击即表示您同意以上用户许可协议的全部条款</text>
    </view>
  </view>
</template>

<script>
import { setCaptureMode } from '../../utils/session.js'
import { detectDepthCapability } from '../../utils/depthDetect.js'

export default {
  data() {
    return {
      statusBarPx: 20,
      safeBottom: 0,
      scrollViewHeight: 400,
      hasScrolledToBottom: false,
      agreed: false,
      detecting: false,
      // 调试：URL 参数 ?forceMode=depth|reference 可跳过真实检测
      forceMode: '',
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarPx = sys.statusBarHeight || 20
    this.safeBottom = sys.safeAreaInsets?.bottom || 0
    this.calcScrollHeight(sys)
    // 调试模式：URL 参数 ?forceMode=depth|reference 可跳过真实景深检测
    if (options?.forceMode === 'depth' || options?.forceMode === 'reference') {
      this.forceMode = options.forceMode
      console.log('[P0] 调试强制模式已启用:', this.forceMode)
    }
    // 后台并行申请摄像头权限（不影响协议阅读）
    this.preRequestCameraPermission()
  },
  methods: {
    calcScrollHeight(sys) {
      // 动态计算 scroll-view 高度：窗口高度 - 顶栏 - header - footer - 安全区
      const wh = sys.windowHeight || 667
      const statusH = sys.statusBarHeight || 20
      // 顶栏约 44px + header 约 40px(标题) + 24px(描述) + 32px(padding*2) = ~140px
      const navHeaderH = statusH + 44 + 40 + 24 + 32
      // footer: 按钮 96rpx≈48px + 提示 24rpx≈12px + 声明 22rpx≈11px + padding 约 20px = ~91px
      const footerH = 48 + 12 + 11 + 20
      const safeBottom = sys.safeAreaInsets?.bottom || 0
      this.scrollViewHeight = Math.max(300, wh - navHeaderH - footerH - safeBottom)
    },
    onScroll(e) {
      // 修复：uni-app scroll-view @scroll 的 e.detail 没有 clientHeight
      // 仅依赖 scrollTop 和 scrollHeight：滚动进度 ≥ 88% 即视为到底
      if (this.hasScrolledToBottom) return
      const detail = e.detail || {}
      const st = detail.scrollTop ?? 0
      const sh = detail.scrollHeight ?? 0
      if (sh > 0 && st >= sh * 0.88) {
        this.markScrolledToBottom()
      }
    },
    onScrollToBottom() {
      if (this.hasScrolledToBottom) return
      this.markScrolledToBottom()
    },
    markScrolledToBottom() {
      if (this.hasScrolledToBottom) return
      this.hasScrolledToBottom = true
      // 震动反馈
      // #ifdef APP-PLUS
      plus.device.vibrate(30)
      // #endif
    },
    onClose() {
      uni.navigateBack({
        fail: () => {
          uni.showToast({ title: '已关闭', icon: 'none', duration: 1000 })
        },
      })
    },
    async onAgree() {
      if (!this.hasScrolledToBottom || this.agreed || this.detecting) return
      this.agreed = true
      this.detecting = true

      try {
        // 景深能力检测：决定 P1 走 depth（无参照物）还是 reference（须持参照物）
        // 有 forceMode 时直接传入，跳过真实检测
        const result = await detectDepthCapability({ forceMode: this.forceMode || undefined })
        console.log('[P0] 景深检测结果:', result)
        const mode = result.hasDepth ? 'depth' : 'reference'
        setCaptureMode(mode)
        console.log('[P0] capture_mode 已写入:', mode)
      } catch (e) {
        // 检测异常时保守降级为 reference 模式（无景深 → 须持参照物）
        console.warn('[P0] 景深检测异常，降级为 reference 模式:', e)
        setCaptureMode('reference')
      } finally {
        this.detecting = false
        // 跳转 P1 时携带 mode 参数（双重保险，storage + URL）
        const captureUrl = this.forceMode
          ? `/pages/capture/index?mode=${this.forceMode}`
          : '/pages/capture/index'
        uni.redirectTo({
          url: captureUrl,
          fail: () => {
            uni.navigateTo({ url: captureUrl })
          },
        })
      }
    },
    preRequestCameraPermission() {
      // #ifdef APP-PLUS
      plus.android.requestPermissions(
        ['android.permission.CAMERA'],
        () => {},
        () => {},
      )
      // #endif
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$orange: #ff6b00;

.agreement-page {
  /* 修复：min-height → height:100vh + overflow:hidden，避免 flex 嵌套高度漂移 */
  height: 100vh;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  padding: 8rpx 32rpx 16rpx;
  background: #fff;
  flex-shrink: 0;
}
.nav-back {
  color: $blue;
  font-size: 30rpx;
}

.header {
  padding: 32rpx 48rpx 24rpx;
  background: #fff;
  flex-shrink: 0;
}
.header-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #1e293b;
}
.header-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  color: #94a3b8;
}

/* 调试模式提示条 */
.debug-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
  padding: 12rpx 20rpx;
  background: #fef3c7;
  border-radius: 12rpx;
  border-left: 6rpx solid #f59e0b;
}
.debug-text {
  font-size: 24rpx;
  color: #92400e;
  flex: 1;
}
.debug-close {
  font-size: 28rpx;
  color: #92400e;
  padding: 4rpx 12rpx;
}

/* 协议滚动区 — 高度由 JS 动态绑定 style，不再依赖 flex:1 */
.agreement-scroll {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  margin: 0 16rpx;
  overflow: hidden;
}

.agreement-content {
  padding: 32rpx 40rpx;
  /* 删除 min-height: 120%，改用 padding-bottom + spacer 保证溢出 */
  padding-bottom: 160rpx;
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12rpx;
  margin-top: 36rpx;

  &:first-child {
    margin-top: 0;
  }
}

.section-body {
  display: block;
  font-size: 28rpx;
  line-height: 1.8;
  color: #475569;
  margin-bottom: 8rpx;
  text-indent: 2em;
}

/* 修复：spacer 从 80rpx 提到 400rpx，确保小屏机型也能触发滚动 */
.scroll-spacer {
  height: 400rpx;
}

/* 底部操作区 */
.footer {
  padding: 20rpx 32rpx 16rpx;
  background: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.scroll-hint {
  padding: 12rpx 0;
  margin-bottom: 8rpx;
}
.scroll-hint-text {
  font-size: 24rpx;
  color: $orange;
}

.btn-agree {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  background: #cbd5e1;
  color: #fff;
  transition: background 0.3s;

  &[disabled] {
    background: #cbd5e1;
    color: #fff;
  }

  &--ready {
    background: $blue;
    color: #fff;
  }

  &--loading {
    background: $blue;
    color: #fff;
    opacity: 0.8;
  }
}

.legal-text {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #94a3b8;
  text-align: center;
}
</style>
