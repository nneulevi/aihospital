<!-- src/views/patient/RecordDetail.vue -->
<template>
  <div class="record-detail-page">
    <van-nav-bar title="病历详情" fixed placeholder left-arrow @click-left="() => router.back()" />

    <div v-if="loading" class="loading-state"><van-loading size="48px" /><p>加载中...</p></div>

    <div v-else class="detail-content">
      <!-- 基本信息 -->
      <div class="info-card">
        <div class="card-header"><span class="card-icon">📋</span><span class="card-title">基本信息</span></div>
        <div class="info-grid">
          <div class="info-item"><span class="info-label">就诊日期</span><span class="info-value">{{ formatDateTime(detail.visitDate) }}</span></div>
          <div class="info-item"><span class="info-label">就诊科室</span><span class="info-value">{{ detail.deptName }}</span></div>
          <div class="info-item"><span class="info-label">就诊医生</span><span class="info-value">{{ detail.doctorName }}</span></div>
          <div class="info-item"><span class="info-label">病历号</span><span class="info-value">{{ (detail as any).caseNumber || '--' }}</span></div>
        </div>
      </div>

      <!-- 患者信息 -->
      <div class="info-card">
        <div class="card-header"><span class="card-icon">👤</span><span class="card-title">患者信息</span></div>
        <div class="info-grid">
          <div class="info-item"><span class="info-label">姓名</span><span class="info-value">张明</span></div>
          <div class="info-item"><span class="info-label">性别</span><span class="info-value">男</span></div>
          <div class="info-item"><span class="info-label">年龄</span><span class="info-value">35岁</span></div>
          <div class="info-item"><span class="info-label">过敏史</span><span class="info-value">无</span></div>
        </div>
      </div>

      <!-- 诊断结果 -->
      <div class="info-card">
        <div class="card-header"><span class="card-icon">✅</span><span class="card-title">诊断结果</span></div>
        <div class="diagnosis-result">
          <div class="diagnosis-text">{{ detail.diagnosis || '暂无诊断' }}</div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <van-button plain round @click="reInquiry"><van-icon name="chat-o" /> 重新问诊</van-button>
        <van-button type="primary" round @click="reRegister"><van-icon name="plus" /> 再次挂号</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import type { PatientRecordListVO } from '@/api/model'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<PatientRecordListVO & { caseNumber?: string; deptId?: number }>({})

const mockGetRecordDetail = async (id: number): Promise<PatientRecordListVO> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        registerId: id,
        visitDate: '2026-05-20',
        deptName: '呼吸内科',
        doctorName: '张敏',
        diagnosis: '上呼吸道感染',
        visitState: 'FINISHED',
        visitStateName: '已完成',
        caseNumber: 'HN202600001',
        deptId: 2
      } as any)
    }, 500)
  })
}

const loadDetail = async () => {
  const id = Number(route.params.id)
  if (!id) { showToast('参数错误'); return }
  loading.value = true
  try {
    detail.value = await mockGetRecordDetail(id)
  } catch { showToast('加载失败') } finally { loading.value = false }
}

const formatDateTime = (date?: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : ''
const reInquiry = () => router.push('/patient/ai')
const reRegister = () => router.push({
  name: 'Appointment',
  query: {
    deptId: (detail.value as any).deptId?.toString(),
    deptName: detail.value.deptName
  }
})

onMounted(loadDetail)
</script>

<style lang="scss" scoped>
.record-detail-page { min-height: 100vh; background: #F5F7FA; padding-bottom: 80px; }
.loading-state { text-align: center; padding: 60px 0; color: #6B6B7E; }
.info-card { background: white; margin: 12px; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-bottom: 1px solid #E8E8E8; background: #F5F7FA; }
.card-icon { font-size: 18px; }
.card-title { flex: 1; font-size: 16px; font-weight: 500; }
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; padding: 12px 16px; }
.info-item { display: flex; flex-direction: column; .info-label { font-size: 12px; color: #6B6B7E; } .info-value { font-size: 14px; color: #1A1A2E; margin-top: 2px; } }
.diagnosis-result { padding: 16px; .diagnosis-text { font-size: 16px; font-weight: 500; color: #1A1A2E; } }
.action-bar { position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 12px; padding: 12px 16px; background: white; border-top: 1px solid #E8E8E8; }
.action-bar .van-button { flex: 1; height: 44px; }
.action-bar .van-button--primary { background: #4CAF50; border-color: #4CAF50; }
</style>