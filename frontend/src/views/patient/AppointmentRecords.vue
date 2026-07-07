<template>
  <div class="records-page">
    <van-nav-bar title="挂号记录" fixed placeholder left-arrow @click-left="router.back()" />
    <article v-for="item in records" :key="item.registerId" class="record-card" @click="router.push(`/patient/record/${item.registerId}`)">
      <div class="record-head">
        <strong>{{ item.deptName || '门诊科室' }}</strong>
        <van-tag type="primary">{{ item.visitStateName || item.visitState || '就诊记录' }}</van-tag>
      </div>
      <p>{{ item.doctorName || '接诊医生待确认' }} · {{ item.visitDate || item.registrationTime || '-' }}</p>
      <small>病历号：{{ item.caseNumber || '-' }}</small>
    </article>
    <van-empty v-if="!records.length && !loading" description="暂无挂号记录" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { getRecords } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const records = ref<any[]>([])

const loadRecords = async () => {
  if (!userStore.patientId) return
  loading.value = true
  try {
    const res = await getRecords({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } })
    records.value = res.data?.records || res.records || []
  } catch {
    showToast('挂号记录加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadRecords)
</script>

<style lang="scss" scoped>
.records-page { min-height: 100vh; background: #f5f7fa; padding: 12px 16px 80px; }
.record-card { margin-bottom: 10px; padding: 14px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.record-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.record-head strong { color: #1a1a2e; font-size: 16px; }
.record-card p { margin: 8px 0 4px; color: #5b6b80; font-size: 14px; }
.record-card small { color: #8b8b9e; }
</style>
