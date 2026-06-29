<template>
  <div class="record-detail-page">
    <van-nav-bar title="病历详情" fixed placeholder left-arrow @click-left="router.back" />

    <div v-if="loading" class="loading-state">
      <van-loading size="36px" />
      <p>正在加载病历...</p>
    </div>

    <van-empty v-else-if="!detail.registerId" description="未找到病历详情" />

    <div v-else class="detail-content">
      <section class="info-card">
        <div class="card-header">
          <van-icon name="records-o" />
          <span>基本信息</span>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">挂号ID</span>
            <span class="value">{{ detail.registerId }}</span>
          </div>
          <div class="info-item">
            <span class="label">就诊日期</span>
            <span class="value">{{ formatDateTime(detail.visitDate) }}</span>
          </div>
          <div class="info-item">
            <span class="label">就诊科室</span>
            <span class="value">{{ detail.deptName || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="label">接诊医生</span>
            <span class="value">{{ detail.doctorName || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态</span>
            <span class="value">{{ detail.visitStateName || detail.visitState || '--' }}</span>
          </div>
        </div>
      </section>

      <section class="info-card">
        <div class="card-header">
          <van-icon name="checked" />
          <span>诊断结果</span>
        </div>
        <div class="diagnosis-text">{{ detail.diagnosis || '暂无诊断结果' }}</div>
      </section>

      <div class="action-bar">
        <van-button plain round icon="chat-o" @click="reInquiry">重新问诊</van-button>
        <van-button type="primary" round icon="plus" @click="reRegister">再次挂号</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import { getRecordDetail } from '@/api'
import type { PatientRecordListVO } from '@/api/model'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<PatientRecordListVO>({})

const loadDetail = async () => {
  const id = Number(route.params.id)
  if (!id) {
    showToast('病历参数错误')
    return
  }

  loading.value = true
  try {
    const res = await getRecordDetail(id)
    detail.value = (res.data || res || {}) as PatientRecordListVO
  } catch {
    showToast('病历详情加载失败')
    detail.value = {}
  } finally {
    loading.value = false
  }
}

const formatDateTime = (date?: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '--'
const reInquiry = () => router.push('/patient/ai')
const reRegister = () => router.push({ name: 'Appointment', query: { deptName: detail.value.deptName } })

onMounted(loadDetail)
</script>

<style lang="scss" scoped>
.record-detail-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 80px;
}
.loading-state {
  text-align: center;
  padding: 64px 0;
  color: #697386;
}
.detail-content {
  padding: 12px;
}
.info-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #eef0f3;
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  font-weight: 600;
  color: #263238;
  border-bottom: 1px solid #eef0f3;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.label {
  font-size: 12px;
  color: #7a8699;
}
.value {
  font-size: 14px;
  color: #263238;
  word-break: break-word;
}
.diagnosis-text {
  padding: 16px;
  line-height: 1.7;
  color: #263238;
}
.action-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #eef0f3;
}
.action-bar .van-button {
  flex: 1;
}
</style>
