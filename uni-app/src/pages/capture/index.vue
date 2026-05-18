<template>
  <view class="page capture-page">
    <view class="nav-bar" :style="{ paddingTop: statusBarPx + 'px' }">
      <text class="nav-back" @tap="onBack">关闭</text>
    </view>

    <view class="preview-wrap">
      <!-- #ifdef H5 -->
      <!-- 原生 video 由 JS 插入 videoMount，避免 uni 包装导致 video.play 不可用 -->
      <view
        v-show="h5StreamActive"
        ref="videoMount"
        class="camera-mount"
        :class="{ 'camera-mount--hidden': !h5Live }"
      />
      <image
        v-if="!h5StreamActive && previewPath"
        class="preview-still"
        :src="previewPath"
        mode="aspectFill"
      />
      <view v-if="!h5StreamActive && !previewPath" class="preview-placeholder">
        <text class="ph-title">{{ placeholderTitle }}</text>
        <text class="ph-sub">{{ placeholderSub }}</text>
      </view>
      <!-- #endif -->

      <!-- #ifdef APP-PLUS || MP-WEIXIN -->
      <camera
        v-if="useLiveCamera"
        id="tryonCamera"
        class="camera"
        device-position="front"
        flash="off"
        @error="onCameraError"
        @initdone="onCameraReady"
      />
      <image
        v-if="previewPath && !useLiveCamera"
        class="preview-still"
        :src="previewPath"
        mode="aspectFill"
      />
      <!-- #endif -->

      <view class="align-frame" :class="ready ? 'is-ready' : ''">
        <view class="align-oval" />
        <view v-if="ready" class="align-dot" />
      </view>

      <view v-if="countdown > 0" class="countdown-layer">
        <text class="countdown-num">{{ countdown }}</text>
      </view>

      <view class="hint-bar">
        <text class="hint-main">{{ hintMain }}</text>
        <text v-if="hintSub" class="hint-sub">{{ hintSub }}</text>
      </view>
    </view>

    <view class="footer" :style="{ paddingBottom: safeBottom + 'px' }">
      <!-- #ifdef H5 -->
      <view v-if="!h5StreamActive || !h5Live" class="row">
        <button class="btn ghost" @tap="pickFrontCamera">前置拍照</button>
        <button class="btn ghost" @tap="pickAlbum">相册</button>
        <button v-if="canRetryLive" class="btn ghost" @tap="retryH5Camera">重试实时预览</button>
      </view>
      <!-- #endif -->
      <button class="btn primary" :disabled="!canShoot || counting" @tap="onShootTap">
        拍 照
      </button>
      <text class="legal">无美颜无滤镜 · 实时预览拍摄</text>
    </view>
  </view>
</template>

<script>
import { clearSession, setFacePath } from '../../utils/session.js'
import { getH5CameraBlockReason, pickImageViaNativeInput } from '../../utils/h5Env.js'
import { hapticReady } from '../../utils/haptic.js'
import { drawVideoToCanvas, H5_MIRROR_FRONT_PREVIEW } from '../../utils/h5Camera.js'

