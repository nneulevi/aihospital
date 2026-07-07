<template>
  <BookingShell title="检验预约" icon="medical-o" tone="#2196F3" :items="items" :requests="requests" :submit-handler="submitInspection" />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showSuccessToast, showToast } from 'vant'
import BookingShell from './_BookingShell.vue'
import {
  createPatientInspectionRequest,
  getPatientInspectionCatalog,
  getPatientInspectionRequests,
  getRecords,
  type PatientMedicalRequestVO,
  type PatientMedicalTechnologyVO,
} from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Array<{ id?: number; name: string; price?: number }>>([])
const requests = ref<PatientMedicalRequestVO[]>([])
const activeRegisterId = ref<number | undefined>()

const loadData = async () => {
  const catalog = await getPatientInspectionCatalog().catch(() => undefined)
  items.value = ((catalog?.data || catalog || []) as PatientMedicalTechnologyVO[]).map((item) => ({
    id: item.techId,
    name: item.techName || '检验项目',
    price: item.techPrice,
  }))
  if (userStore.patientId) {
    const res = await getPatientInspectionRequests({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } }).catch(() => undefined)
    requests.value = res?.data?.records || res?.records || []
    const records = await getRecords({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } }).catch(() => undefined)
    activeRegisterId.value = (records?.data?.records || records?.records || [])
      .find((record: any) => !['REFUNDED', 'CANCELLED'].includes(record.visitState))?.registerId
  }
}

const submitInspection = async (ids: number[]) => {
  if (!userStore.patientId || !activeRegisterId.value) {
    showToast('请先完成门诊挂号，再预约检验项目')
    return
  }
  await createPatientInspectionRequest({
    patientId: userStore.patientId,
    registerId: activeRegisterId.value,
    medicalTechnologyIds: ids,
  })
  showSuccessToast('检验申请已提交')
  await loadData()
}

onMounted(loadData)
</script>
