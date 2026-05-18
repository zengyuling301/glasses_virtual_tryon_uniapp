<template>
  <view class="page workspace-page">
    <view class="nav" :style="{ paddingTop: statusBarPx + 'px' }">
      <text class="nav-back" @tap="onClose">关闭</text>
      <view class="nav-mid" @tap="toggleDetail">
        <text class="nav-title">{{ summaryLine }}</text>
        <text class="nav-chev">{{ detailOpen ? '▴' : '▾' }}</text>
      </view>
      <view class="nav-placeholder" />
    </view>

    <view v-if="detailOpen && metrics" class="detail-panel">
      <text class="detail-row">颊/瞳比 {{ metrics.cheek_over_ipd }}</text>
      <text class="detail-row">脸宽分档 {{ bandText }}</text>
      <text class="detail-row">瞳距约 {{ metrics.ipd_px }} px（示意，非验光）</text>
      <text v-if="metrics.low_confidence" class="detail-warn">{{ metrics.low_confidence_reason }}</text>
    </view>

    <view class="preview-zone">
      <swiper
        class="preview-swiper"
        :current="currentIndex"
        circular
        @change="onSwiperChange"
      >
        <swiper-item v-for="(item, idx) in recommendations" :key="item.id">
          <view class="slide">
            <image
              v-if="tryonSrc(item.id)"
              class="tryon-img"
              :src="tryonSrc(item.id)"
              mode="aspectFit"
            />
            <view v-else class="tryon-loading">
              <text>{{ idx === loadingIndex ? '合成中…' : '' }}</text>
            </view>
          </view>
        </swiper-item>
      </swiper>

      <view class="adapt-banner" :class="bannerClass">
        <text>{{ bannerText }}</text>
      </view>
    </view>

    <scroll-view class="thumb-bar" scroll-x :show-scrollbar="false">
      <view
        v-for="(item, idx) in recommendations"
        :key="'t-' + item.id"
        class="thumb-item"
        :class="{ active: idx === currentIndex }"
        @tap="selectIndex(idx)"
      >
        <image class="thumb-img" :src="thumbUrl(item.id)" mode="aspectFit" />
        <text class="thumb-tag" :class="tagClass(item)">{{ tagText(item) }}</text>
      </view>
    </scroll-view>

    <view class="swipe-hint">上滑可美颜 / 发型 / 场景（示意）</view>

    <view
      class="fab"
      :style="{ bottom: 200 + safeBottom + 'rpx' }"
      @tap="finishOpen = true"
    >
      完成
    </view>

    <enhance-drawer :visible="drawerOpen" @close="drawerOpen = false" @preview="onEnhancePreview" />
    <finish-sheet
      :visible="finishOpen"
      :preview-src="currentTryonSrc"
      @close="finishOpen = false"
      @remeasure="onRemeasure"
    />

    <view class="drawer-trigger" @tap="drawerOpen = true" />
  </view>
</template>

<script>
import { tryOnFace, framePreviewUrl } from '../../utils/api.js'
import {
  getFacePath,
  getMetrics,
  getRecommendations,
  getTryonCacheEntry,
  setTryonCacheEntry,
} from '../../utils/session.js'
import {
  faceSummaryLine,
  adaptBannerText,
  adaptLevel,
  matchStatusLabel,
  bandLabel,
} from '../../utils/adapt.js'
import EnhanceDrawer from '../../components/enhance-drawer/enhance-drawer.vue'
import FinishSheet from '../../components/finish-sheet/finish-sheet.vue'

