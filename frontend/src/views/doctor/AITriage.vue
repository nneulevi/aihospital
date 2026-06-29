<!-- src/views/doctor/AITriage.vue -->
<template>
  <div class="ai-triage-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">🧭 AI 分诊</span>
      <span class="patient-name">{{ patientName }}</span>
    </div>

    <!-- 患者摘要 -->
    <div class="patient-summary">
      <div class="summary-item">
        <span class="label">姓名</span>
        <span class="value">{{ patientName }}</span>
      </div>
      <div class="summary-item">
        <span class="label">年龄/性别</span>
        <span class="value">{{ patientInfo.age }}岁 {{ patientInfo.gender }}</span>
      </div>
      <div class="summary-item">
        <span class="label">初步诊断</span>
        <span class="value">{{ recordForm.diagnosis || '未填写' }}</span>
      </div>
      <div class="summary-item">
        <span class="label">可用结果</span>
        <span class="value">{{ totalResults }} 项</span>
      </div>
    </div>

    <!-- 检查结果摘要 -->
    <div class="results-summary" v-if="results.length > 0">
      <div class="section-title">📋 检查结果摘要</div>
      <div v-for="r in results" :key="r.id" class="result-tag">
        <van-tag :type="r.type === '检查' ? 'primary' : 'warning'" size="small">{{ r.type }}</van-tag>
        <span class="result-name">{{ r.name }}</span>
        <span class="result-brief">{{ r.brief }}</span>
      </div>
    </div>

    <!-- AI 分诊结果 -->
    <div class="triage-result" v-if="triageResult">
      <div class="section-title">
        🤖 分诊建议
        <van-tag type="success" size="small">置信度 {{ triageResult.confidence }}%</van-tag>
      </div>

      <div class="result-card">
        <div class="result-dept">
          <span class="dept-icon">{{ triageResult.icon }}</span>
          <span class="dept-name">{{ triageResult.department }}</span>
          <van-tag type="danger" size="small" v-if="triageResult.urgent">紧急</van-tag>
        </div>
        <div class="result-reason">{{ triageResult.reason }}</div>
        <div class="result-detail">{{ triageResult.detail }}</div>
      </div>

      <div class="triage-actions">
        <van-button type="primary" round block @click="acceptTriage">
          ✅ 采纳建议，转至 {{ triageResult.department }}
        </van-button>
        <van-button type="default" round block plain @click="showMoreOptions">
          📋 查看其他推荐
        </van-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading-state">
      <van-loading size="32" />
      <p>AI 正在分析检查结果...</p>
    </div>

    <!-- 无数据 -->
    <div v-else class="empty-state">
      <van-icon name="search" size="48" color="#BDC3C7" />
      <p>暂无检查结果，请先完成检查</p>
    </div>

    <!-- 其他推荐科室 -->
    <van-action-sheet v-model:show="showOtherDepts" title="其他推荐科室">
      <div class="dept-list">
        <div
            v-for="dept in otherDepts"
            :key="dept.name"
            class="dept-option"
            @click="selectOtherDept(dept)"
        >
          <div class="dept-option-left">
            <span class="dept-icon">{{ dept.icon }}</span>
            <span class="dept-name">{{ dept.name }}</span>
          </div>
          <van-tag type="primary" size="small">{{ dept.confidence }}%</van-tag>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'

const route = useRoute()
const router = useRouter()

const registerId = ref(Number(route.query.registerId) || 0)
const patientName = ref(route.query.name as string || '患者')
const loading = ref(false)
const showOtherDepts = ref(false)

// 患者信息（从草稿或接口获取）
const patientInfo = ref({
  gender: '男',
  age: 58
})

const recordForm = ref({
  diagnosis: '社区获得性肺炎（待确诊）'
})

// 模拟检查结果
const results = ref([
  { id: 1, type: '检查', name: '头颅CT平扫', brief: '右肺上叶磨玻璃结节，6mm' },
  { id: 2, type: '检验', name: '血常规', brief: 'WBC 8.5×10⁹/L，N 72%' }
])

const totalResults = computed(() => results.value.length)

// AI分诊结果
const triageResult = ref<any>(null)
const otherDepts = ref<any[]>([])

