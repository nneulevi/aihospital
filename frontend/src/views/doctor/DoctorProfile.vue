<!-- src/views/doctor/DoctorProfile.vue -->
<template>
  <div class="doctor-profile">
    <div class="user-card">
      <div class="user-avatar">
        <van-icon name="user-circle-o" size="64" color="#5E60CE" />
      </div>
      <div class="user-info">
        <div class="user-name">{{ profile.doctorName || userStore.userName || '医生' }}</div>
        <div class="user-dept">{{ profile.deptName || '未分配科室' }} | {{ profile.titleLevel || '医生' }}</div>
      </div>
    </div>

    <div class="stats-section">
      <div class="stats-title">本月统计</div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-num">{{ stats.monthVisits ?? 0 }}</div>
          <div class="stat-label">接诊人次</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">{{ stats.pendingCount ?? 0 }}</div>
          <div class="stat-label">待接诊</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">{{ stats.finishedCount ?? 0 }}</div>
          <div class="stat-label">今日完成</div>
        </div>
      </div>
    </div>

    <div class="menu-group">
      <div class="menu-item">
        <van-icon name="setting-o" size="22" color="#5E60CE" />
        <span class="menu-label">联系电话：{{ profile.phone || '未登记' }}</span>
      </div>
      <div class="menu-item" @click="router.push('/doctor/schedule')">
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
import { onMounted, reactive } from 'vue'
import { showToast, showDialog } from 'vant'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getDoctorProfile, getDoctorStatistics, type DoctorProfileVO, type DoctorStatisticsVO } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const profile = reactive<DoctorProfileVO>({})
const stats = reactive<DoctorStatisticsVO>({})

const loadProfile = async () => {
  if (!userStore.doctorId) return
  try {
    const [profileRes, statsRes] = await Promise.all([
      getDoctorProfile(userStore.doctorId),
      getDoctorStatistics(userStore.doctorId)
    ])
    Object.assign(profile, profileRes.data || profileRes)
    Object.assign(stats, statsRes.data || statsRes)
  } catch {
    showToast('医生信息加载失败')
  }
}

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

onMounted(loadProfile)
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
