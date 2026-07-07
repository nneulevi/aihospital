<template>
  <div class="manager-page">
    <van-nav-bar title="就诊人管理" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="user-card">
      <van-icon name="user-circle-o" size="56" color="#4CAF50" />
      <div>
        <strong>{{ userStore.userInfo?.realName || userStore.userName || '患者用户' }}</strong>
        <p>{{ userStore.userInfo?.phone || '手机号未完善' }}</p>
        <small>{{ userStore.userInfo?.caseNumber ? `病历号：${userStore.userInfo.caseNumber}` : '当前默认就诊人' }}</small>
      </div>
    </section>
    <section class="info-card">
      <div class="section-title">使用说明</div>
      <p>当前系统已支持患者登录、挂号、病历、缴费和 AI 问诊。多就诊人切换可在后续接入家庭成员档案接口后扩展。</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
</script>

<style lang="scss" scoped>
.manager-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.user-card, .info-card { border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); padding: 16px; }
.user-card { display: flex; gap: 14px; align-items: center; }
.user-card strong { color: #1a1a2e; font-size: 17px; }
.user-card p { margin: 6px 0 3px; color: #5b6b80; }
.user-card small, .info-card p { color: #6b6b7e; line-height: 1.6; }
.info-card { margin-top: 12px; }
.section-title { margin-bottom: 8px; color: #1a1a2e; font-weight: 600; }
</style>
