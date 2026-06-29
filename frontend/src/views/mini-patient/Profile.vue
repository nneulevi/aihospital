<template>
  <main class="mini-page">
    <section class="profile-card">
      <van-icon name="user-circle-o" size="64" color="#2375ff" />
      <h1>{{ userStore.userName || '患者用户' }}</h1>
      <p>{{ displayPhone || '手机号未登记' }}</p>
    </section>

    <section class="menu-list">
      <button type="button" @click="router.push('/mini-patient/records')">
        <van-icon name="records-o" />
        <span>我的病历</span>
        <van-icon name="arrow" />
      </button>
      <button type="button" @click="router.push('/mini-patient/orders')">
        <van-icon name="bill-o" />
        <span>门诊缴费</span>
        <van-icon name="arrow" />
      </button>
      <button type="button" @click="router.push('/patient')">
        <van-icon name="desktop-o" />
        <span>进入 Web 患者端</span>
        <van-icon name="arrow" />
      </button>
    </section>

    <van-button block plain type="danger" class="logout-button" @click="handleLogout">退出登录</van-button>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { maskPhone } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const displayPhone = computed(() => maskPhone((userStore.userInfo as any)?.phone || ''))

const handleLogout = () => {
  userStore.logout()
  showToast('已退出登录')
  router.push('/patient/login?redirect=/mini-patient')
}
</script>

<style lang="scss" scoped>
.mini-page {
  padding: 18px 16px 24px;
}

.profile-card {
  text-align: center;
  border-radius: 8px;
  background: #ffffff;
  padding: 28px 16px;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.profile-card h1 {
  margin: 12px 0 4px;
  color: #1f2a37;
  font-size: 20px;
}

.profile-card p {
  margin: 0;
  color: #687789;
  font-size: 13px;
}

.menu-list {
  display: grid;
  margin-top: 16px;
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.menu-list button {
  display: grid;
  grid-template-columns: 24px 1fr 18px;
  align-items: center;
  gap: 10px;
  min-height: 54px;
  border: 0;
  border-bottom: 1px solid #edf1f6;
  background: #ffffff;
  color: #243447;
  text-align: left;
  font-size: 15px;
}

.menu-list button:last-child {
  border-bottom: 0;
}

.menu-list :deep(.van-icon:first-child) {
  color: #2375ff;
  font-size: 20px;
}

.menu-list :deep(.van-icon:last-child) {
  color: #9aa8b8;
}

.logout-button {
  margin-top: 22px;
}
</style>
