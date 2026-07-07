<template>
  <div class="headct-report-page">
    <section class="workbench-hero">
      <div>
        <p>影像报告</p>
        <h1>头部 CT 检查报告工作台</h1>
        <span>从医生端进入报告服务，处理 AI 草稿、审核、签署和发布。</span>
      </div>
      <van-button plain type="primary" size="small" @click="reloadWorkbench">
        刷新工作台
      </van-button>
    </section>

    <section class="identity-card">
      <div>
        <span>当前医生</span>
        <strong>{{ actorId }}</strong>
      </div>
      <div>
        <span>工作角色</span>
        <strong>报告医生</strong>
      </div>
      <div>
        <span>接入方式</span>
        <strong>主平台内嵌</strong>
      </div>
    </section>

    <section class="iframe-card">
      <iframe
        ref="iframeRef"
        title="头部 CT 检查报告工作台"
        :src="workbenchUrl"
        @load="loaded = true"
      ></iframe>
      <div v-if="!loaded" class="loading-mask">
        正在载入报告工作台...
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const iframeRef = ref<HTMLIFrameElement | null>(null)
const loaded = ref(false)

const actorId = computed(() => {
  const user = userStore.userInfo as any
  return String(user?.employeeId || user?.doctorId || userStore.doctorId || 'doctor-001')
})

const reportBaseUrl = computed(() => {
  return String(import.meta.env.VITE_HEADCT_REPORT_WORKBENCH_URL || 'http://127.0.0.1:8030').replace(/\/$/, '')
})

const workbenchUrl = computed(() => {
  const url = new URL(reportBaseUrl.value)
  url.searchParams.set('actorId', actorId.value)
  url.searchParams.set('actorRole', 'reporting_doctor')
  url.searchParams.set('embedded', 'project2')
  return url.toString()
})

const reloadWorkbench = () => {
  loaded.value = false
  iframeRef.value?.contentWindow?.location.reload()
}
</script>

<style lang="scss" scoped>
.headct-report-page {
  min-height: calc(100vh - 116px);
  padding: 16px;
  background: #f5f7fa;
}

.workbench-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  margin-bottom: 12px;
  border-radius: 12px;
  color: #ffffff;
  background: linear-gradient(135deg, #005b96 0%, #0077b6 100%);
  box-shadow: 0 8px 24px rgba(0, 91, 150, 0.18);
}

.workbench-hero p {
  margin: 0 0 5px;
  opacity: 0.82;
  font-size: 13px;
}

.workbench-hero h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.3;
}

.workbench-hero span {
  display: block;
  margin-top: 8px;
  opacity: 0.88;
  font-size: 13px;
  line-height: 1.55;
}

.identity-card {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.identity-card div {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5edf5;
  border-radius: 10px;
  background: #ffffff;
}

.identity-card span {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.identity-card strong {
  display: block;
  margin-top: 5px;
  color: #1f2937;
  overflow-wrap: anywhere;
}

.iframe-card {
  position: relative;
  min-height: 720px;
  border: 1px solid #d9e4ef;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}

.iframe-card iframe {
  display: block;
  width: 100%;
  min-height: 720px;
  border: 0;
  background: #ffffff;
}

.loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  background: #ffffff;
}

@media (max-width: 760px) {
  .workbench-hero,
  .identity-card {
    grid-template-columns: 1fr;
  }

  .workbench-hero {
    display: grid;
  }
}
</style>
