<!-- src/views/patient/Home.vue -->
<template>
  <div class="home-page">
    <div class="header-area">
      <div class="greeting-row">
        <div class="greeting">
          <span class="greeting-icon">☀️</span>
          <span class="greeting-text">{{ greeting }}，{{ displayName }}</span>
        </div>
        <div class="header-actions">
          <van-icon name="bell-o" size="22" @click="goToMessages" />
        </div>
      </div>
      <div class="patient-switcher" @click="showPatientSheet = true">
        <div class="patient-info">
          <span class="patient-name">{{ displayName || '请选择就诊人' }}</span>
          <span class="patient-id" v-if="userStore.userInfo?.caseNumber">病历号：{{ userStore.userInfo.caseNumber }}</span>
          <span class="patient-id" v-else>点击添加就诊人</span>
        </div>
        <van-icon name="arrow-down" class="switch-arrow" />
      </div>
    </div>

    <div class="core-services">
      <div class="service-card" @click="goToAppointment">
        <div class="service-icon" style="background: #E8F5E9; color: #4CAF50;">
          <van-icon name="calendar-o" size="28" />
        </div>
        <div class="service-text">
          <div class="service-title">预约挂号</div>
          <div class="service-desc">在线预约专家号</div>
        </div>
        <van-icon name="arrow" class="service-arrow" />
      </div>
      <div class="service-card" @click="goToOrders">
        <div class="service-icon" style="background: #FFF3E0; color: #FF9800;">
          <van-icon name="gold-coin-o" size="28" />
        </div>
        <div class="service-text">
          <div class="service-title">自助缴费</div>
          <div class="service-desc">门诊费用在线支付</div>
        </div>
        <van-icon name="arrow" class="service-arrow" />
      </div>
    </div>

    <div class="quick-actions">
      <div class="quick-item" @click="goToCheckin">
        <div class="quick-icon" style="background: #E3F2FD; color: #2196F3;">
          <van-icon name="location-o" size="24" />
        </div>
        <span class="quick-label">就诊报到</span>
      </div>
      <div class="quick-item" @click="goToQueue">
        <div class="quick-icon" style="background: #FCE4EC; color: #E91E63;">
          <van-icon name="clock-o" size="24" />
        </div>
        <span class="quick-label">候诊查询</span>
        <span class="quick-badge" v-if="queueNumber > 0">前面{{ queueNumber }}人</span>
      </div>
    </div>

    <div class="service-section">
      <div class="section-header">
        <span class="section-title">门诊服务</span>
        <span class="section-more" @click="showAllServices">全部</span>
      </div>
      <div class="service-grid">
        <div
            v-for="item in serviceItems"
            :key="item.key"
            class="grid-item"
            @click="goToService(item.key)"
        >
          <div class="grid-icon" :style="{ background: item.bgColor, color: item.color }">
            <van-icon :name="item.icon" size="24" />
          </div>
          <span class="grid-label">{{ item.label }}</span>
        </div>
      </div>
    </div>

    <div class="service-section">
      <div class="section-header">
        <span class="section-title">便民服务</span>
      </div>
      <div class="service-grid" style="grid-template-columns: repeat(3, 1fr);">
        <div class="grid-item" @click="goToGuide">
          <div class="grid-icon" style="background: #E8EAF6; color: #3F51B5;">
            <van-icon name="guide-o" size="24" />
          </div>
          <span class="grid-label">就诊指南</span>
        </div>
        <div class="grid-item" @click="goToCustomerService">
          <div class="grid-icon" style="background: #FBE9E7; color: #FF5722;">
            <van-icon name="service-o" size="24" />
          </div>
          <span class="grid-label">联系客服</span>
        </div>
        <div class="grid-item" @click="goToAI">
          <div class="grid-icon" style="background: #E0F7FA; color: #00BCD4;">
            <van-icon name="chat-o" size="24" />
          </div>
          <span class="grid-label">智能问答</span>
        </div>
      </div>
    </div>

    <van-action-sheet v-model:show="showPatientSheet" title="切换就诊人">
      <div class="patient-list">
        <div
            v-for="patient in patientList"
            :key="patient.patientId"
            class="patient-option"
            :class="{ active: currentPatient?.patientId === patient.patientId }"
            @click="selectPatient(patient)"
        >
          <div class="patient-avatar">
            <van-icon name="user-circle-o" size="32" />
          </div>
          <div class="patient-detail">
            <div class="patient-name">{{ patient.realName }}</div>
            <div class="patient-meta">
              <span>{{ patient.gender === 'MALE' ? '男' : '女' }}</span>
              <span>{{ patient.age || '--' }}岁</span>
              <span>病历号：{{ patient.caseNumber }}</span>
            </div>
          </div>
          <van-icon v-if="currentPatient?.patientId === patient.patientId" name="success" color="#4CAF50" />
        </div>
        <div class="add-patient" @click="goToPatientManager">
          <van-icon name="plus" size="20" />
          <span>添加就诊人</span>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const showPatientSheet = ref(false)
