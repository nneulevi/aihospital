<template>
  <div class="list-page">
    <van-nav-bar title="处方查询" fixed placeholder left-arrow @click-left="router.back()" />
    <article v-for="item in prescriptions" :key="item.prescriptionId" class="list-card">
      <div class="list-head">
        <strong>{{ item.prescriptionNo || `处方 ${item.prescriptionId}` }}</strong>
        <van-tag :type="['PAID', 'DISPENSED'].includes(item.status || '') ? 'success' : 'warning'">{{ item.statusName || item.status || '待处理' }}</van-tag>
      </div>
      <p>{{ item.drugSummary || '处方明细待药房确认' }}</p>
      <p>金额：¥{{ Number(item.totalAmount || 0).toFixed(2) }}</p>
      <small>{{ item.doctorName || '-' }} · {{ item.creationTime || '-' }}</small>
    </article>
    <van-empty v-if="!prescriptions.length && !loading" description="暂无处方记录" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getPatientPrescriptions, type PatientPrescriptionVO } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const prescriptions = ref<PatientPrescriptionVO[]>([])

const load = async () => {
  if (!userStore.patientId) return
  loading.value = true
  try {
    const res = await getPatientPrescriptions({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 50 } })
    prescriptions.value = res.data?.records || res.records || []
  } catch {
    showToast('处方记录加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.list-page { min-height: 100vh; background: #f5f7fa; padding: 12px 16px 80px; }
.list-card { margin-bottom: 10px; padding: 14px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.list-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.list-head strong { color: #1a1a2e; }
.list-card p { margin: 8px 0 4px; color: #5b6b80; }
.list-card small { color: #8b8b9e; }
</style>
