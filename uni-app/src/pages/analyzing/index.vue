<template>
  <view class="page analyzing-page">
    <view class="center">
      <view class="ring">
        <view class="ring-inner" />
        <view class="dot-orbit" />
      </view>
      <text class="title">毫米级精准测算中</text>
      <text class="sub">{{ statusHint }}</text>
      <text v-if="error" class="err">{{ error }}</text>
      <button v-if="error" class="btn" @tap="retry">重试</button>
      <button v-if="error" class="btn ghost" @tap="goCapture">重新拍摄</button>
    </view>
  </view>
</template>

<script>
import { analyzeFace, tryOnFace, pingApi } from '../../utils/api.js'
import { getFacePath, setAnalyzeResult, setTryonCacheEntry } from '../../utils/session.js'
import { API_BASE } from '../../config/index.js'

export default {
  data() {
    return {
      error: '',
      statusHint: '正在连接测算服务…',
    }
  },
  onLoad() {
    this.run()
  },
  methods: {
    retry() {
      this.error = ''
      this.run()
    },
    goCapture() {
      uni.redirectTo({ url: '/pages/capture/index' })
    },
    async run() {
      const facePath = getFacePath()
      if (!facePath) {
        this.error = '未找到照片，请重新拍摄'
        return
      }
      try {
        this.statusHint = '正在连接测算服务…'
        await pingApi()
        this.statusHint = '正在分析面宽并匹配镜框…'
        const data = await analyzeFace(facePath)
        if (!data.ok) {
          if (data.error === 'GLASSES_ON_FACE') {
            this.error =
              data.message ||
              '检测到可能已佩戴眼镜，请摘下后重新拍摄。\n（取景时若已提示，可忽略本条）'
          } else {
            this.error = data.message || '测算失败'
          }
          return
        }
        const recs = data.recommendations || []
        if (!recs.length) {
          this.error = '暂无推荐镜架，请稍后重试'
          return
        }
        setAnalyzeResult(data.metrics, recs)

        try {
          const firstTryon = await tryOnFace(facePath, recs[0].id)
          setTryonCacheEntry(recs[0].id, firstTryon)
        } catch (e) {
          console.warn('prefetch tryon', e)
        }

        uni.redirectTo({ url: '/pages/workspace/index?frameIndex=0' })
      } catch (e) {
        const msg = (e && e.message) || String(e) || '网络异常'
        const base = API_BASE || '（H5 开发走 vite 代理 /api）'
        this.error = `${msg}\n请确认：① 已运行 python demo/app.py  ② API: ${base}`
      }
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$orange: #ff6b00;

.analyzing-page {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.center {
  text-align: center;
  padding: 48rpx;
}

.ring {
  width: 160rpx;
  height: 160rpx;
  margin: 0 auto 40rpx;
  position: relative;
}
.ring-inner {
  position: absolute;
  inset: 0;
  border: 8rpx solid rgba(26, 109, 255, 0.2);
  border-top-color: $blue;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.dot-orbit {
  position: absolute;
  top: -8rpx;
  left: 50%;
  width: 16rpx;
  height: 16rpx;
  margin-left: -8rpx;
  background: $orange;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
  transform-origin: 50% 88rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.title {
  display: block;
  font-size: 36rpx;
  font-weight: 600;
  color: $blue;
}
.sub {
  display: block;
  margin-top: 16rpx;
  font-size: 28rpx;
  color: #64748b;
}
.err {
  display: block;
  margin-top: 32rpx;
  font-size: 26rpx;
  color: #ef4444;
  white-space: pre-line;
  line-height: 1.5;
  text-align: left;
}
.btn {
  margin-top: 24rpx;
  background: $blue;
  color: #fff;
  border-radius: 48rpx;
}
.btn.ghost {
  background: transparent;
  color: $blue;
  border: 2rpx solid $blue;
}
</style>
