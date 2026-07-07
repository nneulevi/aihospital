<!-- src/views/patient/AIInquiry.vue -->
<template>
  <div class="ai-inquiry">
    <van-nav-bar title="智能问诊" fixed placeholder />

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
      <div v-if="aiStreamText" class="stream-preview">{{ aiStreamText }}</div>
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
          <van-tag type="primary">智能推荐</van-tag>
        </div>
        <div class="card-content">
          <div class="suggestion-text">{{ aiSuggestion }}</div>
          <ul v-if="recommendedDepts.length" class="reason-list">
            <li v-for="dept in recommendedDepts" :key="`reason-${dept.id}`">
              <strong>{{ dept.name }}</strong>
              <span>{{ dept.reason || '根据症状与就诊需求匹配' }}</span>
            </li>
          </ul>
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
import { getDoctors, triage, triageStream } from '@/api'
import type { ConsultationResponseVO, DoctorListVO } from '@/api/model'
import dayjs from 'dayjs'

const router = useRouter()

const symptoms = ref('')
const selectedSymptoms = ref<string[]>([])
const analyzing = ref(false)
const analyzed = ref(false)
const analysisProgress = ref(0)
const loadingHint = ref('正在理解您的症状...')
const aiStreamText = ref('')
const streamedConclusion = ref('')
const aiSuggestion = ref('')
const recommendedDepts = ref<any[]>([])
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
  analyzed.value = true
  analysisProgress.value = 0
  aiStreamText.value = ''
  streamedConclusion.value = ''
  loadingHint.value = '正在建立 AI 流式连接...'
  await loadRecommendations(content)
}

const loadRecommendations = async (content: string) => {
  let success = false
  try {
    let finalPayload: any = null
    await triageStream(
      { symptoms: content },
      {
        onEvent: ({ event, data }) => {
          if (event === 'memory_loaded') {
            analysisProgress.value = 20
          } else if (event === 'rag_retrieved') {
            analysisProgress.value = 55
          } else if (event === 'llm_generating') {
            analysisProgress.value = 82
          } else if (event === 'delta') {
            aiStreamText.value += data?.text || ''
            streamedConclusion.value += data?.text || ''
          }
          loadingHint.value = data?.message || loadingHint.value
        },
        onFinal: (data) => {
          finalPayload = data?.data || data
        },
        onError: (data) => {
          throw new Error(data?.message || 'AI分析失败')
        },
      },
    )

    if (!finalPayload) {
      throw new Error('AI流式响应缺少最终结果')
    }

    await applyRecommendations(finalPayload)
    success = true
  } catch {
    try {
      loadingHint.value = '流式连接不可用，正在切换普通分析...'
      const res = await triage({ symptoms: content })
      await applyRecommendations(res.data || res)
      success = true
    } catch {
      showToast('AI分析失败，请重试')
    }
  } finally {
    analysisProgress.value = 100
    analyzing.value = false
    analyzed.value = success
  }
}

const applyRecommendations = async (data: ConsultationResponseVO) => {
  const recommendations = data?.recommendations || []
  const primary = recommendations[0]
  const diagnosisHint = (data as any)?.diagnosisHint || ''
  const professionalText = streamedConclusion.value.trim()
  aiSuggestion.value = professionalText || diagnosisHint || `根据您描述的症状，建议优先考虑「${primary?.deptName || '相关科室'}」就诊。${primary?.reason || '请结合持续时间、伴随症状和既往病史进一步就医评估。'}`

  recommendedDepts.value = recommendations.map((r: any) => ({
    id: r.deptId,
    name: r.deptName,
    matchRate: Math.round((r.confidence || 0) * 100),
    reason: r.reason || '',
  }))

  recommendedDoctors.value = await loadAvailableDoctors(recommendations)
  if (!recommendedDoctors.value.length) {
    showToast('推荐科室当前暂无可预约号源，可进入挂号页查看其他日期')
  }
}

