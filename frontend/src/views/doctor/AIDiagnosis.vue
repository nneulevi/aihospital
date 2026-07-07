<template>
  <div class="doctor-ai-page">
    <div class="panel">
      <div class="page-title">AI 辅助诊断</div>
      <div class="page-subtitle">输入主诉、现病史和体征，系统按当前 RAG + LLM 链路逐字输出诊断辅助建议。</div>

      <van-field v-model="form.symptoms" label="主诉" type="textarea" rows="3" placeholder="如：突发头痛伴恶心 2 小时" />
      <van-field v-model="form.history" label="病史" type="textarea" rows="3" placeholder="既往史、用药史、发病经过" />
      <van-field v-model="form.physique" label="体征" type="textarea" rows="3" placeholder="生命体征、神经系统查体等" />

      <van-button block round type="primary" :loading="loading" @click="runDiagnosis">开始分析</van-button>
    </div>

    <div v-if="streamText || suggestions.length" class="panel result-panel">
      <div class="result-title">AI 输出</div>
      <div v-if="streamText" class="stream-text">{{ streamText }}</div>
      <div v-if="suggestions.length" class="suggestion-list">
        <div v-for="(item, index) in suggestions" :key="index" class="suggestion-card">
          <div class="suggestion-name">{{ item.diseaseName || '诊断建议' }}</div>
          <div class="suggestion-meta">置信度 {{ Math.round(Number(item.confidence || 0) * 100) }}%</div>
          <p>{{ item.reason || item.description || '请结合病史、查体和检查结果综合判断。' }}</p>
        </div>
      </div>
      <van-button plain block type="primary" @click="$router.push('/doctor')">返回接诊队列</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { showToast } from 'vant'
import { diagnosisSuggestStream, suggest } from '@/api'

const loading = ref(false)
const streamText = ref('')
const suggestions = ref<any[]>([])
const standaloneConversationId = ref(`standalone-diagnosis:${Date.now()}:${Math.random().toString(36).slice(2)}`)
const form = reactive({
  symptoms: '',
  history: '',
  physique: ''
})

const diagnosisPayload = () => ({
  conversationId: standaloneConversationId.value,
  symptoms: form.symptoms,
  history: form.history,
  physique: form.physique
})

const runDiagnosis = async () => {
  if (!form.symptoms.trim()) {
    showToast('请先填写主诉')
    return
  }
  loading.value = true
  streamText.value = ''
  suggestions.value = []
  let finalPayload: any = null
  try {
    await diagnosisSuggestStream(
      diagnosisPayload(),
      {
        onEvent({ event, data }) {
          if (event === 'delta') streamText.value += data?.text || ''
        },
        onFinal(data) {
          finalPayload = data?.data || data
        },
        onError(data) {
          throw new Error(data?.message || 'AI诊断失败')
        }
      }
    )
    suggestions.value = finalPayload?.suggestions || []
  } catch {
    const res = await suggest(diagnosisPayload())
    const data = res.data || res
    suggestions.value = data.suggestions || []
    streamText.value = data.summary || '已生成诊断辅助建议，请结合患者完整病历复核。'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.doctor-ai-page {
  padding: 12px;
}
.panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
  margin-bottom: 12px;
}
.page-title,
.result-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.page-subtitle {
  margin: 8px 0 16px;
  color: #64748b;
  line-height: 1.6;
}
.stream-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #1f2937;
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
  margin: 12px 0;
}
.suggestion-list {
  display: grid;
  gap: 10px;
  margin: 12px 0;
}
.suggestion-card {
  border: 1px solid #dbeafe;
  background: #f8fbff;
  border-radius: 10px;
  padding: 12px;
}
.suggestion-name {
  font-weight: 700;
  color: #1677ff;
}
.suggestion-meta,
.suggestion-card p {
  color: #64748b;
}
</style>
