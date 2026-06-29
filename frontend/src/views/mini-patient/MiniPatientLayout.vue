<template>
  <div class="mini-patient-shell" data-testid="mini-patient-shell">
    <div class="mini-patient-frame">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>

    <van-tabbar v-model="active" route fixed safe-area-inset-bottom class="mini-tabbar">
      <van-tabbar-item icon="wap-home-o" to="/mini-patient">首页</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/mini-patient/ai">问诊</van-tabbar-item>
      <van-tabbar-item icon="calendar-o" to="/mini-patient/appointment">挂号</van-tabbar-item>
      <van-tabbar-item icon="records-o" to="/mini-patient/records">记录</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/mini-patient/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = ref(0)

watch(
  () => route.path,
  (path) => {
    if (path === '/mini-patient') active.value = 0
    else if (path.includes('/mini-patient/ai')) active.value = 1
    else if (path.includes('/mini-patient/appointment')) active.value = 2
    else if (path.includes('/mini-patient/records')) active.value = 3
    else if (path.includes('/mini-patient/orders') || path.includes('/mini-patient/profile')) active.value = 4
  },
  { immediate: true },
)
</script>

<style lang="scss" scoped>
.mini-patient-shell {
  min-height: 100vh;
  background: #f7f8fb;
  color: #243447;
}

.mini-patient-frame {
  width: 100%;
  min-height: 100vh;
  padding-bottom: 72px;
  background:
    linear-gradient(180deg, rgba(35, 117, 255, 0.09), rgba(247, 248, 251, 0) 250px),
    #f7f8fb;
}

.mini-tabbar {
  border-top: 1px solid #e6ebf2;
}

:deep(.van-tabbar-item--active) {
  color: #2375ff;
}
</style>