const patientList = ref<any[]>([])
const queueNumber = ref(0)

// ===== 显示名称：从 userStore 获取 =====
const displayName = computed(() => {
  return userStore.userName || userStore.userInfo?.realName || userStore.userInfo?.realname || '用户'
})

// ===== 当前患者信息（从 userStore 获取） =====
const currentPatient = computed(() => ({
  patientId: userStore.userInfo?.patientId,
  realName: userStore.userName || '用户',
  caseNumber: userStore.userInfo?.caseNumber || '',
  gender: userStore.userInfo?.gender || 'MALE',
  age: userStore.userInfo?.age,
}))

// ===== 问候语 =====
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

// ===== 服务网格 =====
const serviceItems = [
  { key: 'lab', label: '检验预约', icon: 'medical-o', bg: '#E3F2FD', color: '#2196F3' },
  { key: 'exam', label: '检查预约', icon: 'scan-o', bg: '#E8F5E9', color: '#4CAF50' },
  { key: 'consult', label: '在线咨询', icon: 'chat-o', bg: '#FFF3E0', color: '#FF9800' },
  { key: 'report', label: '报告查询', icon: 'file-o', bg: '#FCE4EC', color: '#E91E63' },
  { key: 'doctor', label: '出诊查询', icon: 'doctor-o', bg: '#E8EAF6', color: '#3F51B5' },
  { key: 'revisit', label: '复诊预约', icon: 'calendar-o', bg: '#F3E5F5', color: '#9C27B0' },
  { key: 'prescription', label: '处方查询', icon: 'bill-o', bg: '#FFF8E1', color: '#FFC107' },
  { key: 'physical', label: '健康体检', icon: 'heartbeat-o', bg: '#E0F7FA', color: '#00BCD4' },
  { key: 'more', label: '更多服务', icon: 'apps-o', bg: '#F5F5F5', color: '#9E9E9E' },
]

// ===== 就诊人 =====
const loadPatients = async () => {
  // TODO: 从 API 获取就诊人列表
  const userInfo = userStore.userInfo
  if (userInfo) {
    patientList.value = [
      {
        patientId: userInfo.patientId || 1,
        realName: userStore.userName || '用户',
        gender: userInfo.gender || 'MALE',
        age: userInfo.age || 30,
        caseNumber: userInfo.caseNumber || '----',
        phone: userInfo.phone || ''
      }
    ]
  }
}

const selectPatient = (patient: any) => {
  // TODO: 切换就诊人
  showToast('切换就诊人功能开发中')
  showPatientSheet.value = false
}

const loadQueueInfo = async () => {
  queueNumber.value = Math.floor(Math.random() * 15) + 1
}

