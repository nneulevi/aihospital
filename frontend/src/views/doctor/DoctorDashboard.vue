<!-- src/views/doctor/DoctorDashboard.vue -->
<template>
  <div class="doctor-dashboard">
    <div class="welcome-section">
      <div class="greeting">👋 您好，{{ doctorName }}</div>
      <div class="date">{{ today }}</div>
    </div>

    <div class="stats-bar">
      <div class="stat-item" @click="switchTab('pending')">
        <div class="stat-num">{{ pendingList.length }}</div>
        <div class="stat-label">待诊</div>
        <van-tag v-if="pendingList.length > 0" type="danger" class="badge">新</van-tag>
      </div>
      <div class="stat-item" @click="switchTab('consulting')">
        <div class="stat-num">{{ consultingList.length }}</div>
        <div class="stat-label">就诊中</div>
        <van-tag v-if="consultingList.length > 0" type="warning" class="badge">进行中</van-tag>
      </div>
      <div class="stat-item" @click="switchTab('finished')">
        <div class="stat-num">{{ finishedList.length }}</div>
        <div class="stat-label">今日已接诊</div>
      </div>
    </div>

    <van-tabs v-model:active="listTab" class="patient-tabs" @change="onTabChange">
      <van-tab title="待诊队列" name="pending">
        <div class="patient-list">
          <van-pull-refresh v-model="refreshing" @refresh="loadPatients">
            <div v-if="todayPending.length > 0" class="group-label">📅 今日待诊</div>
            <div v-for="p in todayPending" :key="p.registerId" class="patient-card" @click="goToVisit(p)">
              <div class="patient-header">
                <div class="patient-name">{{ p.patientName }}</div>
                <van-tag type="primary">待诊</van-tag>
              </div>
              <div class="patient-info">
                <span>{{ p.gender || '未知' }}</span>
                <span>{{ p.age || '--' }}岁</span>
                <span>病历号: {{ p.caseNumber || '--' }}</span>
              </div>
              <div class="patient-time">
                <van-icon name="clock-o" />
                {{ formatTime(p.registrationTime) }} {{ p.noon === 'MORNING' ? '上午' : '下午' }}
                <span class="wait-time" v-if="p.waitMinutes > 0">等待 {{ p.waitMinutes }}min</span>
              </div>
            </div>

            <div v-if="otherPending.length > 0" class="group-label" :class="{ expired: hasExpired }">
              {{ hasExpired ? '⚠️ 过期未诊' : '📋 其他日期' }}
            </div>
            <div v-for="p in otherPending" :key="p.registerId" class="patient-card" :class="{ expired: p.isExpired }" @click="goToVisit(p)">
              <div class="patient-header">
                <div class="patient-name">{{ p.patientName }}</div>
                <van-tag type="primary" plain>待诊</van-tag>
              </div>
              <div class="patient-info">
                <span>{{ p.gender || '未知' }}</span>
                <span>{{ p.age || '--' }}岁</span>
                <span>病历号: {{ p.caseNumber || '--' }}</span>
              </div>
              <div class="patient-time">
                <van-icon name="clock-o" />
                {{ formatDateTime(p.registrationTime) }}
                <span v-if="p.isExpired" class="expired-tag">已过期</span>
                <span v-else-if="p.isFuture" class="future-tag">预约</span>
              </div>
            </div>

            <div v-if="pendingList.length === 0" class="empty-state">
              <van-icon name="smile-o" size="48" color="#C4B8A8" />
              <p>暂无待诊患者</p>
            </div>
          </van-pull-refresh>
        </div>
      </van-tab>

      <van-tab title="就诊中" name="consulting">
        <div class="patient-list">
          <div v-for="p in consultingList" :key="p.registerId" class="patient-card active" @click="goToVisit(p)">
            <div class="patient-header">
              <div class="patient-name">{{ p.patientName }}</div>
              <van-tag type="warning">就诊中</van-tag>
            </div>
            <div class="patient-info">
              <span>{{ p.gender || '未知' }}</span>
              <span>{{ p.age || '--' }}岁</span>
              <span>病历号: {{ p.caseNumber || '--' }}</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }}
            </div>
          </div>
          <div v-if="consultingList.length === 0" class="empty-state">
            <van-icon name="smile-o" size="48" color="#C4B8A8" />
            <p>暂无就诊中患者</p>
          </div>
        </div>
      </van-tab>

      <van-tab title="今日已完成" name="finished">
        <div class="patient-list">
          <div v-for="p in finishedList" :key="p.registerId" class="patient-card done">
            <div class="patient-header">
              <div class="patient-name">{{ p.patientName }}</div>
              <van-tag type="success">已完成</van-tag>
            </div>
            <div class="patient-info">
              <span>{{ p.gender || '未知' }}</span>
              <span>{{ p.age || '--' }}岁</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }}
            </div>
          </div>
          <div v-if="finishedList.length === 0" class="empty-state">
            <van-icon name="smile-o" size="48" color="#C4B8A8" />
            <p>今日暂无已完成</p>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getProfile, getPatients } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const listTab = ref('pending')
