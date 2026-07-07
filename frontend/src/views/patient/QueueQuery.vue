<template>
  <div class="status-page">
    <van-nav-bar title="候诊查询" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="status-card">
      <van-icon name="clock-o" size="52" color="#9C27B0" />
      <strong>候诊状态</strong>
      <p>{{ queue.message || '暂无候诊队列信息。完成挂号并报道后可查询候诊状态。' }}</p>
      <div class="queue-grid">
        <div><strong>{{ queue.queueNo || '-' }}</strong><span>我的序号</span></div>
        <div><strong>{{ queue.waitingAhead ?? '-' }}</strong><span>前方等待</span></div>
        <div><strong>{{ queue.deptName || '-' }}</strong><span>就诊科室</span></div>
        <div><strong>{{ queue.visitStateName || '-' }}</strong><span>当前状态</span></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getPatientQueueStatus, type PatientQueueStatusVO } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const queue = reactive<PatientQueueStatusVO>({})

onMounted(async () => {
  if (!userStore.patientId) return
  const res = await getPatientQueueStatus(userStore.patientId).catch(() => undefined)
  if (res) Object.assign(queue, res.data || res)
})
</script>

<style lang="scss" scoped>
.status-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.status-card { display: grid; gap: 12px; justify-items: center; text-align: center; padding: 24px 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.status-card > strong { color: #1a1a2e; font-size: 18px; }
.status-card p { margin: 0; color: #5b6b80; line-height: 1.65; }
.queue-grid { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.queue-grid div { padding: 12px; border-radius: 8px; background: #f5f7fa; }
.queue-grid strong, .queue-grid span { display: block; }
.queue-grid strong { color: #4caf50; font-size: 20px; }
.queue-grid span { margin-top: 4px; color: #6b6b7e; font-size: 12px; }
</style>
