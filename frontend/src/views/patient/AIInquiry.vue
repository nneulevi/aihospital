<!-- src/views/patient/AIInquiry.vue -->
<template>
  <div class="ai-inquiry">
    <van-nav-bar title="智能问诊" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 未分析状态 -->
    <div v-if="!analyzed" class="input-area">
      <div class="greeting">
        <span class="greeting-icon">✨</span>
        <span class="greeting-text">请告诉我您的主要不适</span>
      </div>

      <div class="symptom-input-wrapper">
        <van-field
            v-model="symptoms"
            type="textarea"
            placeholder="例如：头痛、发热、胸闷、咳嗽..."
            rows="3"
            autosize
            class="symptom-input"
        />
        <van-icon name="mic" class="voice-icon" @click="startVoiceInput" />
      </div>

      <div class="symptom-tags-section">
        <div class="section-title">常见症状</div>
        <div class="symptom-tags">
          <van-tag
              v-for="tag in commonSymptoms"
              :key="tag"
              :type="selectedSymptoms.includes(tag) ? 'primary' : 'default'"
              @click="toggleSymptom(tag)"
          >
            {{ tag }}
          </van-tag>
        </div>
      </div>

      <van-button
          type="primary"
          block
          round
          :loading="analyzing"
          :disabled="!hasSymptoms"
          @click="startAnalysis"
          class="analyze-btn"
      >
        开始智能分析
      </van-button>
    </div>

    <!-- 分析中状态 -->
    <div v-else-if="analyzing" class="loading-area">
      <van-loading type="spinner" size="48px" color="#4CAF50" />
      <div class="loading-text">🤖 AI正在分析您的症状...</div>
      <van-progress :percentage="analysisProgress" stroke-width="4" color="#4CAF50" />
      <div class="loading-hint">{{ loadingHint }}</div>
    </div>

    <!-- 结果展示状态 -->
    <div v-else class="result-area">
      <div class="symptom-review" @click="resetAnalysis">
        <span class="review-label">您的症状：</span>
        <span class="review-content">{{ inputSymptoms }}</span>
        <van-icon name="edit" class="review-edit" />
      </div>

      <div class="ai-suggestion-card">
        <div class="card-header">
          <span class="card-icon">🤖</span>
          <span class="card-title">AI 分析建议</span>
          <van-tag type="primary" size="small">智能推荐</van-tag>
        </div>
        <div class="card-content">
          <div class="suggestion-text">{{ aiSuggestion }}</div>
        </div>
      </div>

      <div class="recommend-section">
        <div class="section-title">
          <span>🏥 推荐科室</span>
          <span class="section-hint">根据您的症状智能匹配</span>
        </div>
        <div class="dept-list">
          <div
              v-for="dept in recommendedDepts"
              :key="dept.id"
              class="dept-item"
              @click="selectDept(dept)"
          >
            <div class="dept-info">
              <div class="dept-name">{{ dept.name }}</div>
              <div class="dept-match">匹配度 {{ dept.matchRate }}%</div>
            </div>
            <div class="dept-progress">
              <van-progress :percentage="dept.matchRate" stroke-width="6" color="#4CAF50" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="recommendedDoctors.length > 0" class="recommend-section">
        <div class="section-title">
          <span>👨‍⚕️ 推荐医生</span>
          <span class="section-hint">这些医生擅长处理您的症状</span>
        </div>
        <div class="doctor-list">
          <div
              v-for="doc in recommendedDoctors"
              :key="doc.id"
              class="doctor-card"
          >
            <div class="doctor-avatar">
              <van-icon name="doctor-o" size="40" />
            </div>
            <div class="doctor-info">
              <div class="doctor-name">{{ doc.name }}</div>
              <div class="doctor-title">{{ doc.title }}</div>
              <div class="doctor-skill">擅长：{{ doc.skill }}</div>
              <div class="doctor-slots">
                <span class="slot-badge">剩余号源</span>
                <span class="slot-count">上午 {{ doc.morningSlots }}个</span>
                <span class="slot-count">下午 {{ doc.afternoonSlots }}个</span>
              </div>
            </div>
            <van-button
                size="small"
                type="primary"
                round
                @click="goToRegister(doc.id, doc.deptId)"
            >
              去挂号
            </van-button>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-note">
      ⚠️ 本问诊仅提供参考，不构成医疗诊断。如有紧急情况请立即就医。
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { triage } from '@/api'
import type { ConsultationResponseVO, DeptRecommendation } from '@/api/model'

