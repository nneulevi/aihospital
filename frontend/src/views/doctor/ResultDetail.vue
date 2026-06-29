<!-- src/views/doctor/ResultDetail.vue -->
<template>
  <div class="result-detail-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">{{ resultType }}</span>
      <van-tag :type="resultData.state === 'DONE' ? 'success' : 'warning'">
        {{ resultData.state === 'DONE' ? '已出结果' : '待执行' }}
      </van-tag>
    </div>

    <!-- 基本信息 -->
    <div class="info-card">
      <div class="info-row">
        <span class="label">患者姓名</span>
        <span class="value">{{ patientName }}</span>
      </div>
      <div class="info-row">
        <span class="label">项目名称</span>
        <span class="value">{{ resultData.name }}</span>
      </div>
      <div class="info-row">
        <span class="label">检查部位</span>
        <span class="value">{{ resultData.position || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="label">申请时间</span>
        <span class="value">{{ resultData.applyTime || '2026-06-24 09:30' }}</span>
      </div>
      <div class="info-row">
        <span class="label">报告时间</span>
        <span class="value">{{ resultData.reportTime || '2026-06-24 14:20' }}</span>
      </div>
    </div>

    <!-- 结果内容 -->
    <div class="result-card" v-if="resultData.state === 'DONE'">
      <div class="card-title">📋 检查所见</div>
      <div class="result-content">{{ resultData.content || '未见明显异常' }}</div>

      <div class="card-title" style="margin-top:16px;">📝 诊断印象</div>
      <div class="result-content">{{ resultData.impression || '待分析' }}</div>
    </div>

    <div v-else class="empty-result">
      <van-icon name="clock" size="48" color="#BDC3C7" />
      <p>结果尚未出，请稍后刷新</p>
    </div>

    <!-- AI 分析报告 -->
    <div class="ai-report-card" v-if="resultData.state === 'DONE'">
      <div class="ai-header">
        <span class="ai-title">🤖 AI 智能分析</span>
        <van-tag type="primary" size="small">已分析</van-tag>
      </div>

      <div class="ai-section">
        <div class="ai-label">📊 指标解读</div>
        <div class="ai-text">{{ aiReport.interpretation || '分析中...' }}</div>
      </div>

      <div class="ai-section" v-if="aiReport.abnormalities && aiReport.abnormalities.length">
        <div class="ai-label">⚠️ 异常提示</div>
        <div v-for="(item, idx) in aiReport.abnormalities" :key="idx" class="abnormal-item">
          <span class="bullet">•</span>
          <span>{{ item }}</span>
        </div>
      </div>

      <div class="ai-section">
        <div class="ai-label">💡 建议</div>
        <div class="ai-text">{{ aiReport.suggestion || '建议结合临床表现综合判断' }}</div>
      </div>

      <div class="ai-section">
        <div class="ai-label">📈 置信度</div>
        <van-progress :percentage="aiReport.confidence || 85" stroke-width="8" color="#27AE60" />
        <span class="confidence-label">{{ aiReport.confidence || 85 }}%</span>
      </div>

      <div class="ai-actions">
        <van-button size="small" type="primary" plain @click="acceptAI">采纳分析</van-button>
        <van-button size="small" type="default" plain @click="showToast('已反馈给AI团队')">反馈</van-button>
      </div>
    </div>

    <div class="action-bar">
      <van-button type="primary" block round @click="goBack">返回</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'

const route = useRoute()
const router = useRouter()

const resultType = ref('检查报告')
const patientName = ref('张建国')

const resultData = ref({
  id: 1,
  name: '头颅CT平扫',
  position: '头部',
  state: 'DONE', // DONE / PENDING
  content: '右肺上叶见磨玻璃结节，直径约 6mm，边界清晰，密度均匀。余肺野清晰，未见明确占位性病变。纵隔居中，未见肿大淋巴结。',
  impression: '右肺上叶磨玻璃结节，考虑良性病变可能',
  applyTime: '2026-06-24 09:30',
  reportTime: '2026-06-24 14:20'
})

const aiReport = ref({
  interpretation: '右肺上叶磨玻璃结节（GGO），直径约6mm，边界清晰，密度均匀。符合良性结节（如炎性假瘤、错构瘤）的影像学特征。',
  abnormalities: [
    '右肺上叶磨玻璃结节，直径6mm',
    '建议6个月后复查对比'
  ],
  suggestion: '1. 建议6个月后复查胸部CT平扫\n2. 若出现咳嗽加重、胸痛或咯血，及时就诊\n3. 目前无需特殊处理，保持随访即可',
  confidence: 92
})

const goBack = () => {
  router.back()
}

const acceptAI = () => {
  showToast('已采纳AI分析结论')
}

onMounted(() => {
  // 根据路由参数加载不同数据
  const type = route.params.type as string
  const id = Number(route.params.id)

  if (type === 'check') {
    resultType.value = '🔬 检查报告'
  } else if (type === 'inspection') {
    resultType.value = '🧪 检验报告'
  } else if (type === 'disposal') {
    resultType.value = '🩹 处置记录'
  }
})
</script>

<style lang="scss" scoped>
.result-detail-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 80px;
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
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #F5F5F5;

    &:last-child {
      border-bottom: none;
    }

    .label {
      color: #7F8C8D;
      font-size: 13px;
    }

    .value {
      color: #2C3E50;
      font-size: 13px;
      font-weight: 500;
    }
  }
}

.result-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: #2C3E50;
    margin-bottom: 8px;
  }

  .result-content {
    font-size: 14px;
    color: #2C3E50;
    line-height: 1.8;
    background: #F8FAFC;
    padding: 12px;
    border-radius: 8px;
  }
}

.empty-result {
  text-align: center;
  padding: 40px 0;
  background: white;
  border-radius: 12px;

  p {
    color: #BDC3C7;
    margin-top: 12px;
  }
}

.ai-report-card {
  background: linear-gradient(135deg, #F0F7FF 0%, #E8F4FD 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #B3D9F7;

  .ai-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .ai-title {
      font-size: 16px;
      font-weight: 600;
      color: #005B96;
    }
  }

  .ai-section {
    margin-bottom: 12px;

    .ai-label {
      font-size: 13px;
      font-weight: 500;
      color: #2C3E50;
      margin-bottom: 4px;
    }

    .ai-text {
      font-size: 14px;
      color: #2C3E50;
      line-height: 1.8;
      white-space: pre-line;
    }

    .abnormal-item {
      font-size: 14px;
      color: #E74C3C;
      padding: 4px 0;

      .bullet {
        margin-right: 8px;
      }
    }

    .confidence-label {
      font-size: 13px;
      color: #27AE60;
      font-weight: 600;
      display: block;
      text-align: right;
      margin-top: 4px;
    }
  }

  .ai-actions {
    display: flex;
    gap: 10px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(0, 91, 150, 0.15);
  }
}

.action-bar {
  position: fixed;
  bottom: 12px;
  left: 12px;
  right: 12px;

  .van-button {
    height: 44px;
  }
}
</style>