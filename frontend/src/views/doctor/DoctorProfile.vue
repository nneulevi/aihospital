<!-- src/views/doctor/DoctorProfile.vue -->
<template>
  <div class="doctor-profile">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-center">
      <van-loading size="24" vertical>加载中...</van-loading>
    </div>

    <template v-else>
      <div class="user-card">
        <div class="user-avatar">
          <van-icon name="user-circle-o" size="64" color="#005B96" />
        </div>
        <div class="user-info">
          <div class="user-name">{{ profile.realname || userStore.userName || '医生' }}</div>
          <div class="user-title">
            <van-tag type="primary" size="small">{{ profile.titleLevel || '医师' }}</van-tag>
            <van-tag type="warning" size="small" style="margin-left:8px;">
              {{ profile.roleType === 'DOCTOR' ? '医生' : '管理员' }}
            </van-tag>
          </div>
          <div class="user-dept">科室: {{ profile.deptName || '-' }}</div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-item">
          <span class="label">👤 员工ID</span>
          <span class="value">{{ profile.id || '-' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">📞 联系电话</span>
          <span class="value">{{ profile.phone || '-' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">🔑 角色</span>
          <span class="value">{{ profile.roleType === 'DOCTOR' ? '医生' : '管理员' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">📅 入职时间</span>
          <span class="value">{{ formatDate(profile.createTime) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">📊 状态</span>
          <span class="value">
            <van-tag :type="profile.delmark ? 'success' : 'danger'" size="small">
              {{ profile.delmark ? '启用' : '禁用' }}
            </van-tag>
          </span>
        </div>
      </div>

      <div class="stats-section">
        <div class="stats-title">📊 今日统计</div>
        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-num">{{ statistics.todayVisits || 0 }}</div>
            <div class="stat-label">今日接诊</div>
          </div>
          <div class="stat-box">
            <div class="stat-num">{{ statistics.monthVisits || 0 }}</div>
            <div class="stat-label">本月接诊</div>
          </div>
          <div class="stat-box">
            <div class="stat-num">{{ statistics.totalVisits || 0 }}</div>
            <div class="stat-label">累计接诊</div>
          </div>
        </div>
        <div class="stats-grid" style="margin-top: 12px;">
          <div class="stat-box">
            <div class="stat-num">{{ statistics.pendingCount || 0 }}</div>
            <div class="stat-label">待诊</div>
          </div>
          <div class="stat-box">
            <div class="stat-num">{{ statistics.consultingCount || 0 }}</div>
            <div class="stat-label">就诊中</div>
          </div>
          <div class="stat-box">
            <div class="stat-num">{{ statistics.finishedCount || 0 }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </div>

      <div class="menu-group">
        <div class="menu-item" @click="goToSchedule">
          <van-icon name="calendar-o" size="22" color="#005B96" />
          <span class="menu-label">排班管理</span>
          <van-icon name="arrow" class="menu-arrow" />
        </div>
        <div class="menu-item" @click="showToast('功能开发中')">
          <van-icon name="setting-o" size="22" color="#005B96" />
          <span class="menu-label">账号设置</span>
          <van-icon name="arrow" class="menu-arrow" />
        </div>
        <div class="menu-item" @click="showToast('功能开发中')">
          <van-icon name="chart-trending-o" size="22" color="#005B96" />
          <span class="menu-label">数据统计</span>
          <van-icon name="arrow" class="menu-arrow" />
        </div>
        <div class="menu-item" @click="handleLogout">
          <van-icon name="logout" size="22" color="#E76F51" />
          <span class="menu-label" style="color: #E76F51;">退出登录</span>
          <van-icon name="arrow" class="menu-arrow" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { useUserStore } from '@/stores/user'
import { getProfile, getStatistics } from '@/api'
import type { DoctorProfileVO, DoctorStatisticsVO } from '@/api/model'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const profile = ref<DoctorProfileVO>({})
const statistics = ref<DoctorStatisticsVO>({})

// ===== 格式化时间 =====
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

// ===== 加载医生个人信息 =====
const loadProfile = async () => {
  const doctorId = userStore.userInfo?.employeeId
  if (!doctorId) {
    showToast('未获取到医生信息')
    loading.value = false
    return
  }

  try {
    const res = await getProfile({ doctorId })
    profile.value = res
  } catch (error: any) {
    console.error('获取医生信息失败', error)
    showToast(error.message || '加载失败')
  }
}

// ===== 加载医生统计数据 =====
const loadStatistics = async () => {
  const doctorId = userStore.userInfo?.employeeId
  if (!doctorId) return

  try {
    const res = await getStatistics({ doctorId })
    statistics.value = res
  } catch (error: any) {
    console.error('获取统计数据失败', error)
  }
}

// ===== 路由跳转 =====
const goToSchedule = () => {
  router.push('/doctor/schedule')
}

// ===== 退出登录 =====
const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#E76F51'
  })
      .then(() => {
        userStore.logout()
        showToast('已退出登录')
        router.replace('/auth/login')
      })
      .catch(() => {})
}

// ===== 页面初始化 =====
onMounted(async () => {
  await loadProfile()
  await loadStatistics()
  loading.value = false
})
</script>

<style lang="scss" scoped>
.doctor-profile {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.user-card {
  background: white;
  margin: 12px;
  padding: 24px 16px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.user-avatar {
  margin-bottom: 12px;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: #2C3E50;
}

.user-title {
  margin-top: 8px;
}

.user-dept {
  font-size: 13px;
  color: #7F8C8D;
  margin-top: 6px;
}

.detail-section {
  background: white;
  margin: 12px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #F5F5F5;

  &:last-child {
    border-bottom: none;
  }

  .label {
    color: #7F8C8D;
    font-size: 14px;
  }

  .value {
    color: #2C3E50;
    font-size: 14px;
    font-weight: 500;
  }
}

.stats-section {
  background: white;
  margin: 12px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.stats-title {
  font-size: 15px;
  font-weight: 600;
  color: #2C3E50;
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
    color: #005B96;
  }

  .stat-label {
    font-size: 12px;
    color: #7F8C8D;
    margin-top: 4px;
  }
}

.menu-group {
  background: white;
  margin: 12px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
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

  &:active {
    background: #F5F7FA;
  }
}

.menu-label {
  flex: 1;
  margin-left: 12px;
  font-size: 14px;
  color: #2C3E50;
}

.menu-arrow {
  color: #BDC3C7;
}
</style>