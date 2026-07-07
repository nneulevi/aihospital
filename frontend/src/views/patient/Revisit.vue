<template>
  <BookingShell title="复诊预约" icon="calendar-o" tone="#9C27B0" :items="items" />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import BookingShell from './_BookingShell.vue'
import { getRecords } from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const items = ref<Array<{ name: string; price?: number }>>([])

onMounted(async () => {
  if (!userStore.patientId) return
  const res = await getRecords({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } }).catch(() => undefined)
  const records = res?.data?.records || res?.records || []
  items.value = records.map((record: any) => ({
    name: `${record.deptName || '门诊科室'} · ${record.doctorName || '医生待确认'}`,
  }))
})
</script>