const router = useRouter()

const symptoms = ref('')
const selectedSymptoms = ref<string[]>([])
const analyzing = ref(false)
const analyzed = ref(false)
const analysisProgress = ref(0)
const loadingHint = ref('正在理解您的症状...')
const aiSuggestion = ref('')
const recommendedDepts = ref<{ id: number; name: string; matchRate: number }[]>([])
const recommendedDoctors = ref<any[]>([])

const commonSymptoms = ['头痛', '咳嗽', '胃痛', '发烧', '乏力', '皮疹', '胸闷', '恶心', '腹泻', '关节痛']

const hasSymptoms = computed(() => {
  return symptoms.value.trim() !== '' || selectedSymptoms.value.length > 0
})

const inputSymptoms = computed(() => {
  if (symptoms.value.trim()) return symptoms.value
  return selectedSymptoms.value.join('、')
})

const toggleSymptom = (tag: string) => {
  const index = selectedSymptoms.value.indexOf(tag)
  if (index > -1) {
    selectedSymptoms.value.splice(index, 1)
  } else {
    selectedSymptoms.value.push(tag)
  }
}

const startVoiceInput = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.start()
    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript
      symptoms.value = text
    }
    recognition.onerror = () => {
      showToast('语音识别失败，请手动输入')
    }
  } else {
    showToast('当前浏览器不支持语音输入')
  }
}

const startAnalysis = async () => {
  const content = symptoms.value.trim() || selectedSymptoms.value.join('、')
  if (!content) {
    showToast('请描述您的症状')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0

  const hints = ['正在理解您的症状...', '分析可能的病因...', '匹配最佳科室...', '推荐合适的医生...']
  let step = 0

  const timer = setInterval(() => {
    step++
    analysisProgress.value = step * 25
    loadingHint.value = hints[step - 1] || '分析完成'
    if (step >= 4) {
      clearInterval(timer)
      loadRecommendations(content)
    }
  }, 800)
}

const loadRecommendations = async (content: string) => {
  try {
    const res = await triage({ symptoms: content }) as ConsultationResponseVO
    aiSuggestion.value = `根据您描述的症状，建议优先考虑「${res.recommendations?.[0]?.deptName || '相关科室'}」就诊。${res.recommendations?.[0]?.reason || ''}`

    recommendedDepts.value = (res.recommendations || []).map((r: DeptRecommendation) => ({
      id: r.deptId || 0,
      name: r.deptName || '',
      matchRate: Math.round((r.confidence || 0) * 100)
    }))

    // 后端暂无推荐医生接口，保留模拟
    recommendedDoctors.value = [
      {
        id: 101,
        deptId: res.recommendations?.[0]?.deptId || 2,
        name: '张敏',
        title: '主任医师',
        skill: '呼吸道感染、慢性支气管炎、哮喘',
        morningSlots: 3,
        afternoonSlots: 5
      },
      {
        id: 102,
        deptId: res.recommendations?.[0]?.deptId || 2,
        name: '李华',
        title: '副主任医师',
        skill: '肺炎、慢性阻塞性肺病、咳嗽',
        morningSlots: 5,
        afternoonSlots: 2
      }
    ]

    analyzing.value = false
    analyzed.value = true
  } catch (error) {
    showToast('AI分析失败，请重试')
    analyzing.value = false
  }
}

const selectDept = (dept: { id: number; name: string }) => {
  router.push({
    name: 'Appointment',
    query: { deptId: String(dept.id), deptName: dept.name }
  })
}

const goToRegister = (doctorId: number, deptId?: number) => {
  router.push({
    name: 'Appointment',
    query: {
      doctorId: String(doctorId),
      deptId: deptId ? String(deptId) : undefined
    }
  })
}

const resetAnalysis = () => {
  analyzed.value = false
  symptoms.value = ''
  selectedSymptoms.value = []
  recommendedDepts.value = []
  recommendedDoctors.value = []
  analysisProgress.value = 0
}
</script>

<style lang="scss" scoped>
.ai-inquiry {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 16px;
  padding-bottom: 80px;
}

.input-area .greeting {
  text-align: center;
  margin: 32px 0;
}
.input-area .greeting .greeting-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}
.input-area .greeting .greeting-text {
  font-size: 20px;
  font-weight: 500;
  color: #1A1A2E;
}
.symptom-input-wrapper {
  position: relative;
}
.symptom-input-wrapper .symptom-input {
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
}
.symptom-input-wrapper .voice-icon {
  position: absolute;
  right: 16px;
  bottom: 16px;
  font-size: 24px;
  color: #4CAF50;
}
.symptom-tags-section {
  margin: 24px 0;
}
.symptom-tags-section .section-title {
  font-size: 14px;
  color: #6B6B7E;
  margin-bottom: 8px;
}
.symptom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.symptom-tags .van-tag {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 9999px;
  background: white;
}
.symptom-tags .van-tag--primary {
  background: #4CAF50;
  color: white;
}
.analyze-btn {
  margin-top: 24px;
  height: 48px;
  font-size: 16px;
  background: #4CAF50;
  border-color: #4CAF50;
}

