<template>
  <view v-if="visible" class="mask" @tap="$emit('close')">
    <view class="sheet" @tap.stop>
      <text class="title">完成试戴</text>
      <image v-if="previewSrc" class="mini-preview" :src="previewSrc" mode="aspectFit" />

      <view class="action" @tap="onCart">
        <text class="ico">🛒</text>
        <text>加入购物车</text>
      </view>
      <view class="action" @tap="onFavorite">
        <text class="ico">♡</text>
        <text>收藏</text>
      </view>
      <view class="action" @tap="onSave(false)">
        <text class="ico">↓</text>
        <text>保存到相册</text>
      </view>
      <view class="action accent" @tap="onShare">
        <text class="ico">↗</text>
        <text class="accent-txt">分享</text>
      </view>

      <view class="divider" />
      <view class="action muted" @tap="$emit('remeasure')">
        <text>重新测脸</text>
      </view>
      <view class="action muted" @tap="$emit('close')">
        <text>取消</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  props: {
    visible: { type: Boolean, default: false },
    previewSrc: { type: String, default: '' },
    frame: { type: Object, default: null },
  },
  methods: {
    onCart() {
      if (!this.frame) {
        uni.showToast({ title: '未选中款式', icon: 'none' })
        return
      }
      const url = this.frame.product_url || `https://www.kxym.com/product/${this.frame.id}`
      // #ifdef H5
      window.open(url, '_blank')
      // #endif
      // #ifndef H5
      uni.navigateTo({ url: `/pages/webview/index?url=${encodeURIComponent(url)}` })
      // #endif
      this.$emit('close')
    },
    onFavorite() {
      if (!this.frame) {
        uni.showToast({ title: '未选中款式', icon: 'none' })
        return
      }
      const key = 'tryon_favorites'
      let list = []
      try {
        const raw = uni.getStorageSync(key)
        if (raw) list = JSON.parse(raw)
      } catch (_) {}
      const exists = list.some((item) => item.id === this.frame.id)
      if (exists) {
        uni.showToast({ title: '已收藏过', icon: 'none' })
        return
      }
      list.push({
        id: this.frame.id,
        name: this.frame.name,
        image: this.frame.image,
        mm_total_width: this.frame.mm_total_width,
        band: this.frame.band,
        savedAt: Date.now(),
      })
      uni.setStorageSync(key, JSON.stringify(list))
      uni.showToast({ title: '已收藏', icon: 'success' })
      this.$emit('close')
    },
    onSave(_watermark) {
      if (!this.previewSrc) {
        uni.showToast({ title: '暂无试戴图', icon: 'none' })
        return
      }
      // #ifdef H5
      if (this.previewSrc.startsWith('data:')) {
        const a = document.createElement('a')
        a.href = this.previewSrc
        a.download = 'tryon.png'
        a.click()
        uni.showToast({ title: '已开始下载', icon: 'success' })
      } else {
        uni.showToast({ title: '请长按图片保存', icon: 'none' })
      }
      // #endif
      // #ifndef H5
      let filePath = this.previewSrc
      if (this.previewSrc.startsWith('data:')) {
        // base64 写入临时文件
        const fs = uni.getFileSystemManager()
        const tmp = `${uni.env.USER_DATA_PATH}/tryon_${Date.now()}.png`
        const base64 = this.previewSrc.replace(/^data:image\/\w+;base64,/, '')
        try {
          fs.writeFileSync(tmp, base64, 'base64')
          filePath = tmp
        } catch (e) {
          uni.showToast({ title: '写入失败', icon: 'none' })
          return
        }
      }
      uni.saveImageToPhotosAlbum({
        filePath,
        success: () => uni.showToast({ title: '已保存', icon: 'success' }),
        fail: () => uni.showToast({ title: '保存失败，请检查相册权限', icon: 'none' }),
      })
      // #endif
      this.$emit('close')
    },
    onShare() {
      // #ifdef APP-PLUS
      uni.shareWithSystem({
        type: 'image',
        imageUrl: this.previewSrc || '',
        success: () => this.$emit('close'),
        fail: () => uni.showToast({ title: '分享失败', icon: 'none' }),
      })
      // #endif
      // #ifdef MP-WEIXIN
      uni.showShareMenu({
        withShareTicket: true,
        menus: ['shareAppMessage', 'shareTimeline'],
      })
      uni.showToast({ title: '点击右上角分享', icon: 'none' })
      // #endif
      // #ifdef H5
      uni.showToast({ title: '请使用浏览器分享', icon: 'none' })
      // #endif
      this.$emit('close')
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;
$orange: #ff6b00;

.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 110;
  display: flex;
  align-items: flex-end;
}
.sheet {
  width: 100%;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 32rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
}
.title {
  display: block;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 24rpx;
}
.mini-preview {
  width: 100%;
  height: 240rpx;
  margin-bottom: 24rpx;
  background: #f1f5f9;
  border-radius: 16rpx;
}
.action {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 28rpx 0;
  font-size: 30rpx;
  color: #1e293b;
  border-bottom: 1rpx solid #f1f5f9;
}
.action.accent .accent-txt {
  color: $orange;
  font-weight: 600;
}
.action.muted {
  justify-content: center;
  color: #64748b;
  border-bottom: none;
}
.ico {
  width: 48rpx;
  text-align: center;
}
.divider {
  height: 16rpx;
}
</style>
