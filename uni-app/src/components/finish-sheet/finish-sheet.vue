<template>
  <view v-if="visible" class="mask" @tap="$emit('close')">
    <view class="sheet" @tap.stop>
      <text class="title">完成试戴</text>
      <image v-if="previewSrc" class="mini-preview" :src="previewSrc" mode="aspectFit" />

      <view class="action" @tap="onCart">
        <text class="ico">🛒</text>
        <text>加入购物车（跳转商品详情）</text>
      </view>
      <view class="action" @tap="onFavorite">
        <text class="ico">♡</text>
        <text>收藏</text>
      </view>
      <view class="action" @tap="onSave(true)">
        <text class="ico">↓</text>
        <text>保存到相册（有水印 · 待接 SDK）</text>
      </view>
      <view class="action accent" @tap="onSave(false)">
        <text class="ico">↓</text>
        <text class="accent-txt">保存高清（无水印 · 待接 SDK）</text>
      </view>
      <view class="action" @tap="onShare">
        <text class="ico">↗</text>
        <text>分享</text>
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
  },
  methods: {
    onCart() {
      uni.showToast({ title: '接入商品库后跳转 SKU', icon: 'none' })
    },
    onFavorite() {
      uni.showToast({ title: '已收藏（示意）', icon: 'none' })
    },
    onSave(watermark) {
      if (!this.previewSrc) {
        uni.showToast({ title: '暂无试戴图', icon: 'none' })
        return
      }
      // #ifdef H5
      uni.showToast({
        title: watermark ? 'H5 请长按图片保存' : '无水印版待后端提供',
        icon: 'none',
      })
      // #endif
      // #ifndef H5
      if (this.previewSrc.startsWith('data:')) {
        uni.showToast({ title: '保存功能需写入临时文件后调用相册 API', icon: 'none' })
        return
      }
      uni.saveImageToPhotosAlbum({
        filePath: this.previewSrc,
        success: () => uni.showToast({ title: '已保存', icon: 'success' }),
        fail: () => uni.showToast({ title: '保存失败，请检查相册权限', icon: 'none' }),
      })
      // #endif
    },
    onShare() {
      // #ifdef MP-WEIXIN
      uni.showToast({ title: '请使用 onShareAppMessage 配置', icon: 'none' })
      // #endif
      // #ifndef MP-WEIXIN
      uni.showToast({ title: '分享面板待接入 APP SDK', icon: 'none' })
      // #endif
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
