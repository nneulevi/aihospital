<!-- src/views/patient/AppointmentSuccess.vue -->
<template>
  <div class="success-page">
    <div class="success-card">
      <div class="success-icon"><van-icon name="checked" size="64" color="#4CAF50" /></div>
      <div class="success-title">挂号成功</div>
      <div class="success-subtitle">请按时到院就诊</div>

      <div class="info-card">
        <div class="info-row"><span class="info-label">就诊科室</span><span class="info-value">{{ appointmentInfo.deptName }}</span></div>
        <div class="info-row"><span class="info-label">就诊医生</span><span class="info-value">{{ appointmentInfo.doctorName }}（{{ appointmentInfo.doctorTitle }}）</span></div>
        <div class="info-row"><span class="info-label">就诊时间</span><span class="info-value">{{ appointmentInfo.visitDate }} {{ appointmentInfo.noon === 'MORNING' ? '上午' : '下午' }}</span></div>
        <div class="info-row"><span class="info-label">就诊地点</span><span class="info-value">{{ appointmentInfo.location }}</span></div>
        <div class="info-row"><span class="info-label">排队序号</span><span class="info-value highlight">{{ appointmentInfo.queueNumber }}</span></div>
        <div class="info-row"><span class="info-label">病历号</span><span class="info-value">{{ appointmentInfo.caseNumber }}</span></div>
      </div>

      <div class="tips-card">
        <div class="tips-title">温馨提示</div>
        <div class="tip-item">📋 请携带身份证和医保卡就诊</div>
        <div class="tip-item">⏰ 请提前15分钟到达候诊区</div>
        <div class="tip-item">💰 如需取消挂号，请在就诊前1小时操作</div>
      </div>

      <div class="action-buttons">
        <van-button plain type="primary" round @click="goToRecords">查看挂号记录</van-button>
        <van-button type="primary" round @click="goToHome">返回首页</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const appointmentInfo = ref({
  registerId: '',
  deptName: '呼吸内科',
  doctorName: '张敏',
  doctorTitle: '主任医师',
  visitDate: dayjs().format('YYYY-MM-DD'),
  noon: 'MORNING',
  location: '门诊楼2楼 呼吸科诊区3号诊室',
  queueNumber: '08',
  caseNumber: 'MR202506150001'
})

onMounted(() => {
  const { registerId } = route.query
  if (registerId) {
    appointmentInfo.value.registerId = registerId as string
    appointmentInfo.value.caseNumber = `MR${dayjs().format('YYYYMMDD')}${registerId}`
    appointmentInfo.value.queueNumber = String(Number(registerId) % 20 + 1)
  }
})

const goToRecords = () => router.push('/patient/appointments')
const goToHome = () => router.push('/patient/home')
</script>

<style lang="scss" scoped>
.success-page { min-height: 100vh; background: #F5F7FA; padding: 32px 16px; }
.success-card { background: white; border-radius: 16px; padding: 32px 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.success-icon { text-align: center; margin-bottom: 16px; }
.success-title { text-align: center; font-size: 24px; font-weight: 700; color: #4CAF50; }
.success-subtitle { text-align: center; font-size: 14px; color: #6B6B7E; margin-bottom: 24px; }
.info-card { background: #F5F7FA; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #E8E8E8; &:last-child { border-bottom: none; } }
.info-label { font-size: 14px; color: #6B6B7E; }
.info-value { font-size: 14px; color: #1A1A2E; &.highlight { font-size: 18px; font-weight: 700; color: #FF9800; } }
.tips-card { background: #FFF3E0; border-radius: 8px; padding: 12px; margin-bottom: 24px; }
.tips-title { font-size: 14px; font-weight: 500; color: #E76F51; margin-bottom: 8px; }
.tip-item { font-size: 12px; color: #4A4A5E; padding: 4px 0; }
.action-buttons { display: flex; gap: 12px; }
.action-buttons .van-button { flex: 1; height: 44px; }
.action-buttons .van-button--primary { background: #4CAF50; border-color: #4CAF50; }
.action-buttons .van-button--plain { color: #4CAF50; border-color: #4CAF50; }
</style>