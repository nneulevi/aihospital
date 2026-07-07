<template>
  <div class="status-page">
    <van-nav-bar title="就诊报到" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="status-card">
      <van-icon name="location-o" size="52" color="#4CAF50" />
      <strong>到院报到</strong>
      <p>{{ checkinMessage }}</p>
      <div v-if="todayRegister.registerId" class="info-grid">
        <div><span>科室</span><strong>{{ todayRegister.deptName || '-' }}</strong></div>
        <div><span>医生</span><strong>{{ todayRegister.doctorName || '-' }}</strong></div>
        <div><span>序号</span><strong>{{ todayRegister.queueNo || '-' }}</strong></div>
        <div><span>状态</span><strong>{{ todayRegister.visitStateName || '-' }}</strong></div>
      </div>
      <van-button type="primary" round block :loading="loading" :disabled="!todayRegister.registerId" @click="submitCheckin">
        确认报到
      </van-button>
      <van-button plain round block @click="router.push('/patient/records')">查看就诊记录</van-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { getTodayRegister, submitPatientCheckin, type PatientTodayRegisterVO } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const todayRegister = reactive<PatientTodayRegisterVO>({})

const checkinMessage = computed(() => {
  if (!todayRegister.registerId) return '暂无需要报到的今日挂号记录。'
  if (todayRegister.visitState === 'CHECKED_IN') return '您已完成报到，请前往候诊区等待叫号。'
  return '请确认信息无误后完成报到。'
})

const loadTodayRegister = async () => {
  if (!userStore.patientId) return
  const res = await getTodayRegister(userStore.patientId).catch(() => undefined)
  Object.assign(todayRegister, res?.data || res || {})
}

const submitCheckin = async () => {
  if (!userStore.patientId || !todayRegister.registerId) return
  loading.value = true
  try {
    const res = await submitPatientCheckin(userStore.patientId, todayRegister.registerId)
    Object.assign(todayRegister, res.data || res)
    showToast('报到成功')
  } catch {
    showToast('报到失败，请到分诊台处理')
  } finally {
    loading.value = false
  }
}

onMounted(loadTodayRegister)
</script>

<style lang="scss" scoped>
.status-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.status-card { display: grid; gap: 12px; justify-items: center; text-align: center; padding: 24px 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.status-card strong { color: #1a1a2e; font-size: 18px; }
.status-card p { margin: 0; color: #5b6b80; line-height: 1.65; }
.status-card :deep(.van-button--primary) { background: #4caf50; border-color: #4caf50; }
.info-grid { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.info-grid div { padding: 12px; border-radius: 8px; background: #f5f7fa; }
.info-grid span, .info-grid strong { display: block; }
.info-grid span { color: #7a8797; font-size: 12px; }
.info-grid strong { margin-top: 4px; color: #1f2a37; font-size: 15px; }
</style>
