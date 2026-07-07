<template>
  <div class="consult-page">
    <van-nav-bar title="在线咨询" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="consult-card">
      <van-icon name="chat-o" size="48" color="#4CAF50" />
      <strong>AI 问诊优先</strong>
      <p>当前系统已接入 AI 智能问诊，可根据症状给出科室推荐。需要医生处理时，可先完成挂号进入正式就诊流程。</p>
      <van-button type="primary" round block @click="router.push('/patient/ai')">进入 AI 问诊</van-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style lang="scss" scoped>
.consult-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.consult-card { display: grid; justify-items: center; gap: 12px; text-align: center; padding: 24px 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.consult-card strong { color: #1a1a2e; font-size: 18px; }
.consult-card p { margin: 0; color: #5b6b80; line-height: 1.65; }
.consult-card :deep(.van-button--primary) { background: #4caf50; border-color: #4caf50; }
</style>