const refreshing = ref(false)

const doctorId = computed(() => userStore.doctorId || 0)
const doctorName = ref('')

const pendingList = ref<any[]>([])
const consultingList = ref<any[]>([])
const finishedList = ref<any[]>([])

const todayStr = dayjs().format('YYYY-MM-DD')

const todayPending = computed(() => pendingList.value.filter(p => p.isToday))
const otherPending = computed(() => pendingList.value.filter(p => !p.isToday))
const hasExpired = computed(() => otherPending.value.some(p => p.isExpired))

const loadDoctorProfile = async () => {
  const id = doctorId.value
  if (!id) {
    console.warn('[DoctorDashboard] doctorId 为空')
    doctorName.value = userStore.userInfo?.realName || userStore.userInfo?.realname || '医生'
    return
  }

  try {
    // ✅ 正确：直接传递参数对象
    const res = await getProfile({ doctorId: id })
    doctorName.value = res.realname || '医生'
  } catch (e) {
    console.error('[DoctorDashboard] 加载医生信息失败:', e)
    doctorName.value = userStore.userInfo?.realName || userStore.userInfo?.realname || '医生'
  }
}

const loadPatients = async () => {
  const id = doctorId.value
  if (!id) {
    console.warn('[DoctorDashboard] doctorId 为空，无法加载患者列表')
    return
  }

  refreshing.value = true
  try {
    // ✅ 正确：直接传递参数对象，不要嵌套在 query 中
    const [pendingRes, consultingRes, finishedRes] = await Promise.all([
      getPatients({
        doctorId: id,
        visitState: 'REGISTERED',
        pageNum: 1,
        pageSize: 100
      }),
      getPatients({
        doctorId: id,
        visitState: 'CONSULTING',
        pageNum: 1,
        pageSize: 100
      }),
      getPatients({
        doctorId: id,
        visitState: 'FINISHED',
        pageNum: 1,
        pageSize: 100
      })
    ])

    const processList = (res: any, state: string) => {
      const records = res.records || res.content || []
      return records.map((p: any) => {
        const visitDate = p.registrationTime ? dayjs(p.registrationTime).format('YYYY-MM-DD') : ''
        const regTime = p.registrationTime ? dayjs(p.registrationTime) : null
        return {
          ...p,
          visitDate,
          isToday: visitDate === todayStr,
          isExpired: visitDate && visitDate < todayStr,
          isFuture: visitDate && visitDate > todayStr,
          waitMinutes: regTime ? dayjs().diff(regTime, 'minute') : 0
        }
      })
    }

    const allPending = processList(pendingRes, 'REGISTERED')
    const allConsulting = processList(consultingRes, 'CONSULTING')
    const allFinished = processList(finishedRes, 'FINISHED')

    pendingList.value = allPending.sort((a: any, b: any) => {
      if (a.isToday && !b.isToday) return -1
      if (!a.isToday && b.isToday) return 1
      if (a.isExpired && !b.isExpired) return -1
      if (!a.isExpired && b.isExpired) return 1
      return dayjs(a.registrationTime).valueOf() - dayjs(b.registrationTime).valueOf()
    })

    consultingList.value = allConsulting
    finishedList.value = allFinished.filter((p: any) => p.isToday)
  } catch (e: any) {
    console.error('[DoctorDashboard] 加载患者列表失败:', e)
    showToast('加载失败: ' + (e.message || '未知错误'))
  } finally {
    refreshing.value = false
  }
}

