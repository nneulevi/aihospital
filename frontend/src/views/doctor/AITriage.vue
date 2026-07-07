<template>
  <div class="doctor-ai-page">
    <div class="panel header-panel">
      <div>
        <div class="page-title">AI 分诊对话</div>
        <div class="page-subtitle">像在线助手一样连续追问患者症状，系统基于当前 RAG + LLM 链路逐字输出分诊建议。</div>
      </div>
      <van-button plain size="small" icon="replay" @click="newConversation">新会话</van-button>
    </div>

    <div class="panel chat-panel">
      <div class="messages" ref="messageListRef">
        <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
          <div class="message-bubble">
            <div class="message-role">{{ message.role === 'user' ? '医生输入' : 'AI 分诊' }}</div>
            <div class="message-text">{{ message.content }}</div>
          </div>
        </div>
        <div v-if="loading && !activeAssistantText" class="message-row assistant">
          <div class="message-bubble muted">
            <div class="message-role">AI 分诊</div>
            <div class="message-text">{{ loadingHint }}</div>
          </div>
        </div>
      </div>

      <div v-if="recommendations.length" class="recommend-card">
        <div class="result-title">当前推荐科室</div>
        <div v-for="item in recommendations" :key="`${item.deptId}-${item.deptName}`" class="recommend-item">
          <div>
            <div class="dept-name">{{ item.deptName || '相关科室' }}</div>
            <div class="dept-reason">{{ item.reason || '需结合患者完整病史和检查结果复核。' }}</div>
          </div>
          <van-tag type="primary">{{ confidenceText(item.confidence) }}</van-tag>
        </div>
      </div>
    </div>

    <div class="panel input-panel">
      <van-field
        v-model="draft"
        type="textarea"
        rows="3"
        autosize
        placeholder="例如：患者突发头痛伴恶心，持续2小时；可继续追问：如果没有发热和外伤，下一步怎么分诊？"
      />
      <div class="input-actions">
        <van-button plain size="small" @click="fillExample">填入示例</van-button>
        <van-button type="primary" round :loading="loading" :disabled="!draft.trim()" @click="sendMessage">发送</van-button>
      </div>
    </div>

    <div class="footer-actions">
      <van-button plain block type="primary" @click="$router.push('/doctor')">查看待诊队列</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { showToast } from 'vant'
import { triage, triageStream } from '@/api'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

type Recommendation = {
  deptId?: number
  deptName?: string
  confidence?: number
  reason?: string
}

const draft = ref('')
const loading = ref(false)
const loadingHint = ref('正在连接 AI 分诊服务...')
const activeAssistantText = ref('')
const recommendations = ref<Recommendation[]>([])
const messageListRef = ref<HTMLElement | null>(null)
const conversationId = ref(createConversationId())
const messages = ref<ChatMessage[]>([
  {
    id: createMessageId(),
    role: 'assistant',
    content: '请描述患者主诉、持续时间、危险信号和已知病史。我会按分诊优先级给出建议，你可以继续追问或补充信息。'
  }
])

function createConversationId() {
  return `doctor-triage:${Date.now()}:${Math.random().toString(36).slice(2)}`
}

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function scrollToBottom() {
  nextTick(() => {
    const el = messageListRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function appendAssistantDelta(text: string) {
  activeAssistantText.value += text
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant' && last.id.startsWith('stream-')) {
    last.content = activeAssistantText.value
  } else {
    messages.value.push({
      id: `stream-${createMessageId()}`,
      role: 'assistant',
      content: activeAssistantText.value
    })
  }
  scrollToBottom()
}

function appendAssistantFinal(text: string) {
  const content = text.trim() || '已完成分诊分析，请结合患者实际情况复核。'
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant' && last.id.startsWith('stream-')) {
    last.id = createMessageId()
    last.content = content
  } else {
    messages.value.push({ id: createMessageId(), role: 'assistant', content })
  }
  activeAssistantText.value = ''
  scrollToBottom()
}

function recommendationSummary(items: Recommendation[]) {
  if (!items.length) {
    return ''
  }
  return items
    .map((item, index) => `${index + 1}. ${item.deptName || '相关科室'}：匹配度 ${confidenceText(item.confidence)}。${item.reason || ''}`)
    .join('\n')
}

function confidenceText(value?: number) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return '待评估'
  }
  return `${Math.round(numeric * 100)}%`
}

