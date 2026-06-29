<!-- src/views/doctor/AIDiagnosis.vue -->
<template>
  <div class="ai-diagnosis-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">AI 辅助诊断</span>
      <span class="patient-name">{{ patientName }}</span>
    </div>

    <!-- 患者摘要 -->
    <div class="patient-summary">
      <div class="summary-grid">
        <div class="summary-item">
          <span class="label">主诉</span>
          <span class="value">{{ recordForm.readme || '未填写' }}</span>
        </div>
        <div class="summary-item">
          <span class="label">现病史</span>
          <span class="value">{{ recordForm.present || '未填写' }}</span>
        </div>
        <div class="summary-item">
          <span class="label">既往史</span>
          <span class="value">{{ recordForm.history || '未填写' }}</span>
        </div>
        <div class="summary-item">
          <span class="label">体格检查</span>
          <span class="value">{{ recordForm.physique || '未填写' }}</span>
        </div>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="chat-container" ref="chatContainer">
      <div v-for="(msg, idx) in messages" :key="idx" class="message-item">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="user-msg">
          <div class="msg-content user">{{ msg.content }}</div>
          <van-icon name="manager-o" class="avatar user-avatar" />
        </div>
        <!-- AI 消息 -->
        <div v-else class="ai-msg">
          <van-icon name="robot" class="avatar ai-avatar" />
          <div class="msg-content ai">
            <div v-if="msg.diagnoses && msg.diagnoses.length">
              <div v-for="(d, i) in msg.diagnoses" :key="i" class="diagnosis-card" @click="selectDiagnosis(d)">
                <div class="diag-header">
                  <span class="diag-name">{{ d.diseaseName }}</span>
                  <van-tag :type="d.confidence > 0.8 ? 'danger' : d.confidence > 0.5 ? 'warning' : 'default'">
                    {{ (d.confidence * 100).toFixed(0) }}%
                  </van-tag>
                </div>
                <div class="diag-evidence">{{ d.evidence }}</div>
                <div class="diag-action">
                  <van-button size="small" type="primary" plain @click.stop="adoptDiagnosis(d)">采纳诊断</van-button>
                </div>
              </div>
            </div>
            <div v-else>{{ msg.content }}</div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="aiLoading" class="message-item">
        <van-icon name="robot" class="avatar ai-avatar" />
        <div class="msg-content ai loading">
          <van-loading size="16" /> AI 思考中...
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <van-button size="small" round plain @click="sendQuickMsg('分析可能疾病')">分析可能疾病</van-button>
      <van-button size="small" round plain @click="sendQuickMsg('推荐治疗方案')">推荐治疗方案</van-button>
      <van-button size="small" round plain @click="sendQuickMsg('用药建议')">用药建议</van-button>
      <van-button size="small" round plain @click="sendQuickMsg('风险评估')">风险评估</van-button>
    </div>

    <!-- 输入框 -->
    <div class="chat-input">
      <van-field
          v-model="inputMsg"
          placeholder="向AI提问，如：这个症状考虑什么疾病？"
          type="text"
          @keyup.enter="sendMessage"
      />
      <van-button type="primary" size="small" round @click="sendMessage">发送</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'

const route = useRoute()
const router = useRouter()

const registerId = ref(Number(route.query.registerId) || 0)
const patientName = ref(route.query.name as string || '患者')

const aiLoading = ref(false)
const inputMsg = ref('')
const chatContainer = ref<HTMLElement | null>(null)

// 病历数据（从草稿或接口获取）
const recordForm = reactive({
  readme: '发热、咳嗽3天，体温最高39.2℃',
  present: '3天前受凉后出现发热，伴咳嗽、咳黄色痰',
  history: '既往体健，无慢性病史',
  physique: 'T 38.8℃，P 96次/分，R 22次/分，双肺呼吸音粗，可闻及湿啰音'
})

// 对话消息
const messages = ref<any[]>([
  {
    role: 'ai',
    content: '您好，我已收到患者病历信息。请告诉我您需要什么帮助，或者点击下方快捷按钮。',
    diagnoses: []
  }
])

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 发送消息
const sendMessage = async () => {
  const content = inputMsg.value.trim()
  if (!content) return
  if (aiLoading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content })
  inputMsg.value = ''
  scrollToBottom()

  // AI 响应
  aiLoading.value = true
  try {
    // 模拟 AI 请求
    await new Promise(resolve => setTimeout(resolve, 1500))

    const aiResponse = generateAIResponse(content)
    messages.value.push({
      role: 'ai',
      content: aiResponse.content,
      diagnoses: aiResponse.diagnoses || []
    })
  } catch {
    messages.value.push({
      role: 'ai',
      content: '抱歉，AI 服务暂时不可用，请稍后再试。',
      diagnoses: []
    })
  } finally {
    aiLoading.value = false
    scrollToBottom()
  }
}

// 快捷消息
const sendQuickMsg = (text: string) => {
  inputMsg.value = text
  sendMessage()
}

