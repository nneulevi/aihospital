<template>
  <main class="mini-page">
    <van-nav-bar title="AI 智能问诊" />

    <section class="ai-hero">
      <div>
        <p class="eyebrow">智能预问诊</p>
        <h1>先描述症状，再预约合适科室</h1>
        <p>系统会结合症状文本、问诊记忆和知识库内容给出科室建议，便于后续挂号与医生接诊。</p>
      </div>
      <van-icon name="chat-o" />
    </section>

    <section class="panel">
      <div class="panel-title">
        <h2>症状描述</h2>
        <span>最多 300 字</span>
      </div>
      <van-field
        v-model="symptoms"
        type="textarea"
        rows="5"
        maxlength="300"
        show-word-limit
        placeholder="请描述主要不适、持续时间、伴随症状和既往相关情况"
      />
      <div class="symptom-tags">
        <button
          v-for="item in commonSymptoms"
          :key="item"
          type="button"
          :class="{ active: symptoms.includes(item) }"
          @click="appendSymptom(item)"
        >
          {{ item }}
        </button>
      </div>
      <van-button block type="primary" :loading="loading" @click="analyzeSymptoms">开始分析</van-button>
    </section>

    <section class="panel result">
      <div class="panel-title">
        <h2>辅助建议</h2>
        <span>{{ departments.length ? `${departments.length} 个推荐` : '待分析' }}</span>
      </div>
      <p class="suggestion-text">{{ suggestion }}</p>
      <p v-if="streamText" class="stream-preview">{{ streamText }}</p>
      <div v-if="departments.length" class="dept-list">
        <button
          v-for="(dept, index) in departments"
          :key="dept.deptId || dept.deptName"
          type="button"
          @click="goAppointment(dept)"
        >
          <span class="dept-rank">{{ index + 1 }}</span>
          <span class="dept-main">
            <strong>{{ dept.deptName || '推荐科室' }}</strong>
            <small>{{ dept.reason || '根据症状匹配的优先就诊科室' }}</small>
          </span>
          <van-icon name="arrow" />
        </button>
      </div>
      <div v-else class="empty-result">
        <van-icon name="guide-o" />
        <span>填写症状后，这里会展示推荐科室和挂号入口。</span>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { triage, triageStream } from '@/api'

const router = useRouter()
const symptoms = ref('')
const loading = ref(false)
const suggestion = ref('请先填写症状，系统会给出科室建议并衔接挂号。')
const streamText = ref('')
const departments = ref<any[]>([])
const commonSymptoms = ['头痛', '头晕', '发热', '咳嗽', '胸闷', '腹痛', '恶心', '乏力']

const appendSymptom = (value: string) => {
  symptoms.value = symptoms.value ? `${symptoms.value}、${value}` : value
}

const applyResult = (data: any) => {
  departments.value = data?.recommendations || []
  const first = departments.value[0]
  suggestion.value = first
    ? `建议优先选择${first.deptName || '相关科室'}。${first.reason || ''}`
    : '已完成症状分析，建议结合医生线下问诊进一步确认。'
}

const analyzeSymptoms = async () => {
  const content = symptoms.value.trim()
  if (!content) {
    showToast('请先描述症状')
    return
  }

  loading.value = true
  departments.value = []
  streamText.value = ''
  suggestion.value = '正在建立 AI 流式连接...'

  try {
    let finalPayload: any = null
    await triageStream(
      { symptoms: content },
      {
        onEvent: ({ event, data }) => {
          if (event === 'memory_loaded' || event === 'rag_retrieved' || event === 'llm_generating') {
            suggestion.value = data?.message || suggestion.value
          } else if (event === 'delta') {
            streamText.value += data?.text || ''
          }
        },
        onFinal: (data) => {
          finalPayload = data?.data || data
        },
        onError: (data) => {
          throw new Error(data?.message || 'AI 分析失败')
        },
      },
    )

    if (!finalPayload) {
      throw new Error('AI 流式响应缺少最终结果')
    }
    applyResult(finalPayload)
  } catch {
    try {
      suggestion.value = '流式连接不可用，正在切换普通分析...'
      const res = await triage({ symptoms: content })
      applyResult(res.data || res)
    } catch {
      suggestion.value = '当前可先前往全科或相关专科就诊，医生会结合检查结果进一步判断。'
      departments.value = []
      showToast('AI 分析暂不可用')
    }
  } finally {
    streamText.value = ''
    loading.value = false
  }
}

const goAppointment = (dept: any) => {
  router.push({
    path: '/mini-patient/appointment',
    query: {
      deptId: dept.deptId,
      deptName: dept.deptName,
    },
  })
}
</script>

<style lang="scss" scoped>
.mini-page {
  padding: 0 0 18px;
}

.ai-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 14px 16px 0;
  padding: 18px;
  border-radius: 8px;
  background:
    radial-gradient(circle at right top, rgba(255, 255, 255, 0.42), transparent 38%),
    linear-gradient(135deg, #2a9d8f 0%, #41b8e8 100%);
  color: #ffffff;
  box-shadow: 0 8px 24px rgba(42, 157, 143, 0.14);
}

.ai-hero :deep(.van-icon) {
  flex: 0 0 auto;
  font-size: 42px;
  opacity: 0.92;
}

.ai-hero h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.32;
  overflow-wrap: anywhere;
}

.ai-hero p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.86);
}

.eyebrow {
  margin: 0 0 6px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  font-weight: 600;
}

.panel {
  margin: 14px 16px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-title h2 {
  margin: 0;
  color: #1f2a37;
  font-size: 17px;
}

.panel-title span {
  flex: 0 0 auto;
  color: #8391a3;
  font-size: 12px;
}

:deep(.van-cell) {
  border-radius: 8px;
  background: #f7faff;
  border: 1px solid #e6eef8;
}

.symptom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 16px;
}

.symptom-tags button {
  border: 1px solid #d8e2ee;
  border-radius: 8px;
  background: #f7faff;
  color: #2375ff;
  padding: 7px 10px;
  font-size: 13px;
}

.symptom-tags button.active {
  border-color: #2375ff;
  background: #eaf2ff;
}

:deep(.van-button--primary) {
  background: #2375ff;
  border-color: #2375ff;
}

.suggestion-text {
  margin: 0;
  color: #5b6b80;
  font-size: 14px;
  line-height: 1.65;
}

.stream-preview {
  margin: 10px 0 0;
  padding: 10px 12px;
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid #d7ebff;
  border-radius: 8px;
  background: #f7fbff;
  color: #305066;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.dept-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.dept-list button {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  border: 1px solid #e6ebf2;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px;
}

.dept-rank {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #eaf2ff;
  color: #2375ff;
  font-size: 14px;
  font-weight: 700;
}

.dept-main {
  min-width: 0;
  flex: 1;
}

.dept-list strong,
.dept-list small {
  display: block;
}

.dept-list strong {
  color: #1f2a37;
  font-size: 15px;
}

.dept-list small {
  margin-top: 5px;
  color: #687789;
  font-size: 12px;
  line-height: 1.5;
}

.dept-list :deep(.van-icon) {
  color: #b5c1cf;
}

.empty-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 12px;
  border-radius: 8px;
  background: #f7faff;
  color: #687789;
  font-size: 13px;
  line-height: 1.5;
}

.empty-result :deep(.van-icon) {
  flex: 0 0 auto;
  color: #2375ff;
  font-size: 20px;
}
</style>
