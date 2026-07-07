<!-- src/views/layouts/PatientLayout.vue -->
<template>
  <div class="patient-app">
    <router-view />

    <!-- 底部 Tabbar（登录页不显示） -->
    <van-tabbar v-if="showTabbar" route fixed>
      <van-tabbar-item icon="home-o" to="/patient/home" @click="navigate('/patient/home')">
        首页
      </van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/patient/ai" @click="navigate('/patient/ai')">
        AI问诊
      </van-tabbar-item>
      <van-tabbar-item icon="records-o" to="/patient/records" @click="navigate('/patient/records')">
        病历
      </van-tabbar-item>
      <van-tabbar-item icon="bill-o" to="/patient/orders" @click="navigate('/patient/orders')">
        缴费
      </van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/patient/profile" @click="navigate('/patient/profile')">
        我的
      </van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const showTabbar = computed(() => {
  return !['PatientLogin'].includes(route.name as string)
})

const navigate = (path: string) => {
  if (route.path !== path) {
    router.replace(path)
  }
}
</script>

<style lang="scss" scoped>
.patient-app {
  min-height: 100vh;
  padding-bottom: 50px;
}
</style>
