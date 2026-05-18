<template>
  <view v-if="visible" class="mask" @tap="$emit('close')">
    <view class="sheet" @tap.stop>
      <view class="handle" />
      <view class="tabs">
        <text
          v-for="t in tabs"
          :key="t.id"
          class="tab"
          :class="{ active: tab === t.id }"
          @tap="tab = t.id"
        >{{ t.label }}</text>
      </view>

      <view v-if="tab === 'beauty'" class="panel">
        <view class="chips">
          <text
            v-for="o in beautyOpts"
            :key="o"
            class="chip"
            :class="{ active: beauty === o }"
            @tap="applyBeauty(o)"
          >{{ o }}</text>
        </view>
        <text class="note">试戴满意后再美化；当前为前端示意，接入 SDK 后替换</text>
      </view>

      <view v-else-if="tab === 'hair'" class="panel">
        <scroll-view scroll-x class="hair-scroll">
          <view
            v-for="h in hairs"
            :key="h"
            class="hair-item"
            :class="{ active: hair === h }"
            @tap="hair = h"
          >{{ h }}</view>
        </scroll-view>
      </view>

      <view v-else class="panel">
        <view class="chips">
          <text
            v-for="s in scenes"
            :key="s"
            class="chip"
            :class="{ active: scene === s }"
            @tap="scene = s"
          >{{ s }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  props: {
    visible: { type: Boolean, default: false },
  },
  data() {
    return {
      tab: 'beauty',
      tabs: [
        { id: 'beauty', label: '美颜' },
        { id: 'hair', label: '发型' },
        { id: 'scene', label: '场景' },
      ],
      beauty: '自然',
      beautyOpts: ['关', '自然', '提亮'],
      hair: '推荐',
      hairs: ['推荐', '短发', '长发', '卷发'],
      scene: '原背景',
      scenes: ['原背景', '商务', '户外', '校园', '运动'],
    }
  },
  methods: {
    applyBeauty(o) {
      this.beauty = o
      if (o === '关') {
        this.$emit('preview', '')
        return
      }
      uni.showToast({ title: `美颜·${o}（待接入）`, icon: 'none' })
    },
  },
}
</script>

<style lang="scss" scoped>
$blue: #1a6dff;

.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}
.sheet {
  width: 100%;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 16rpx 24rpx 48rpx;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
}
.handle {
  width: 80rpx;
  height: 8rpx;
  background: #cbd5e1;
  border-radius: 4rpx;
  margin: 0 auto 24rpx;
}
.tabs {
  display: flex;
  gap: 24rpx;
  margin-bottom: 24rpx;
}
.tab {
  font-size: 30rpx;
  color: #64748b;
}
.tab.active {
  color: $blue;
  font-weight: 600;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.chip {
  padding: 16rpx 28rpx;
  background: #f1f5f9;
  border-radius: 32rpx;
  font-size: 28rpx;
}
.chip.active {
  background: $blue;
  color: #fff;
}
.note {
  display: block;
  margin-top: 20rpx;
  font-size: 24rpx;
  color: #94a3b8;
}
.hair-scroll {
  white-space: nowrap;
}
.hair-item {
  display: inline-block;
  padding: 20rpx 32rpx;
  margin-right: 16rpx;
  background: #f1f5f9;
  border-radius: 16rpx;
}
.hair-item.active {
  background: $blue;
  color: #fff;
}
</style>
