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
    </view>

    <!-- 协议正文滚动区 -->
    <scroll-view
      class="agreement-scroll"
      style="height: 60vh"
      scroll-y
      :scroll-top="scrollTop"
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

        <!-- 底部留白，确保内容有足够高度触发滚动 -->
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
        :class="{ 'btn-agree--ready': hasScrolledToBottom }"
        :disabled="!hasScrolledToBottom"
        @tap="onAgree"
      >
        {{ hasScrolledToBottom ? '已阅读并同意' : '请阅读完协议后确认' }}
      </button>

      <text class="legal-text">点击即表示您同意以上用户许可协议的全部条款</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarPx: 20,
      safeBottom: 0,
      hasScrolledToBottom: false,
      scrollTop: 0,
      agreed: false,
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarPx = sys.statusBarHeight || 20
    this.safeBottom = sys.safeAreaInsets?.bottom || 0
    // 后台并行申请摄像头权限（不影响协议阅读）
    this.preRequestCameraPermission()
  },
  methods: {
    onScroll(e) {
      // @scroll 兜底：手动计算滚动位置，跨平台兼容性更好
      if (this.hasScrolledToBottom) return
      const detail = e.detail || e.target || {}
      const st = detail.scrollTop ?? 0
      const sh = detail.scrollHeight ?? 0
      const ch = detail.clientHeight ?? 0
      // 滚动到距底部 16px 以内即视为已到底
      if (sh > 0 && ch > 0 && st + ch >= sh - 16) {
        this.markScrolledToBottom()
      }
    },
    onScrollToBottom() {
      if (this.hasScrolledToBottom) return
      this.markScrolledToBottom()
    },
    markScrolledToBottom() {
      this.hasScrolledToBottom = true
      // 震动反馈（仅在支持的机型上生效）
      // #ifdef APP-PLUS
      plus.device.vibrate(30)
      // #endif
    },
    onClose() {
      uni.navigateBack({
        fail: () => {
          // 无历史栈时退出当前页面
          uni.showToast({ title: '已关闭', icon: 'none', duration: 1000 })
        },
      })
    },
    async onAgree() {
      if (!this.hasScrolledToBottom || this.agreed) return
      this.agreed = true

      // 后台已预申请摄像头权限，此处直接跳转拍照页
      uni.redirectTo({
        url: '/pages/capture/index',
        fail: () => {
          uni.navigateTo({ url: '/pages/capture/index' })
        },
      })
    },
    preRequestCameraPermission() {
      // 后台并行申请摄像头权限，不阻塞用户阅读协议
      // #ifdef APP-PLUS
      plus.android.requestPermissions(
        ['android.permission.CAMERA'],
        (_result) => {
          // 静默处理，不打扰用户
        },
        (_error) => {},
      )
      // #endif

      // #ifdef H5
      // H5 环境下在拍照页才会触发 getUserMedia，此处仅做标记
      // #endif
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$orange: #ff6b00;
$green: #22c55e;

.agreement-page {
  min-height: 100vh;
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

/* 协议滚动区 */
.agreement-scroll {
  flex: 1;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  margin: 0 16rpx;
  overflow: hidden;
}

.agreement-content {
  padding: 32rpx 40rpx;
  /* min-height: 120% 确保短内容也有足够高度触发 scrolltolower */
  min-height: 120%;
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

.scroll-spacer {
  height: 80rpx;
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
}

.legal-text {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #94a3b8;
  text-align: center;
}
</style>