const loadAvailableDoctors = async (recommendations: any[]) => {
  const result: any[] = []
  const candidateNoons = currentNoonFirst()
  for (const recommendation of recommendations.slice(0, 3)) {
    if (!recommendation?.deptId) continue
    for (let dayOffset = 0; dayOffset < 7 && result.length < 4; dayOffset += 1) {
      const visitDate = dayjs().add(dayOffset, 'day').format('YYYY-MM-DD')
      for (const noon of candidateNoons) {
        if (result.length >= 4) break
        const res = await getDoctors({
          query: {
            deptId: recommendation.deptId,
            visitDate,
            noon,
            pageNum: 1,
            pageSize: 10,
          },
        }).catch(() => undefined)
        const doctors = resolveRecords<DoctorListVO>(res)
          .filter((doctor) => (doctor.remainingQuota || 0) > 0)
        doctors.forEach((doctor) => {
          if (result.some((item) => item.id === doctor.doctorId && item.visitDate === visitDate && item.noon === noon)) {
            return
          }
          result.push({
            id: doctor.doctorId,
            deptId: recommendation.deptId,
            deptName: recommendation.deptName,
            name: doctor.doctorName || '医生',
            title: doctor.titleLevel || '医师',
            skill: doctor.specialty || `${doctor.deptName || recommendation.deptName || '相关科室'}门诊`,
            morningSlots: noon === 'MORNING' ? doctor.remainingQuota || 0 : 0,
            afternoonSlots: noon === 'AFTERNOON' ? doctor.remainingQuota || 0 : 0,
            visitDate,
            noon,
          })
        })
      }
    }
  }
  return result
}

const resolveRecords = <T,>(res: any): T[] => {
  return res?.data?.records || res?.records || []
}

const currentNoonFirst = () => {
  const hour = new Date().getHours()
  return hour < 12 ? ['MORNING', 'AFTERNOON'] : ['AFTERNOON', 'MORNING']
}

const selectDept = (dept: any) => {
  router.push({
    name: 'Appointment',
    query: { deptId: String(dept.id), deptName: dept.name }
  })
}

const goToRegister = (doctorId: number, deptId?: number) => {
  const doc = recommendedDoctors.value.find((item) => item.id === doctorId)
  router.push({
    name: 'Appointment',
    query: {
      doctorId: String(doctorId),
      deptId: deptId ? String(deptId) : undefined,
      deptName: doc?.deptName,
      visitDate: doc?.visitDate,
      noon: doc?.noon,
    }
  })
}

const resetAnalysis = () => {
  analyzed.value = false
  symptoms.value = ''
  selectedSymptoms.value = []
  recommendedDepts.value = []
  recommendedDoctors.value = []
  streamedConclusion.value = ''
  aiStreamText.value = ''
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
  color: #1F2937;
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
  color: #64748B;
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
  color: #1F2937;
  margin: 20px 0 16px;
}
.loading-area .loading-hint {
  font-size: 14px;
  color: #64748B;
  margin-top: 16px;
}
.loading-area .stream-preview {
  margin-top: 14px;
  padding: 12px 14px;
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid #D8EEDB;
  border-radius: 8px;
  background: #F7FBF7;
  color: #1F2937;
  font-size: 13px;
  line-height: 1.7;
  text-align: left;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-area .symptom-review {
  background: #F0F7F1;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.result-area .symptom-review .review-label {
  color: #64748B;
}
.result-area .symptom-review .review-content {
  flex: 1;
  color: #1F2937;
  font-weight: 500;
}
.result-area .symptom-review .review-edit {
  color: #4CAF50;
  cursor: pointer;
}

.ai-suggestion-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.10) 0%, rgba(76, 175, 80, 0.04) 100%);
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
  color: #1F2937;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-suggestion-card .reason-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: #334155;
  font-size: 13px;
  line-height: 1.7;
}
.ai-suggestion-card .reason-list strong {
  margin-right: 6px;
  color: #1F2937;
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
  color: #1F2937;
}
.recommend-section .section-title .section-hint {
  font-size: 12px;
  font-weight: 400;
  color: #64748B;
}
.dept-list .dept-item {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}
.dept-list .dept-item:active {
  background: #F0F7F1;
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
  background: #F0F7F1;
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
  color: #1F2937;
}
.doctor-list .doctor-card .doctor-info .doctor-title {
  font-size: 12px;
  color: #4CAF50;
  margin: 4px 0;
}
.doctor-list .doctor-card .doctor-info .doctor-skill {
  font-size: 12px;
  color: #64748B;
  margin-bottom: 4px;
}
.doctor-list .doctor-card .doctor-info .doctor-slots {
  display: flex;
  gap: 8px;
}
.doctor-list .doctor-card .doctor-info .doctor-slots .slot-badge {
  font-size: 12px;
  color: #64748B;
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
  color: #94A3B8;
}
</style>