export default {
  components: { EnhanceDrawer, FinishSheet },
  data() {
    return {
      statusBarPx: 20,
      safeBottom: 0,
      metrics: null,
      recommendations: [],
      currentIndex: 0,
      loadingIndex: -1,
      cache: {},
      detailOpen: false,
      drawerOpen: false,
      finishOpen: false,
      enhanceOverlay: '',
    }
  },
  computed: {
    currentFrame() {
      return this.recommendations[this.currentIndex] || null
    },
    summaryLine() {
      return faceSummaryLine(this.metrics, this.recommendations)
    },
    bandText() {
      return bandLabel(this.metrics && this.metrics.band)
    },
    bannerText() {
      return adaptBannerText(this.currentFrame)
    },
    bannerClass() {
      const lv = adaptLevel(this.currentFrame && this.currentFrame.match_status)
      return 'banner-' + lv
    },
    currentTryonSrc() {
      const id = this.currentFrame && this.currentFrame.id
      if (this.enhanceOverlay) return this.enhanceOverlay
      return id ? this.tryonSrc(id) : ''
    },
  },
  onLoad(query) {
    const sys = uni.getSystemInfoSync()
    this.statusBarPx = sys.statusBarHeight || 20
    this.safeBottom = sys.safeAreaInsets?.bottom || 0

    this.metrics = getMetrics()
    this.recommendations = getRecommendations()
    const idx = parseInt(query.frameIndex || '0', 10)
    this.currentIndex = Number.isFinite(idx) ? Math.min(idx, this.recommendations.length - 1) : 0

    if (!getFacePath() || !this.recommendations.length) {
      uni.redirectTo({ url: '/pages/capture/index' })
      return
    }

    const initCache = {}
    this.recommendations.forEach((r) => {
      const cached = getTryonCacheEntry(r.id)
      if (cached) initCache[r.id] = cached
    })
    this.cache = initCache

    this.ensureTryon(this.currentIndex)
  },
  methods: {
    tryonSrc(frameId) {
      return this.cache[frameId] || ''
    },
    thumbUrl(frameId) {
      return framePreviewUrl(frameId)
    },
    tagText(item) {
      return matchStatusLabel(item.match_status).slice(0, 4)
    },
    tagClass(item) {
      return adaptLevel(item.match_status)
    },
    toggleDetail() {
      this.detailOpen = !this.detailOpen
    },
    onClose() {
      uni.navigateBack({
        fail: () => uni.redirectTo({ url: '/pages/capture/index' }),
      })
    },
    onRemeasure() {
      uni.redirectTo({ url: '/pages/capture/index' })
    },
    onSwiperChange(e) {
      const idx = e.detail.current
      this.selectIndex(idx)
    },
    selectIndex(idx) {
      if (idx === this.currentIndex) return
      this.currentIndex = idx
      this.enhanceOverlay = ''
      this.ensureTryon(idx)
    },
    async ensureTryon(idx) {
      const frame = this.recommendations[idx]
      if (!frame || this.cache[frame.id]) return
      const facePath = getFacePath()
      this.loadingIndex = idx
      try {
        const src = await tryOnFace(facePath, frame.id)
        this.cache = { ...this.cache, [frame.id]: src }
        setTryonCacheEntry(frame.id, src)
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '试戴失败', icon: 'none' })
      } finally {
        this.loadingIndex = -1
      }
    },
    onEnhancePreview(src) {
      this.enhanceOverlay = src || ''
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$orange: #ff6b00;
$green: #22c55e;

.workspace-page {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  position: relative;
}

.nav {
  display: flex;
  align-items: center;
  padding: 8rpx 24rpx 16rpx;
  background: #fff;
}
.nav-back,
.nav-placeholder {
  width: 100rpx;
  font-size: 28rpx;
  color: #334155;
}
.nav-placeholder {
  width: 100rpx;
}
.nav-mid {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}
.nav-title {
  font-size: 26rpx;
  color: $blue;
  font-weight: 600;
  max-width: 420rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nav-chev {
  font-size: 22rpx;
  color: $blue;
}

.detail-panel {
  margin: 0 24rpx 12rpx;
  padding: 20rpx 24rpx;
  background: #fff;
  border: 2rpx solid $blue;
  border-radius: 16rpx;
}
.detail-row {
  display: block;
  font-size: 26rpx;
  color: #334155;
  line-height: 1.6;
}
.detail-warn {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #ef4444;
}

.preview-zone {
  flex: 1;
  margin: 0 24rpx;
  min-height: 52vh;
  background: #0f172a;
  border-radius: 20rpx;
  overflow: hidden;
  position: relative;
}
.preview-swiper,
.slide {
  height: 52vh;
}
.tryon-img {
  width: 100%;
  height: 100%;
}
.tryon-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 28rpx;
}

.adapt-banner {
  position: absolute;
  left: 16rpx;
  right: 16rpx;
  bottom: 16rpx;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;
  font-size: 26rpx;
  color: #fff;
}
.banner-fit {
  background: rgba(26, 109, 255, 0.92);
}
.banner-marginal {
  background: rgba(100, 116, 139, 0.92);
}
.banner-unfit {
  background: rgba(255, 107, 0, 0.92);
}

.thumb-bar {
  white-space: nowrap;
  padding: 20rpx 16rpx;
}
.thumb-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  width: 160rpx;
  margin-right: 16rpx;
  vertical-align: top;
  opacity: 0.65;
}
.thumb-item.active {
  opacity: 1;
  transform: scale(1.05);
}
.thumb-img {
  width: 140rpx;
  height: 72rpx;
  background: #fff;
  border-radius: 12rpx;
  border: 2rpx solid #e2e8f0;
}
.thumb-item.active .thumb-img {
  border-color: $blue;
}
.thumb-tag {
  margin-top: 8rpx;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  color: #fff;
}
.thumb-tag.fit {
  background: $green;
}
.thumb-tag.marginal {
  background: #eab308;
}
.thumb-tag.unfit {
  background: #ef4444;
}

.swipe-hint {
  text-align: center;
  font-size: 24rpx;
  color: #94a3b8;
  padding-bottom: 8rpx;
}

.drawer-trigger {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 120rpx;
  height: 80rpx;
  z-index: 5;
}

.fab {
  position: fixed;
  right: 32rpx;
  z-index: 20;
  width: 120rpx;
  height: 120rpx;
  line-height: 120rpx;
  text-align: center;
  border-radius: 60rpx;
  background: $blue;
  color: #fff;
  font-size: 30rpx;
  font-weight: 600;
  box-shadow: 0 8rpx 24rpx rgba(26, 109, 255, 0.45);
}
</style>
