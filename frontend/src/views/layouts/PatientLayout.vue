<!-- src/views/layouts/PatientLayout.vue -->
<template>
  <div class="patient-app">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>

    <!-- 底部 Tabbar（登录页不显示） -->
    <van-tabbar v-if="showTabbar" v-model="active" route fixed>
      <van-tabbar-item icon="chat-o" to="/patient/ai">
        AI问诊
      </van-tabbar-item>
      <van-tabbar-item icon="records-o" to="/patient/records">
        病历
      </van-tabbar-item>
      <van-tabbar-item icon="bill-o" to="/patient/orders">
        缴费
      </van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/patient/profile">
        我的
      </van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = ref(0)

const showTabbar = computed(() => {
  return !['PatientLogin'].includes(route.name as string)
})

watch(() => route.path, (path) => {
  if (path.includes('/patient/ai')) active.value = 0
  else if (path.includes('/patient/records')) active.value = 1
  else if (path.includes('/patient/orders')) active.value = 2
  else if (path.includes('/patient/profile')) active.value = 3
}, { immediate: true })
</script>

<style lang="scss" scoped>
.patient-app {
  min-height: 100vh;
  padding-bottom: 50px;
}
</style>