// 模拟AI分诊分析
const runAITriage = async () => {
  if (results.value.length === 0) return

  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 模拟分诊结果
    triageResult.value = {
      department: '胸外科',
      icon: '🫁',
      confidence: 92,
      urgent: false,
      reason: 'CT发现右肺上叶磨玻璃结节（6mm），需专科进一步评估',
      detail: '结节边界清晰，密度均匀，建议胸外科专科门诊就诊，进一步评估结节性质。'
    }

    otherDepts.value = [
      { name: '呼吸内科', icon: '🫁', confidence: 78 },
      { name: '肿瘤科', icon: '🎯', confidence: 45 },
      { name: '影像科', icon: '📊', confidence: 30 }
    ]

    showToast('✅ AI 分诊分析完成')
  } catch {
    showToast('分诊分析失败')
  } finally {
    loading.value = false
  }
}

// 采纳分诊
const acceptTriage = () => {
  showDialog({
    title: '确认转诊',
    message: `确认将 ${patientName.value} 转至 ${triageResult.value.department} 进一步诊疗？`,
    showCancelButton: true,
    confirmButtonText: '确认转诊'
  }).then(() => {
    showToast(`✅ 已转诊至 ${triageResult.value.department}`)
    // 将分诊结果回填到确诊页面
    const event = new CustomEvent('triage-accepted', {
      detail: {
        department: triageResult.value.department,
        reason: triageResult.value.reason
      }
    })
    window.dispatchEvent(event)
    setTimeout(() => goBack(), 500)
  }).catch(() => {})
}

const showMoreOptions = () => {
  showOtherDepts.value = true
}

const selectOtherDept = (dept: any) => {
  triageResult.value = {
    ...triageResult.value,
    department: dept.name,
    icon: dept.icon,
    confidence: dept.confidence,
    reason: `根据AI分析，建议转至${dept.name}进一步诊疗`,
    detail: '请结合临床实际情况综合判断'
  }
  showOtherDepts.value = false
  showToast(`已切换至 ${dept.name}`)
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  // 自动执行分诊
  runAITriage()
})
</script>

<style lang="scss" scoped>
.ai-triage-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 20px;
}

.nav-header {
  display: flex;
  align-items: center;
  background: white;
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

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
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .summary-item {
    .label {
      font-size: 11px;
      color: #BDC3C7;
      display: block;
    }
    .value {
      font-size: 14px;
      color: #2C3E50;
      font-weight: 500;
    }
  }
}

.results-summary {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #2C3E50;
    margin-bottom: 10px;
  }

  .result-tag {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    border-bottom: 1px solid #F5F5F5;

    &:last-child {
      border-bottom: none;
    }

    .result-name {
      font-size: 13px;
      color: #2C3E50;
    }

    .result-brief {
      font-size: 12px;
      color: #7F8C8D;
      margin-left: auto;
    }
  }
}

.triage-result {
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #2C3E50;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .result-card {
    background: linear-gradient(135deg, #E8F4FD 0%, #D6EAF8 100%);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #B3D9F7;

    .result-dept {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;

      .dept-icon {
        font-size: 28px;
      }

      .dept-name {
        font-size: 18px;
        font-weight: 600;
        color: #005B96;
      }
    }

    .result-reason {
      font-size: 14px;
      color: #2C3E50;
      font-weight: 500;
      margin-bottom: 6px;
    }

    .result-detail {
      font-size: 13px;
      color: #5C6B7A;
      line-height: 1.6;
    }
  }

  .triage-actions {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  background: white;
  border-radius: 12px;

  p {
    color: #7F8C8D;
    margin-top: 12px;
  }
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  background: white;
  border-radius: 12px;
  color: #BDC3C7;
}

.dept-list {
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;

  .dept-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #F5F5F5;
    cursor: pointer;

    &:last-child {
      border-bottom: none;
    }

    .dept-option-left {
      display: flex;
      align-items: center;
      gap: 10px;

      .dept-icon {
        font-size: 20px;
      }
      .dept-name {
        font-size: 14px;
        color: #2C3E50;
      }
    }
  }
}
</style>