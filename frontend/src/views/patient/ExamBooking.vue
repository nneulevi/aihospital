<template>
  <BookingShell title="检查预约" icon="scan-o" tone="#4CAF50" :items="items" :requests="requests" :submit-handler="submitCheck" />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showSuccessToast, showToast } from 'vant'
import BookingShell from './_BookingShell.vue'
import {
  createPatientCheckRequest,
  getPatientCheckCatalog,
  getPatientCheckRequests,
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
  const catalog = await getPatientCheckCatalog().catch(() => undefined)
  items.value = ((catalog?.data || catalog || []) as PatientMedicalTechnologyVO[]).map((item) => ({
    id: item.techId,
    name: item.techName || '检查项目',
    price: item.techPrice,
  }))
  if (userStore.patientId) {
    const res = await getPatientCheckRequests({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } }).catch(() => undefined)
    requests.value = res?.data?.records || res?.records || []
    const records = await getRecords({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } }).catch(() => undefined)
    activeRegisterId.value = (records?.data?.records || records?.records || [])
      .find((record: any) => !['REFUNDED', 'CANCELLED'].includes(record.visitState))?.registerId
  }
}

const submitCheck = async (ids: number[]) => {
  if (!userStore.patientId || !activeRegisterId.value) {
    showToast('请先完成门诊挂号，再预约检查项目')
    return
  }
  await createPatientCheckRequest({
    patientId: userStore.patientId,
    registerId: activeRegisterId.value,
    medicalTechnologyIds: ids,
  })
  showSuccessToast('检查申请已提交')
  await loadData()
}

onMounted(loadData)
</script>
