<template>
  <div class="staff-shell">
    <header class="topbar">
      <div>
        <div class="eyebrow">Medical Technology</div>
        <h1>医技工作台</h1>
      </div>
      <button class="logout" @click="logoutToLogin">退出</button>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const logoutToLogin = () => {
  userStore.logout()
  router.push('/auth/login')
}
</script>

<style scoped>
.staff-shell {
  min-height: 100vh;
  background: #f4f6f8;
}
.topbar {
  height: 72px;
  padding: 0 28px;
  background: #0f4c81;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.eyebrow {
  font-size: 12px;
  opacity: 0.72;
}
h1 {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 700;
}
main {
  padding: 24px;
}
.logout {
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: transparent;
  color: #fff;
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}
</style>
