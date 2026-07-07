<template>
  <div class="list-page">
    <van-nav-bar title="报告查询" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="hint-card">
      <strong>检查检验报告</strong>
      <p>展示医生开立并由医技端完成的检查、检验报告，结果状态与后端业务记录同步。</p>
    </section>
    <article v-for="item in reports" :key="item.reportId" class="list-card" @click="router.push(`/patient/record/${item.registerId}`)">
      <div class="list-head">
        <strong>{{ item.itemName || '检查检验项目' }}</strong>
        <van-tag :type="item.status === 'COMPLETED' ? 'success' : 'warning'">{{ item.statusName || item.status || '处理中' }}</van-tag>
      </div>
      <p>{{ item.result || '报告尚未完成，请以医技科室最终提交结果为准。' }}</p>
      <small>{{ item.itemType === 'CHECK' ? '检查' : '检验' }} · {{ item.deptName || '-' }} · {{ item.reportTime || item.creationTime || '-' }}</small>
    </article>
    <van-empty v-if="!reports.length && !loading" description="暂无报告记录" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { getPatientReports, type PatientReportVO } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const reports = ref<PatientReportVO[]>([])

const load = async () => {
  if (!userStore.patientId) return
  loading.value = true
  try {
    const res = await getPatientReports({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 20 } })
    reports.value = res.data?.records || res.records || []
  } catch {
    showToast('报告记录加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.list-page { min-height: 100vh; background: #f5f7fa; padding: 12px 16px 80px; }
.hint-card, .list-card { margin-bottom: 10px; padding: 14px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.hint-card strong, .list-head strong { color: #1a1a2e; }
.hint-card p, .list-card p { margin: 8px 0 4px; color: #5b6b80; line-height: 1.6; }
.list-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.list-card small { color: #8b8b9e; }
</style>