export default {
  data() {
    return {
      statusBarPx: 20,
      safeBottom: 0,
      useLiveCamera: true,
      h5Live: false,
      h5StreamActive: false,
      canRetryLive: true,
      mediaStream: null,
      h5VideoEl: null,
      placeholderTitle: '正在打开摄像头…',
      placeholderSub: '',
      previewPath: '',
      cameraReady: false,
      ready: false,
      hintMain: '正在打开摄像头…',
      hintSub: '',
      canShoot: false,
      counting: false,
      countdown: 0,
      _countTimer: null,
      guideLoop: null,
      guideReadyWas: false,
      guideModelLoading: false,
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarPx = sys.statusBarHeight || 20
    this.safeBottom = sys.safeAreaInsets?.bottom || 0
  },
  onReady() {
    // #ifdef H5
    this.initH5Camera()
    // #endif
  },
  onUnload() {
    this.clearCountdown()
  },
  beforeUnmount() {
    this.stopH5Camera()
  },
  methods: {
    onBack() {
      this.stopH5Camera()
      uni.navigateBack({ fail: () => uni.reLaunch({ url: '/pages/capture/index' }) })
    },
    stopH5Camera() {
      // #ifdef H5
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((t) => t.stop())
        this.mediaStream = null
      }
      this.h5StreamActive = false
      this.h5Live = false
      this.stopFaceGuide()
      this.destroyH5VideoEl()
      // #endif
    },
    stopFaceGuide() {
      if (this.guideLoop) {
        this.guideLoop.stop()
        this.guideLoop = null
      }
      this.guideReadyWas = false
      import('../../utils/glassesGuard.js')
        .then((m) => {
          m.resetGlassesGuardThrottle()
          m.disposeGlassesDetector()
        })
        .catch(() => {})
    },
    applyGuideState(state) {
      const wasOk = this.ready
      this.ready = !!state.ok
      this.canShoot = !!state.ok && this.h5Live && !this.counting
      this.hintMain = state.hintMain || '请调整姿势'
      this.hintSub = state.hintSub || ''
      if (state.ok && !wasOk) {
        hapticReady()
      }
      this.guideReadyWas = state.ok
    },
    async startFaceGuide() {
      this.stopFaceGuide()
      this.ready = false
      this.canShoot = false
      this.hintMain = '正在加载人脸检测…'
      this.hintSub = '首次约需数秒'
      this.guideModelLoading = true
      try {
        const { initFaceLandmarker, startVideoGuideLoop } = await import('../../utils/faceGuide.js')
        const { initGlassesDetector } = await import('../../utils/glassesGuard.js')
        this.hintSub = '正在加载眼镜检测模型…'
        await Promise.all([
          initFaceLandmarker(),
          initGlassesDetector().catch((e) => {
            console.warn('FrameFind init failed, glasses guard disabled', e)
          }),
        ])
        if (!this.h5VideoEl) return
        this.guideLoop = startVideoGuideLoop(this.h5VideoEl, (state) => this.applyGuideState(state))
        this.hintMain = '请将面部置于框内'
        this.hintSub = '对准后框变绿'
      } catch (e) {
        console.warn('faceGuide init failed', e)
        this.hintMain = '人脸检测不可用，仍可直接拍摄'
        this.hintSub = '请确保网络可访问模型 CDN，或配置代理'
        this.markReady()
      } finally {
        this.guideModelLoading = false
      }
    },
    getVideoMountEl() {
      const ref = this.$refs.videoMount
      if (!ref) return null
      const el = ref.$el || ref
      return el && el.nodeType === 1 ? el : null
    },
    destroyH5VideoEl() {
      if (this.h5VideoEl) {
        this.h5VideoEl.srcObject = null
        this.h5VideoEl.remove()
        this.h5VideoEl = null
      }
    },
    ensureH5VideoEl() {
      if (this.h5VideoEl && this.h5VideoEl.parentNode) {
        return this.h5VideoEl
      }
      const mount = this.getVideoMountEl()
      if (!mount) return null
      this.destroyH5VideoEl()
      const video = document.createElement('video')
      video.setAttribute('data-live-preview', '1')
      video.className = H5_MIRROR_FRONT_PREVIEW ? 'camera-native mirror-fix' : 'camera-native'
      video.autoplay = true
      video.playsInline = true
      video.setAttribute('playsinline', 'true')
      video.setAttribute('webkit-playsinline', 'true')
      video.muted = true
      mount.appendChild(video)
      this.h5VideoEl = video
      return video
    },
    // #ifdef H5
    async initH5Camera() {
      this.hintMain = '正在打开摄像头…'
      this.hintSub = '若长时间无画面，请点「重试实时预览」'
      this.canShoot = false
      this.h5Live = false
      const block = getH5CameraBlockReason()
      if (block) {
        this.h5StreamActive = false
        this.canRetryLive = block.code !== 'insecure'
        this.hintMain = block.message
        this.hintSub = block.hint
        this.placeholderTitle = block.message
        this.placeholderSub = block.hint
        return
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        })
        this.mediaStream = stream
        await this.bindStreamToVideo(stream)
      } catch (e) {
        this.h5StreamActive = false
        this.onH5CameraFail(e.message || '请允许使用摄像头')
      }
    },
    async bindStreamToVideo(stream) {
      this.h5StreamActive = true
      this.placeholderTitle = '正在连接摄像头…'
      await this.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      let video = this.ensureH5VideoEl()
      if (!video) {
        await new Promise((r) => setTimeout(r, 200))
        video = this.ensureH5VideoEl()
      }
      if (!video || typeof video.play !== 'function') {
        throw new Error('预览组件未就绪，请点重试')
      }

      video.srcObject = stream

      let done = false
      const finish = () => {
        if (done) return
        done = true
        const playRet = video.play()
        const onPlaying = () => {
          this.h5Live = true
          this.cameraReady = true
          this.ready = false
          this.canShoot = false
          this.startFaceGuide()
        }
        if (playRet && typeof playRet.then === 'function') {
          playRet.then(onPlaying).catch((err) => {
            this.onH5CameraFail(err.message || '无法播放预览')
          })
        } else {
          onPlaying()
        }
      }

      video.onloadedmetadata = finish
      video.onloadeddata = finish
      if (video.readyState >= 2) {
        finish()
        return
      }
      setTimeout(() => {
        if (!this.h5Live && this.mediaStream) finish()
      }, 1500)
    },
    onH5CameraFail(msg) {
      this.stopFaceGuide()
      this.h5StreamActive = false
      this.h5Live = false
      this.destroyH5VideoEl()
      this.hintMain = msg
      this.hintSub = '请用「前置拍照」或「相册」'
      this.placeholderTitle = msg
      this.placeholderSub = '请用「前置拍照」或「相册」'
      this.canShoot = false
    },
    async pickFrontCamera() {
      try {
        const url = await pickImageViaNativeInput({ capture: 'user' })
        this.stopH5Camera()
        this.previewPath = url
        this.markReady()
      } catch (_) {
        /* 用户取消 */
      }
    },
    retryH5Camera() {
      this.stopH5Camera()
      this.initH5Camera()
    },
    captureH5Frame() {
      const video = this.h5VideoEl
      if (!video || !video.videoWidth) {
        uni.showToast({ title: '摄像头未就绪', icon: 'none' })
        return
      }
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      drawVideoToCanvas(ctx, video, canvas.width, canvas.height)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
      this.stopH5Camera()
      this.goAnalyze(dataUrl)
    },
    // #endif
    onCameraReady() {
      this.cameraReady = true
      this.markReady()
    },
    onCameraError() {
      this.useLiveCamera = false
      this.hintMain = '相机不可用，请使用相册'
      this.hintSub = ''
    },
    markReady() {
      this.ready = true
      this.canShoot = true
      this.hintMain = '已对准，请点击下方拍摄'
      this.hintSub = '点击后将开始 3 秒倒计时'
    },
    pickAlbum() {
      uni.chooseImage({
        count: 1,
        sourceType: ['album'],
        sizeType: ['compressed'],
        success: (res) => {
          const path = res.tempFilePaths[0]
          if (!path) return
          this.stopH5Camera()
          this.previewPath = path
          this.markReady()
        },
      })
    },
    onShootTap() {
      if (!this.canShoot || this.counting) return
      this.startCountdown(() => this.capturePhoto())
    },
    startCountdown(done) {
      this.counting = true
      this.countdown = 3
      this.clearCountdown()
      const tick = () => {
        if (this.countdown <= 1) {
          this.countdown = 0
          this.counting = false
          done()
          return
        }
        this.countdown -= 1
        this._countTimer = setTimeout(tick, 1000)
      }
      this._countTimer = setTimeout(tick, 1000)
    },
    clearCountdown() {
      if (this._countTimer) {
        clearTimeout(this._countTimer)
        this._countTimer = null
      }
    },
    capturePhoto() {
      // #ifdef H5
      if (this.h5Live && this.cameraReady) {
        this.captureH5Frame()
        return
      }
      if (this.previewPath) {
        this.goAnalyze(this.previewPath)
        return
      }
      uni.showToast({ title: '请先允许摄像头或选择相册', icon: 'none' })
      return
      // #endif

      // #ifdef APP-PLUS || MP-WEIXIN
      if (this.useLiveCamera && this.cameraReady) {
        const ctx = uni.createCameraContext()
        ctx.takePhoto({
          quality: 'high',
          success: (res) => this.goAnalyze(res.tempImagePath),
          fail: () => uni.showToast({ title: '拍摄失败', icon: 'none' }),
        })
        return
      }
      // #endif
      if (this.previewPath) {
        this.goAnalyze(this.previewPath)
        return
      }
      uni.showToast({ title: '请先对准并等待摄像头就绪', icon: 'none' })
    },
    goAnalyze(filePath) {
      clearSession()
      setFacePath(filePath)
      uni.navigateTo({ url: '/pages/analyzing/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$green: #22c55e;
$orange: #ff6b00;

.capture-page {
  min-height: 100vh;
  background: #0f172a;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  padding: 8rpx 32rpx 16rpx;
}
.nav-back {
  color: #fff;
  font-size: 30rpx;
}

.preview-wrap {
  flex: 1;
  position: relative;
  overflow: hidden;
  margin: 0 24rpx;
  border-radius: 24rpx;
  background: #000;
}

.camera-mount {
  width: 100%;
  min-height: 68vh;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #000;
}
.camera-mount--hidden {
  opacity: 0;
}
.camera-mount :deep(.camera-native),
.camera-mount .camera-native {
  width: 100%;
  height: 68vh;
  min-height: 68vh;
  object-fit: cover;
  display: block;
  background: #000;
}
.camera-mount :deep(.camera-native.mirror-fix),
.camera-mount .camera-native.mirror-fix {
  transform: scaleX(-1);
}

.preview-still {
  width: 100%;
  height: 100%;
  min-height: 68vh;
  object-fit: cover;
  display: block;
}

.preview-placeholder {
  min-height: 68vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
.ph-title {
  font-size: 36rpx;
  color: #e2e8f0;
}
.ph-sub {
  margin-top: 12rpx;
  font-size: 26rpx;
  text-align: center;
  padding: 0 32rpx;
}

.align-frame {
  position: absolute;
  left: 0;
  right: 0;
  top: 18%;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  z-index: 2;
}
.align-oval {
  width: 420rpx;
  height: 520rpx;
  border: 4rpx solid $blue;
  border-radius: 48% 48% 44% 44%;
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.35);
  transition: border-color 0.25s;
}
.align-frame.is-ready .align-oval {
  border-color: $green;
}
.align-dot {
  width: 20rpx;
  height: 20rpx;
  margin-top: 24rpx;
  border-radius: 50%;
  background: $orange;
  box-shadow: 0 0 16rpx $orange;
}

.countdown-layer {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.45);
}
.countdown-num {
  font-size: 144rpx;
  font-weight: 700;
  color: $orange;
}

.hint-bar {
  position: absolute;
  left: 24rpx;
  right: 24rpx;
  bottom: 32rpx;
  z-index: 2;
  padding: 20rpx 24rpx;
  background: rgba(26, 109, 255, 0.92);
  border-radius: 16rpx;
}
.hint-main {
  display: block;
  color: #fff;
  font-size: 28rpx;
}
.hint-sub {
  display: block;
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.85);
  font-size: 24rpx;
}

.footer {
  padding: 24rpx 32rpx 16rpx;
}
.row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.btn {
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 48rpx;
  font-size: 32rpx;
  border: none;
}
.btn.primary {
  background: $blue;
  color: #fff;
}
.btn.primary[disabled] {
  background: #64748b;
  color: #cbd5e1;
}
.btn.ghost {
  flex: 1;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}
.legal {
  display: block;
  margin-top: 16rpx;
  text-align: center;
  font-size: 22rpx;
  color: #64748b;
}
</style>
