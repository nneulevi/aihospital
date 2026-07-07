<template>
  <div class="schedule-page">
    <van-nav-bar title="出诊查询" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="schedule-card">
      <strong>按科室查看医生排班</strong>
      <p>当前真实排班号源已在“预约挂号”流程中接入，可选择科室、日期和午别查看可挂号医生。</p>
      <van-button type="primary" round block @click="router.push('/patient/appointment')">去预约挂号</van-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style lang="scss" scoped>
.schedule-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.schedule-card { display: grid; gap: 12px; padding: 18px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.schedule-card strong { color: #1a1a2e; }
.schedule-card p { margin: 0; color: #5b6b80; line-height: 1.65; }
.schedule-card :deep(.van-button--primary) { background: #4caf50; border-color: #4caf50; }
</style>