// ===== 路由跳转 =====
const goToAppointment = () => router.push('/patient/appointment')
const goToOrders = () => router.push('/patient/orders')
const goToCheckin = () => router.push('/patient/checkin')
const goToQueue = () => router.push('/patient/queue')
const goToMessages = () => showToast('消息中心开发中')
const goToPatientManager = () => router.push('/patient/patient-manager')
const goToGuide = () => showToast('就诊指南')
const goToCustomerService = () => showToast('联系客服：400-123-4567')
const goToAI = () => router.push('/patient/ai')
const showAllServices = () => showToast('全部服务')

const goToService = (key: string) => {
  const routeMap: Record<string, string> = {
    lab: '/patient/lab-booking',
    exam: '/patient/exam-booking',
    consult: '/patient/consult',
    report: '/patient/reports',
    doctor: '/patient/doctor-schedule',
    revisit: '/patient/revisit',
    prescription: '/patient/prescriptions',
    physical: '/patient/physical-exam',
    more: '/patient/services',
  }
  const path = routeMap[key]
  if (path) router.push(path)
  else showToast('功能开发中')
}

onMounted(() => {
  loadPatients()
  loadQueueInfo()
})
</script>

<style lang="scss" scoped>
.home-page { min-height: 100vh; background: #F5F7FA; padding: 0 16px 80px; }
.header-area {
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  margin: 0 -16px 16px; padding: 20px 16px 24px; border-radius: 0 0 24px 24px; color: white;
}
.greeting-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.greeting-text { font-size: 18px; font-weight: 500; margin-left: 8px; }
.header-actions { display: flex; gap: 16px; }
.patient-switcher {
  display: flex; justify-content: space-between; align-items: center;
  background: rgba(255,255,255,0.2); border-radius: 12px; padding: 12px 16px;
  cursor: pointer; backdrop-filter: blur(4px);
}
.patient-info { display: flex; flex-direction: column; gap: 2px; }
.patient-name { font-size: 16px; font-weight: 500; }
.patient-id { font-size: 12px; opacity: 0.85; }
.switch-arrow { font-size: 18px; opacity: 0.8; }

.core-services { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.service-card {
  background: white; border-radius: 12px; padding: 16px; display: flex;
  align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer; &:active { transform: scale(0.97); }
}
.service-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.service-text { flex: 1; .service-title { font-size: 15px; font-weight: 500; color: #1A1A2E; } .service-desc { font-size: 12px; color: #8B8B9E; margin-top: 2px; } }
.service-arrow { color: #C4C4D6; font-size: 14px; }

.quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.quick-item {
  background: white; border-radius: 12px; padding: 16px; display: flex;
  flex-direction: column; align-items: center; gap: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); cursor: pointer; position: relative;
  &:active { transform: scale(0.97); }
}
.quick-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.quick-label { font-size: 14px; font-weight: 500; color: #1A1A2E; }
.quick-badge { position: absolute; top: 8px; right: 8px; background: #E91E63; color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px; }

.service-section { background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-title { font-size: 16px; font-weight: 600; color: #1A1A2E; }
.section-more { font-size: 13px; color: #8B8B9E; cursor: pointer; }
.service-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px 8px; }
.grid-item { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; &:active { opacity: 0.7; } }
.grid-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.grid-label { font-size: 12px; color: #4A4A5E; text-align: center; }

.patient-list { padding: 8px 16px 20px; }
.patient-option {
  display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 10px;
  margin-bottom: 4px; cursor: pointer; &.active { background: #F0F4F0; }
}
.patient-detail { flex: 1; .patient-name { font-size: 16px; font-weight: 500; color: #1A1A2E; } .patient-meta { font-size: 13px; color: #8B8B9E; display: flex; gap: 12px; margin-top: 2px; } }
.add-patient {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px; border: 2px dashed #D0D0D0; border-radius: 10px;
  margin-top: 8px; cursor: pointer; color: #4A4A5E; font-size: 14px;
}
</style>