const switchTab = (tab: string) => { listTab.value = tab }
const onTabChange = () => { loadPatients() }

const goToVisit = (patient: any) => {
  router.push({
    name: 'PatientVisit',
    query: {
      registerId: String(patient.registerId),
      name: patient.patientName,
      from: 'dashboard'
    }
  })
}

const formatTime = (time?: string) => time ? dayjs(time).format('HH:mm') : '--:--'
const formatDateTime = (time?: string) => time ? dayjs(time).format('MM-DD HH:mm') : ''

const today = computed(() => dayjs().format('YYYY年MM月DD日 dddd'))

onMounted(() => {
  console.log('[DoctorDashboard] onMounted - isLoggedIn:', userStore.isLoggedIn)
  console.log('[DoctorDashboard] onMounted - doctorId:', userStore.doctorId)
  console.log('[DoctorDashboard] onMounted - userInfo:', userStore.userInfo)

  if (!userStore.isLoggedIn || !userStore.doctorId) {
    showToast('请先登录')
    router.push('/auth/login')
    return
  }
  loadDoctorProfile()
  loadPatients()
})
</script>

<style lang="scss" scoped>
.doctor-dashboard {
  padding: 12px;
  padding-bottom: 20px;
}

.welcome-section {
  background: linear-gradient(135deg, #005B96 0%, #0077B6 100%);
  margin: -12px -12px 12px -12px;
  padding: 20px 16px 16px;
  color: white;

  .greeting {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .date {
    font-size: 14px;
    opacity: 0.8;
  }
}

.stats-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  margin-top: 8px;
}

.stat-item {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  position: relative;
  transition: all 0.3s;

  &:active {
    transform: scale(0.95);
  }

  .stat-num {
    font-size: 24px;
    font-weight: 700;
    color: #005B96;
  }

  .stat-label {
    font-size: 12px;
    color: #8B7A6B;
    margin-top: 4px;
  }

  .badge {
    position: absolute;
    top: 8px;
    right: 8px;
  }
}

.patient-tabs :deep(.van-tabs__line) {
  background-color: #005B96;
}

.patient-list {
  padding: 8px 0;
}

.group-label {
  font-size: 13px;
  color: #666;
  padding: 8px 12px;
  font-weight: 500;

  &.expired {
    color: #E74C3C;
  }
}

.patient-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  margin-left: 12px;
  margin-right: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
  }

  &.active {
    border-left: 4px solid #F4A261;
  }

  &.done {
    border-left: 4px solid #8CB369;
    opacity: 0.8;
  }

  &.expired {
    border-left: 4px solid #E74C3C;
    background: #FFF5F5;
  }
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .patient-name {
    font-size: 16px;
    font-weight: 600;
    color: #2C3E50;
  }
}

.patient-info {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #7F8C8D;
  margin-bottom: 8px;
}

.patient-time {
  font-size: 12px;
  color: #95A5A6;
  display: flex;
  align-items: center;
  gap: 4px;

  .wait-time {
    color: #E74C3C;
    margin-left: 8px;
  }

  .expired-tag {
    color: #E74C3C;
    margin-left: 8px;
    font-weight: 500;
  }

  .future-tag {
    color: #27AE60;
    margin-left: 8px;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #BDC3C7;
}
</style>