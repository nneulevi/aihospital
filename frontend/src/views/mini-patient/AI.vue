<template>
  <main class="mini-page">
    <van-nav-bar title="AI 智能问诊" />

    <section class="panel">
      <h2>症状描述</h2>
      <van-field
        v-model="symptoms"
        type="textarea"
        rows="5"
        maxlength="300"
        show-word-limit
        placeholder="请描述主要不适、持续时间和伴随症状"
      />
      <div class="symptom-tags">
        <button v-for="item in commonSymptoms" :key="item" type="button" @click="appendSymptom(item)">
          {{ item }}
        </button>
      </div>
      <van-button block type="primary" :loading="loading" @click="analyzeSymptoms">开始分析</van-button>
    </section>

    <section class="panel result">
      <h2>辅助建议</h2>
      <p>{{ suggestion }}</p>
      <div v-if="departments.length" class="dept-list">
        <button v-for="dept in departments" :key="dept.deptId || dept.deptName" type="button" @click="goAppointment(dept)">
          <strong>{{ dept.deptName || '推荐科室' }}</strong>
          <span>{{ dept.reason || '根据症状匹配的优先就诊科室' }}</span>
        </button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { triage } from '@/api'

const router = useRouter()
const symptoms = ref('')
const loading = ref(false)
const suggestion = ref('请先填写症状，系统会给出科室建议并衔接挂号。')
const departments = ref<any[]>([])
const commonSymptoms = ['头痛', '发热', '咳嗽', '胸闷', '腹痛', '乏力']

const appendSymptom = (value: string) => {
  symptoms.value = symptoms.value ? `${symptoms.value}、${value}` : value
}

const analyzeSymptoms = async () => {
  const content = symptoms.value.trim()
  if (!content) {
    showToast('请先描述症状')
    return
  }
  loading.value = true
  try {
    const res = await triage({ symptoms: content })
    const data = res.data || res
    departments.value = data.recommendations || []
    const first = departments.value[0]
    suggestion.value = first
      ? `建议优先选择${first.deptName || '相关科室'}。${first.reason || ''}`
      : '已完成症状分析，建议结合医生线下问诊进一步确认。'
  } catch {
    suggestion.value = '当前可先前往全科或相关专科就诊，医生会结合检查结果进一步判断。'
    departments.value = []
  } finally {
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
  padding-bottom: 18px;
}

.panel {
  margin: 14px 16px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.panel h2 {
  margin: 0 0 12px;
  color: #1f2a37;
  font-size: 17px;
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

:deep(.van-button--primary) {
  background: #2375ff;
  border-color: #2375ff;
}

.result p {
  margin: 0;
  color: #5b6b80;
  font-size: 14px;
  line-height: 1.65;
}

.dept-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.dept-list button {
  text-align: left;
  border: 1px solid #e6ebf2;
  border-radius: 8px;
  background: #f8fbff;
  padding: 12px;
}

.dept-list strong,
.dept-list span {
  display: block;
}

.dept-list strong {
  color: #1f2a37;
  font-size: 15px;
}

.dept-list span {
  margin-top: 5px;
  color: #687789;
  font-size: 12px;
  line-height: 1.5;
}
</style>
