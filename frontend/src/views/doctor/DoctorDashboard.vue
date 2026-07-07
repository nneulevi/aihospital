<!-- src/views/doctor/DoctorDashboard.vue -->
<template>
  <div class="doctor-dashboard">
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-num">{{ pendingList.length }}</div>
        <div class="stat-label">待诊</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ consultingList.length }}</div>
        <div class="stat-label">就诊中</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ finishedToday }}</div>
        <div class="stat-label">今日已接诊</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ pendingCheckCount }}</div>
        <div class="stat-label">待处理检查</div>
      </div>
    </div>

    <div class="quick-grid">
      <div class="quick-card" @click="$router.push('/doctor/ai-diagnosis')">
        <van-icon name="records-o" />
        <span>AI 辅助诊断</span>
      </div>
      <div class="quick-card" @click="$router.push('/doctor/ai-triage')">
        <van-icon name="guide-o" />
        <span>AI 分诊</span>
      </div>
      <div class="quick-card" @click="$router.push('/doctor/schedule')">
        <van-icon name="calendar-o" />
        <span>我的排班</span>
      </div>
      <div class="quick-card" @click="$router.push('/doctor/headct-reports')">
        <van-icon name="description-o" />
        <span>CT 报告工作台</span>
      </div>
    </div>

    <van-tabs v-model:active="listTab" class="patient-tabs">
      <van-tab title="待诊队列" name="pending">
        <div class="patient-list">
          <div v-for="p in pendingList" :key="p.registerId" class="patient-card" :class="{ receiving: receivingId === p.registerId }" @click="goToVisit(p)">
            <div class="patient-header">
              <div class="patient-name">{{ p.patientName }}</div>
              <van-tag type="primary">{{ receivingId === p.registerId ? '接诊中' : '待诊' }}</van-tag>
            </div>
            <div class="patient-info">
              <span>{{ p.gender }}</span>
              <span>{{ p.age }}岁</span>
              <span>病历号: {{ p.caseNumber }}</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }} {{ formatNoon(p.noon) }}
            </div>
          </div>
          <div v-if="pendingList.length === 0" class="empty-state">
            <van-icon name="smile-o" size="48" color="#C4B8A8" />
            <p>暂无待诊患者</p>
          </div>
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
              <span>{{ p.gender }}</span>
              <span>{{ p.age }}岁</span>
              <span>病历号: {{ p.caseNumber }}</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }} {{ formatNoon(p.noon) }}
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
              <span>{{ p.gender }}</span>
              <span>{{ p.age }}岁</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }} {{ formatNoon(p.noon) }}
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getPatients, receivePatient, getDoctorDashboardSummary } from '@/api'
import type { DoctorPatientListVO } from '@/api/model'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const listTab = ref('pending')
const allPatients = ref<DoctorPatientListVO[]>([])
const finishedToday = ref(0)
const pendingCheckCount = ref(0)
const receivingId = ref<number | null>(null)

const pendingList = ref<DoctorPatientListVO[]>([])
const consultingList = ref<DoctorPatientListVO[]>([])
const finishedList = ref<DoctorPatientListVO[]>([])

const loadPatients = async () => {
  try {
    const doctorId = userStore.doctorId || 1
    const [pendingRes, consultingRes, finishedRes] = await Promise.all([
      getPatients({ doctorId, visitState: 'REGISTERED', pageNum: 1, pageSize: 50 }),
      getPatients({ doctorId, visitState: 'DOCTOR_RECEIVED', pageNum: 1, pageSize: 50 }),
      getPatients({ doctorId, visitState: 'DIAGNOSIS_DONE', pageNum: 1, pageSize: 50 })
    ])
    pendingList.value = pendingRes.data?.records || []
    consultingList.value = consultingRes.data?.records || []
    finishedList.value = finishedRes.data?.records || []
    allPatients.value = [...pendingList.value, ...consultingList.value, ...finishedList.value]
  } catch {
    showToast('加载失败')
  }
}

const loadDashboardSummary = async () => {
  try {
    const doctorId = userStore.doctorId || 1
    const res = await getDoctorDashboardSummary(doctorId)
    const data = res.data || res
    finishedToday.value = data.finishedToday || 0
    pendingCheckCount.value = data.pendingCheckCount || 0
  } catch {
    showToast('统计信息加载失败')
  }
}

const goToVisit = async (patient: DoctorPatientListVO) => {
  if (!patient.registerId) {
    showToast('缺少挂号ID，无法接诊')
    return
  }
  const shouldReceive = (patient as any).visitState === 'REGISTERED' || !(patient as any).visitState
  if (shouldReceive) {
    receivingId.value = patient.registerId
    try {
      await receivePatient(patient.registerId)
      ;(patient as any).visitState = 'DOCTOR_RECEIVED'
      showToast('已接诊')
    } catch {
      showToast('接诊失败')
      receivingId.value = null
      return
    }
    receivingId.value = null
  }
  router.push({
    name: 'PatientVisit',
    query: { registerId: String(patient.registerId), name: patient.patientName }
  })
}

const formatTime = (time?: string) => time ? dayjs(time).format('HH:mm') : ''
const formatNoon = (noon?: string) => {
  if (noon === 'AM' || noon === 'MORNING') return '上午'
  if (noon === 'PM' || noon === 'AFTERNOON') return '下午'
  return ''
}

onMounted(() => {
  loadPatients()
  loadDashboardSummary()
})
</script>

<style lang="scss" scoped>
.doctor-dashboard {
  padding: 12px;
  padding-bottom: 20px;
}
.stats-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.quick-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 8px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
  cursor: pointer;
  color: #1677ff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
}
.stat-item {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .stat-num {
    font-size: 24px;
    font-weight: 700;
    color: #1677ff;
  }
  .stat-label {
    font-size: 12px;
    color: #64748b;
    margin-top: 4px;
  }
}
.patient-tabs :deep(.van-tabs__line) {
  background-color: #1677ff;
}
.patient-list {
  padding: 8px 0;
}
.patient-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  &.active {
    border-left: 4px solid #1677ff;
  }
  &.done {
    border-left: 4px solid #10b981;
    opacity: 0.8;
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
    color: #1f2937;
  }
}
.patient-info {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.patient-time {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #94a3b8;
}

@media (max-width: 680px) {
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
