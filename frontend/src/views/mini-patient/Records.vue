<template>
  <main class="mini-page">
    <van-nav-bar title="电子病历" />
    <section class="record-list">
      <button v-for="record in records" :key="record.registerId" type="button" class="record-card">
        <span class="tag">{{ record.visitState || '已就诊' }}</span>
        <strong>{{ record.doctorName || '接诊医生' }} · {{ record.deptName || '门诊科室' }}</strong>
        <span>{{ formatDate(record.visitDate) }}</span>
        <p>{{ record.diagnosis || '医生诊疗记录已归档，可在详情中继续查看。' }}</p>
      </button>
      <van-empty v-if="!records.length" description="暂无就诊记录" />
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { getRecords } from '@/api'
import { useUserStore } from '@/stores/user'
import type { PatientRecordListVO } from '@/api/model'

const userStore = useUserStore()
const records = ref<PatientRecordListVO[]>([])
const formatDate = (value?: string) => value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '时间待确认'

const loadRecords = async () => {
  if (!userStore.patientId) return
  try {
    const res = await getRecords({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } })
    records.value = res.data?.records || res.records || []
  } catch {
    records.value = []
  }
}

onMounted(loadRecords)
</script>

<style lang="scss" scoped>
.record-list {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
}

.record-card {
  text-align: left;
  border: 0;
  border-radius: 8px;
  background: #ffffff;
  padding: 15px;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.record-card .tag {
  display: inline-block;
  margin-bottom: 8px;
  border-radius: 8px;
  background: #ecfdf5;
  color: #2a9d8f;
  padding: 4px 8px;
  font-size: 12px;
}

.record-card strong,
.record-card span,
.record-card p {
  display: block;
}

.record-card strong {
  color: #1f2a37;
  font-size: 15px;
}

.record-card span {
  margin-top: 6px;
  color: #687789;
  font-size: 12px;
}

.record-card p {
  margin: 10px 0 0;
  color: #5b6b80;
  font-size: 13px;
  line-height: 1.55;
}
</style>
