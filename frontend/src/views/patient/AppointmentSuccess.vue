<!-- src/views/patient/AppointmentSuccess.vue -->
<template>
  <div class="success-page">
    <div class="success-card">
      <div class="success-icon"><van-icon name="checked" size="64" color="#8CB369" /></div>
      <div class="success-title">挂号成功</div>
      <div class="success-subtitle">请按时到院就诊</div>

      <div v-if="loading" class="info-card muted">
        <van-loading size="20" color="#4CAF50">正在获取挂号信息...</van-loading>
      </div>
      <div v-else-if="loadError" class="info-card muted">
        {{ loadError }}
      </div>
      <div v-else class="info-card">
        <div class="info-row"><span class="info-label">就诊科室</span><span class="info-value">{{ appointmentInfo.deptName }}</span></div>
        <div class="info-row"><span class="info-label">就诊医生</span><span class="info-value">{{ appointmentInfo.doctorName }}</span></div>
        <div class="info-row"><span class="info-label">就诊日期</span><span class="info-value">{{ appointmentInfo.visitDate }}</span></div>
        <div class="info-row"><span class="info-label">当前状态</span><span class="info-value highlight">{{ appointmentInfo.visitStateName }}</span></div>
        <div class="info-row"><span class="info-label">挂号编号</span><span class="info-value">{{ appointmentInfo.registerId }}</span></div>
      </div>

      <div class="tips-card">
        <div class="tips-title">温馨提示</div>
        <div class="tip-item">📋 请携带身份证和医保卡就诊</div>
        <div class="tip-item">⏰ 请提前15分钟到达候诊区</div>
        <div class="tip-item">💰 当前挂号成功后进入候诊流程，医生开立检查、检验、处方等项目后可在缴费页处理费用</div>
        <div class="tip-item">↩ 如需取消挂号，请在就诊前1小时操作</div>
      </div>

      <div class="action-buttons">
        <van-button plain type="primary" round @click="goToRecords">查看挂号记录</van-button>
        <van-button plain type="primary" round @click="goToOrders">查看缴费</van-button>
        <van-button type="primary" round @click="goToHome">返回首页</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecordDetail } from '@/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const loadError = ref('')

const appointmentInfo = ref({
  registerId: '',
  deptName: '',
  doctorName: '',
  visitDate: '',
  visitStateName: ''
})

onMounted(async () => {
  const { registerId } = route.query
  if (!registerId) {
    loadError.value = '未获取到挂号编号，可到挂号记录中查看。'
    return
  }
  loading.value = true
  try {
    const res: any = await getRecordDetail(Number(registerId))
    const data = res.data || res
    appointmentInfo.value = {
      registerId: String(data.registerId || registerId),
      deptName: data.deptName || '待分配科室',
      doctorName: data.doctorName || '待分配医生',
      visitDate: data.visitDate || '',
      visitStateName: data.visitStateName || data.visitState || '已挂号'
    }
  } catch {
    loadError.value = '挂号已提交，但详情暂时加载失败，可到挂号记录中查看。'
  } finally {
    loading.value = false
  }
})

const goToRecords = () => router.push('/patient/records')
const goToOrders = () => router.push('/patient/orders')
const goToHome = () => router.push('/patient/home')
</script>

<style lang="scss" scoped>
.success-page { min-height: 100vh; background: #F5F7FA; padding: 32px 16px; }
.success-card { background: white; border-radius: 8px; padding: 32px 20px; box-shadow: 0 1px 8px rgba(31,42,55,.08); }
.success-icon { text-align: center; margin-bottom: 16px; }
.success-title { text-align: center; font-size: 24px; font-weight: 700; color: #4CAF50; }
.success-subtitle { text-align: center; font-size: 14px; color: #687789; margin-bottom: 24px; }
.info-card { background: #F7FBF7; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.info-card.muted { color: #687789; text-align: center; }
.info-row { display: flex; justify-content: space-between; gap: 16px; padding: 8px 0; border-bottom: 1px solid #E6EBF2; &:last-child { border-bottom: none; } }
.info-label { font-size: 14px; color: #687789; }
.info-value { font-size: 14px; color: #1A1A2E; text-align: right; &.highlight { font-size: 18px; font-weight: 700; color: #4CAF50; } }
.tips-card { background: #EEF8F0; border-radius: 8px; padding: 12px; margin-bottom: 24px; }
.tips-title { font-size: 14px; font-weight: 500; color: #2E7D32; margin-bottom: 8px; }
.tip-item { font-size: 12px; color: #1A1A2E; padding: 4px 0; }
.action-buttons { display: flex; gap: 12px; }
.action-buttons .van-button { flex: 1; height: 44px; }
.action-buttons .van-button--primary { background: #4CAF50; border-color: #4CAF50; }
.action-buttons .van-button--plain { color: #4CAF50; border-color: #4CAF50; }
</style>