.loading-area {
  text-align: center;
  padding: 40px 16px;
}
.loading-area .loading-text {
  font-size: 18px;
  color: #1A1A2E;
  margin: 20px 0 16px;
}
.loading-area .loading-hint {
  font-size: 14px;
  color: #6B6B7E;
  margin-top: 16px;
}

.result-area .symptom-review {
  background: #F0F4F0;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.result-area .symptom-review .review-label {
  color: #6B6B7E;
}
.result-area .symptom-review .review-content {
  flex: 1;
  color: #1A1A2E;
  font-weight: 500;
}
.result-area .symptom-review .review-edit {
  color: #4CAF50;
  cursor: pointer;
}

.ai-suggestion-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.08) 0%, rgba(76, 175, 80, 0.03) 100%);
  border-left: 4px solid #4CAF50;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}
.ai-suggestion-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-suggestion-card .card-header .card-icon {
  font-size: 20px;
}
.ai-suggestion-card .card-header .card-title {
  font-size: 16px;
  font-weight: 500;
  color: #4CAF50;
}
.ai-suggestion-card .suggestion-text {
  font-size: 14px;
  line-height: 1.6;
  color: #1A1A2E;
}

.recommend-section {
  margin-bottom: 20px;
}
.recommend-section .section-title {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 500;
  color: #1A1A2E;
}
.recommend-section .section-title .section-hint {
  font-size: 12px;
  font-weight: 400;
  color: #6B6B7E;
}
.dept-list .dept-item {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}
.dept-list .dept-item:active {
  background: #F0F4F0;
}
.dept-list .dept-item .dept-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.dept-list .dept-item .dept-info .dept-name {
  font-size: 16px;
  font-weight: 500;
}
.dept-list .dept-item .dept-info .dept-match {
  font-size: 14px;
  color: #4CAF50;
}

.doctor-list .doctor-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
}
.doctor-list .doctor-card .doctor-avatar {
  width: 60px;
  height: 60px;
  background: #F0F4F0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4CAF50;
  flex-shrink: 0;
}
.doctor-list .doctor-card .doctor-info {
  flex: 1;
}
.doctor-list .doctor-card .doctor-info .doctor-name {
  font-size: 16px;
  font-weight: 500;
  color: #1A1A2E;
}
.doctor-list .doctor-card .doctor-info .doctor-title {
  font-size: 12px;
  color: #4CAF50;
  margin: 4px 0;
}
.doctor-list .doctor-card .doctor-info .doctor-skill {
  font-size: 12px;
  color: #6B6B7E;
  margin-bottom: 4px;
}
.doctor-list .doctor-card .doctor-info .doctor-slots {
  display: flex;
  gap: 8px;
}
.doctor-list .doctor-card .doctor-info .doctor-slots .slot-badge {
  font-size: 12px;
  color: #6B6B7E;
}
.doctor-list .doctor-card .doctor-info .doctor-slots .slot-count {
  font-size: 12px;
  color: #4CAF50;
}

.footer-note {
  position: fixed;
  bottom: 16px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  color: #C4C4D6;
}
</style>