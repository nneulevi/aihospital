<!-- src/views/layouts/DoctorLayout.vue -->
<template>
  <div class="doctor-app">
    <el-container>
      <el-header style="background:#005B96;color:white;display:flex;align-items:center;padding:0 20px;">
        <span style="font-size:18px;font-weight:bold;">👨‍⚕️ 医生端</span>
        <span style="margin-left:20px;font-size:14px;opacity:0.8;">Element Plus 已加载</span>
        <span style="margin-left:auto;font-size:14px;">
          <el-button type="text" style="color:white;" @click="goToPatient">去患者端</el-button>
        </span>
      </el-header>
      <el-main style="min-height:80vh;background:#F5F7FA;padding:20px;">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const goToPatient = () => router.push('/patient')
</script>

<style scoped>
.doctor-app {
  min-height: 100vh;
}
.el-header {
  --el-header-padding: 0 20px;
}
</style>