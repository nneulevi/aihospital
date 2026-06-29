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
      <van-tabbar-item icon="home-o" to="/patient/home">
        首页
      </van-tabbar-item>
      <van-tabbar-item icon="records-o" to="/patient/appointments">
        挂号记录
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
  if (path.includes('/patient/home')) active.value = 0
  else if (path.includes('/patient/appointments')) active.value = 1
  else if (path.includes('/patient/profile')) active.value = 2
}, { immediate: true })
</script>

<style lang="scss" scoped>
.patient-app {
  min-height: 100vh;
  padding-bottom: 50px;
  background: #F5F7FA;
}
</style>