<!-- src/views/doctor/DoctorProfile.vue -->
<template>
  <div class="doctor-profile">
    <div class="user-card">
      <div class="user-avatar">
        <van-icon name="user-circle-o" size="64" color="#5E60CE" />
      </div>
      <div class="user-info">
        <div class="user-name">{{ userStore.userName || '张医生' }}</div>
        <div class="user-dept">呼吸内科 | 主任医师</div>
      </div>
    </div>

    <div class="stats-section">
      <div class="stats-title">本月统计</div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-num">156</div>
          <div class="stat-label">接诊人次</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">98%</div>
          <div class="stat-label">诊断准确率</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">4.9</div>
          <div class="stat-label">患者评分</div>
        </div>
      </div>
    </div>

    <div class="menu-group">
      <div class="menu-item" @click="showToast('功能开发中')">
        <van-icon name="setting-o" size="22" color="#5E60CE" />
        <span class="menu-label">账号设置</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="showToast('功能开发中')">
        <van-icon name="records-o" size="22" color="#5E60CE" />
        <span class="menu-label">排班查询</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="handleLogout">
        <van-icon name="logout" size="22" color="#E76F51" />
        <span class="menu-label" style="color: #E76F51;">退出登录</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast, showDialog } from 'vant'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#E76F51'
  }).then(() => {
    userStore.logout()
    showToast('已退出登录')
    router.push('/auth/login')
  }).catch(() => {})
}
</script>

<style lang="scss" scoped>
.doctor-profile {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}
.user-card {
  background: white;
  margin: 12px;
  padding: 32px 16px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.user-avatar {
  margin-bottom: 12px;
}
.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #5C4B3A;
}
.user-dept {
  font-size: 13px;
  color: #8B7A6B;
  margin-top: 4px;
}
.stats-section {
  background: white;
  margin: 12px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stats-title {
  font-size: 15px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 12px;
}
.stats-grid {
  display: flex;
  gap: 12px;
}
.stat-box {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #F5F7FA;
  border-radius: 8px;
  .stat-num {
    font-size: 20px;
    font-weight: 700;
    color: #5E60CE;
  }
  .stat-label {
    font-size: 12px;
    color: #8B7A6B;
    margin-top: 4px;
  }
}
.menu-group {
  background: white;
  margin: 12px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #F5F5F5;
  cursor: pointer;
  &:last-child {
    border-bottom: none;
  }
}
.menu-label {
  flex: 1;
  margin-left: 12px;
  font-size: 14px;
  color: #5C4B3A;
}
.menu-arrow {
  color: #C4B8A8;
}
</style>