// 生成 AI 响应（模拟）
const generateAIResponse = (query: string) => {
  if (query.includes('疾病') || query.includes('诊断')) {
    return {
      content: '根据患者症状和体征，我分析以下几种可能的诊断：',
      diagnoses: [
        {
          diseaseName: '社区获得性肺炎',
          confidence: 0.92,
          evidence: '发热、咳嗽、肺部湿啰音，血象升高'
        },
        {
          diseaseName: '急性支气管炎',
          confidence: 0.78,
          evidence: '咳嗽为主，无明显发热，肺部听诊正常'
        },
        {
          diseaseName: '过敏性鼻炎',
          confidence: 0.45,
          evidence: '打喷嚏、流清涕，无发热'
        }
      ]
    }
  }

  if (query.includes('治疗') || query.includes('方案')) {
    return {
      content: '根据初步诊断，建议以下治疗方案：\n1. 抗感染治疗：阿莫西林 0.5g tid\n2. 止咳化痰：氨溴索 30mg tid\n3. 退热：布洛芬 0.2g prn\n4. 休息、多饮水\n需根据检查结果调整用药。',
      diagnoses: []
    }
  }

  if (query.includes('用药') || query.includes('药品')) {
    return {
      content: '推荐用药方案：\n• 阿莫西林胶囊 0.5g × 28粒，口服，每日三次\n• 盐酸氨溴索片 30mg × 20片，口服，每日三次\n• 布洛芬缓释胶囊 0.3g × 10粒，必要时口服\n请根据患者过敏史调整。',
      diagnoses: []
    }
  }

  if (query.includes('风险') || query.includes('评估')) {
    return {
      content: '风险评估：\n✅ 生命体征基本稳定\n⚠️ 患者年龄58岁，需关注心功能\n⚠️ 建议完善心电图、心肌酶检查\n⚠️ 如体温持续>39℃超过3天，建议住院治疗',
      diagnoses: []
    }
  }

  return {
    content: '收到，请稍等... 让我结合病历信息分析一下。',
    diagnoses: []
  }
}

// 采纳诊断
const adoptDiagnosis = (d: any) => {
  // 将诊断回填到病历
  const event = new CustomEvent('adopt-diagnosis', {
    detail: { diagnosis: d.diseaseName }
  })
  window.dispatchEvent(event)
  showToast(`已采纳诊断：${d.diseaseName}`)
}

// 选择诊断查看详情
const selectDiagnosis = (d: any) => {
  showToast(`查看详情：${d.diseaseName}`)
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  // 监听采纳事件
  window.addEventListener('adopt-diagnosis', (e: any) => {
    // 可以在这里做额外处理
  })
})
</script>

<style lang="scss" scoped>
.ai-diagnosis-page {
  height: 100vh;
  background: #F5F7FA;
  display: flex;
  flex-direction: column;
}

.nav-header {
  background: white;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #EBEDF0;
  flex-shrink: 0;

  .van-icon {
    font-size: 22px;
    cursor: pointer;
    color: #2C3E50;
  }

  .title {
    flex: 1;
    margin-left: 12px;
    font-size: 17px;
    font-weight: 600;
    color: #2C3E50;
  }

  .patient-name {
    font-size: 14px;
    color: #7F8C8D;
    background: #F5F7FA;
    padding: 4px 12px;
    border-radius: 12px;
  }
}

.patient-summary {
  background: white;
  padding: 12px 16px;
  margin: 8px 12px;
  border-radius: 10px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;

    .summary-item {
      display: flex;
      flex-direction: column;

      .label {
        font-size: 11px;
        color: #BDC3C7;
      }

      .value {
        font-size: 13px;
        color: #2C3E50;
        word-break: break-all;
      }
    }
  }
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  padding-bottom: 0;
}

.message-item {
  display: flex;
  margin-bottom: 16px;
  align-items: flex-start;

  .avatar {
    font-size: 32px;
    flex-shrink: 0;
  }

  .user-avatar {
    color: #005B96;
    margin-left: 8px;
  }

  .ai-avatar {
    color: #27AE60;
    margin-right: 8px;
  }

  .msg-content {
    max-width: 78%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-line;

    &.user {
      background: #005B96;
      color: white;
      border-radius: 12px 12px 0 12px;
      order: 1;
    }

    &.ai {
      background: white;
      color: #2C3E50;
      border-radius: 12px 12px 12px 0;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);

      &.loading {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #7F8C8D;
      }
    }
  }

  &.user-msg {
    flex-direction: row-reverse;
  }
}

.diagnosis-card {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-left: 3px solid #005B96;
  cursor: pointer;

  .diag-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;

    .diag-name {
      font-weight: 600;
      color: #2C3E50;
    }
  }

  .diag-evidence {
    font-size: 13px;
    color: #7F8C8D;
    margin-bottom: 6px;
  }

  .diag-action {
    display: flex;
    gap: 8px;
  }
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  flex-shrink: 0;
  overflow-x: auto;
  background: white;
  border-top: 1px solid #EBEDF0;

  .van-button {
    flex-shrink: 0;
  }
}

.chat-input {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: white;
  border-top: 1px solid #EBEDF0;
  flex-shrink: 0;

  :deep(.van-field) {
    flex: 1;
    background: #F5F7FA;
    border-radius: 20px;

    .van-field__control {
      padding: 8px 16px;
    }
  }
}
</style>