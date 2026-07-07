<template>
  <BookingShell title="健康体检" icon="heartbeat-o" tone="#00BCD4" :items="items" />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import BookingShell from './_BookingShell.vue'
import { getPatientCheckCatalog, type PatientMedicalTechnologyVO } from '@/api'

const items = ref<Array<{ name: string; price?: number }>>([])

onMounted(async () => {
  const catalog = await getPatientCheckCatalog().catch(() => undefined)
  items.value = ((catalog?.data || catalog || []) as PatientMedicalTechnologyVO[]).map((item) => ({
    name: item.techName || '体检项目',
    price: item.techPrice,
  }))
})
</script>