function requestPayload(content: string) {
  return {
    conversationId: conversationId.value,
    symptoms: content
  }
}

async function sendMessage() {
  const content = draft.value.trim()
  if (!content) {
    showToast('请先输入患者情况或追问内容')
    return
  }

  messages.value.push({ id: createMessageId(), role: 'user', content })
  draft.value = ''
  loading.value = true
  loadingHint.value = '正在加载长上下文记忆...'
  activeAssistantText.value = ''
  scrollToBottom()

  let finalPayload: any = null
  try {
    await triageStream(requestPayload(content), {
      onEvent({ event, data }) {
        if (event === 'memory_loaded') {
          loadingHint.value = data?.message || '正在加载长上下文记忆...'
        } else if (event === 'rag_retrieved') {
          loadingHint.value = data?.message || '正在检索医学知识库...'
        } else if (event === 'llm_generating') {
          loadingHint.value = data?.message || '正在逐字生成分诊建议...'
        } else if (event === 'delta') {
          appendAssistantDelta(data?.text || '')
        }
      },
      onFinal(data) {
        finalPayload = data?.data || data
      },
      onError(data) {
        throw new Error(data?.message || 'AI分诊失败')
      }
    })

    applyFinalPayload(finalPayload)
  } catch {
    try {
      const res = await triage(requestPayload(content))
      applyFinalPayload(res.data || res)
    } catch {
      appendAssistantFinal('AI 分诊服务暂时不可用，请稍后重试或改由人工判断分诊优先级。')
      showToast('AI分诊失败，请重试')
    }
  } finally {
    loading.value = false
    activeAssistantText.value = ''
  }
}

function applyFinalPayload(payload: any) {
  const data = payload?.result || payload
  const items = (data?.recommendations || []) as Recommendation[]
  recommendations.value = items
  const summary = data?.diagnosis_hint || data?.summary || recommendationSummary(items)
  if (!activeAssistantText.value.trim()) {
    appendAssistantFinal(summary)
  } else {
    appendAssistantFinal(activeAssistantText.value)
  }
}

function newConversation() {
  conversationId.value = createConversationId()
  draft.value = ''
  recommendations.value = []
  activeAssistantText.value = ''
  messages.value = [
    {
      id: createMessageId(),
      role: 'assistant',
      content: '已开始新的 AI 分诊会话。请描述患者当前主诉、持续时间、伴随症状和危险信号。'
    }
  ]
  scrollToBottom()
}

function fillExample() {
  draft.value = '患者突发头痛伴恶心2小时，无外伤史，无发热。请判断优先分诊科室和下一步需要追问的关键问题。'
}
</script>

<style lang="scss" scoped>
.doctor-ai-page {
  min-height: 100vh;
  padding: 12px;
  background: #f5f7fb;
}
.panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
  margin-bottom: 12px;
}
.header-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
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
.chat-panel {
  min-height: 360px;
}
.messages {
  max-height: 52vh;
  overflow-y: auto;
  padding-right: 4px;
}
.message-row {
  display: flex;
  margin-bottom: 12px;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.assistant {
  justify-content: flex-start;
}
.message-bubble {
  width: fit-content;
  max-width: min(82%, 720px);
  border-radius: 12px;
  padding: 10px 12px;
  line-height: 1.7;
  word-break: break-word;
  white-space: pre-wrap;
}
.message-row.user .message-bubble {
  color: #fff;
  background: #1677ff;
}
.message-row.assistant .message-bubble {
  color: #1f2937;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}
.message-bubble.muted {
  color: #64748b;
}
.message-role {
  margin-bottom: 4px;
  font-size: 12px;
  opacity: 0.75;
}
.message-text {
  font-size: 14px;
}
.recommend-card {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e5e7eb;
}
.recommend-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}
.recommend-item:last-child {
  border-bottom: 0;
}
.dept-name {
  font-weight: 700;
  color: #1f2937;
}
.dept-reason {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}
.input-panel :deep(.van-field) {
  padding: 0;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}
.input-actions .van-button:last-child {
  min-width: 112px;
}
.footer-actions {
  padding-bottom: 16px;
}
@media (max-width: 560px) {
  .header-panel,
  .input-actions {
    flex-direction: column;
  }
  .message-bubble {
    max-width: 92%;
  }
  .input-actions .van-button {
    width: 100%;
  }
}
</style>
