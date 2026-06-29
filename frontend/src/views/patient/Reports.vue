<!-- src/views/patient/Reports.vue -->
<template>
  <div class="reports-page">
    <van-nav-bar title="报告查询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-number">{{ reports.length }}</span>
        <span class="stat-label">总报告</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-number">{{ unreadCount }}</span>
        <span class="stat-label">未读</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-number">{{ abnormalCount }}</span>
        <span class="stat-label">异常指标</span>
      </div>
    </div>

    <!-- Tab 切换 -->
    <van-tabs v-model:active="activeTab" class="report-tabs">
      <van-tab title="全部" name="all" />
      <van-tab title="检验报告" name="INSPECTION" />
      <van-tab title="检查报告" name="CHECK" />
      <van-tab title="影像报告" name="IMAGE" />
    </van-tabs>

    <!-- 报告列表 -->
    <div class="report-list">
      <div
          v-for="report in filteredReports"
          :key="report.id"
          class="report-card"
          :class="{ unread: !report.isViewed }"
          @click="viewReport(report)"
      >
        <div class="report-left">
          <div class="report-icon" :style="{ background: getReportColor(report.requestType) }">
            <van-icon :name="getReportIcon(report.requestType)" size="24" color="white" />
          </div>
        </div>
        <div class="report-info">
          <div class="report-top">
            <span class="report-title">{{ report.reportTitle || report.requestTypeName }}</span>
            <van-tag :type="report.isViewed ? 'default' : 'danger'" size="mini">
              {{ report.isViewed ? '已读' : '未读' }}
            </van-tag>
          </div>
          <div class="report-meta">
            <span>{{ report.requestTypeName }}</span>
            <span>{{ report.deptName || '--' }}</span>
            <span>{{ formatDate(report.reportTime) }}</span>
          </div>
          <div class="report-status" v-if="report.status">
            <van-tag :type="getStatusType(report.status)" size="small">
              {{ getStatusText(report.status) }}
            </van-tag>
            <span v-if="report.abnormalCount" class="abnormal-tag">
              ⚠️ {{ report.abnormalCount }} 项异常
            </span>
          </div>
        </div>
        <van-icon name="arrow" class="report-arrow" />
      </div>

      <div v-if="filteredReports.length === 0" class="empty-state">
        <van-icon name="file-o" size="64" color="#C4C4D6" />
        <p>暂无报告</p>
        <span class="empty-desc">检查/检验完成后，报告将在此显示</span>
      </div>
    </div>

    <!-- ===== 报告详情弹窗 ===== -->
    <van-popup
        v-model:show="showDetail"
        position="bottom"
        :style="{ height: '85%', borderRadius: '16px 16px 0 0' }"
        closeable
        close-icon-position="top-right"
    >
      <div class="report-detail" v-if="currentReport">
        <!-- 头部 -->
        <div class="detail-header">
          <div class="detail-title">{{ currentReport.reportTitle || currentReport.requestTypeName }}</div>
          <div class="detail-subtitle">
            <span>{{ currentReport.requestTypeName }}</span>
            <span>{{ formatDate(currentReport.reportTime) }}</span>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="section-title">基本信息</div>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">报告编号</span>
              <span class="value">{{ currentReport.reportNo || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">患者姓名</span>
              <span class="value">{{ currentReport.patientName || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">申请科室</span>
              <span class="value">{{ currentReport.deptName || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">报告时间</span>
              <span class="value">{{ formatDateTime(currentReport.reportTime) }}</span>
            </div>
          </div>
        </div>

        <!-- 报告内容 -->
        <div class="detail-section">
          <div class="section-title">报告内容</div>
          <div class="report-content">
            <div v-if="currentReport.reportText" class="content-text">
              {{ currentReport.reportText }}
            </div>
            <div v-else class="content-placeholder">
              报告内容加载中...
            </div>
          </div>
        </div>

        <!-- 异常指标 -->
        <div class="detail-section" v-if="currentReport.abnormalItems?.length">
          <div class="section-title">异常指标</div>
          <div class="abnormal-list">
            <div
                v-for="item in currentReport.abnormalItems"
                :key="item.name"
                class="abnormal-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value">{{ item.value }}</span>
              <span class="item-range">参考范围：{{ item.referenceRange }}</span>
              <van-tag type="danger" size="mini">异常</van-tag>
            </div>
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="detail-actions">
          <van-button plain round size="small" @click="markAsRead(currentReport)">
            {{ currentReport.isViewed ? '已读' : '标记已读' }}
          </van-button>
          <van-button type="primary" round size="small" @click="downloadReport(currentReport)">
            <van-icon name="down" /> 下载报告
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

// ============ 状态 ============
const activeTab = ref('all')
const reports = ref<any[]>([])
const showDetail = ref(false)
const currentReport = ref<any>(null)

// ============ 模拟数据 ============

const mockReports = [
  // 检验报告
  {
    id: 1,
    reportNo: 'JY202606250001',
    reportTitle: '血常规检验报告',
    requestType: 'INSPECTION',
    requestTypeName: '检验报告',
    deptName: '呼吸内科',
    patientName: '张明',
    reportTime: '2026-06-25 10:30:00',
    reportText: '白细胞计数: 7.8×10^9/L (正常范围: 4.0-10.0)\n红细胞计数: 4.5×10^12/L (正常范围: 4.0-5.5)\n血红蛋白: 145g/L (正常范围: 120-160)\n血小板计数: 220×10^9/L (正常范围: 100-300)\n中性粒细胞: 65% (正常范围: 50-70)\n淋巴细胞: 28% (正常范围: 20-40)',
    isViewed: false,
    status: 'COMPLETED',
    statusText: '已完成',
    abnormalCount: 0,
    abnormalItems: [],
    reportFileUrl: '/reports/1.pdf'
  },
  {
    id: 2,
    reportNo: 'JY202606250002',
    reportTitle: '肝功能检验报告',
    requestType: 'INSPECTION',
    requestTypeName: '检验报告',
    deptName: '消化内科',
    patientName: '张明',
    reportTime: '2026-06-24 15:20:00',
    reportText: '总蛋白: 72g/L (正常范围: 60-80)\n白蛋白: 42g/L (正常范围: 35-55)\n总胆红素: 18μmol/L (正常范围: 5-21)\n直接胆红素: 6μmol/L (正常范围: 0-8)\nALT: 45U/L (正常范围: 0-40) ↑\nAST: 38U/L (正常范围: 0-40)\nγ-GT: 52U/L (正常范围: 10-50) ↑',
    isViewed: true,
    status: 'COMPLETED',
    statusText: '已完成',
    abnormalCount: 2,
    abnormalItems: [
      { name: 'ALT', value: '45U/L', referenceRange: '0-40' },
      { name: 'γ-GT', value: '52U/L', referenceRange: '10-50' }
    ],
    reportFileUrl: '/reports/2.pdf'
  },
  // 检查报告
  {
    id: 3,
    reportNo: 'JC202606230001',
    reportTitle: '胸部CT平扫报告',
    requestType: 'CHECK',
    requestTypeName: '检查报告',
    deptName: '呼吸内科',
    patientName: '张明',
    reportTime: '2026-06-23 09:00:00',
    reportText: '检查所见：\n双侧胸廓对称，纵隔居中。双肺纹理清晰，未见明显异常密度影。气管及主要支气管通畅。纵隔内未见明显肿大淋巴结。心脏形态大小正常。双侧胸腔未见积液。\n\n诊断意见：\n胸部CT平扫未见明显异常。',
    isViewed: false,
    status: 'COMPLETED',
    statusText: '已完成',
    abnormalCount: 0,
    abnormalItems: [],
    reportFileUrl: '/reports/3.pdf'
  },
  {
    id: 4,
    reportNo: 'JC202606220001',
    reportTitle: '腹部彩超报告',
    requestType: 'CHECK',
    requestTypeName: '检查报告',
    deptName: '消化内科',
    patientName: '张明',
    reportTime: '2026-06-22 14:30:00',
    reportText: '检查所见：\n肝脏：大小形态正常，包膜光滑，实质回声均匀，肝内血管走行清晰。\n胆囊：大小正常，壁光滑，腔内未见明显异常回声。\n胰腺：大小形态正常，实质回声均匀。\n脾脏：大小正常。\n双肾：大小形态正常，实质回声均匀，集合系统未见分离。\n\n诊断意见：\n腹部彩超未见明显异常。',
    isViewed: true,
    status: 'COMPLETED',
    statusText: '已完成',
    abnormalCount: 0,
    abnormalItems: [],
    reportFileUrl: '/reports/4.pdf'
  },
  // 影像报告（待完善）
  {
    id: 5,
    reportNo: 'YX202606210001',
    reportTitle: 'X光影像报告',
    requestType: 'IMAGE',
    requestTypeName: '影像报告',
    deptName: '骨科',
    patientName: '张明',
    reportTime: '2026-06-21 11:00:00',
    reportText: '影像所见：\n右腕关节正侧位片示：骨骼形态结构正常，关节间隙清晰，未见明显骨折征象。\n\n诊断意见：\n右腕关节X光未见明显骨折。',
    isViewed: true,
    status: 'COMPLETED',
    statusText: '已完成',
    abnormalCount: 0,
    abnormalItems: [],
    reportFileUrl: '/reports/5.pdf'
  }
]

// ============ 计算属性 ============

const unreadCount = computed(() => {
  return reports.value.filter(r => !r.isViewed).length
})

const abnormalCount = computed(() => {
  return reports.value.reduce((sum, r) => sum + (r.abnormalCount || 0), 0)
})

const filteredReports = computed(() => {
  if (activeTab.value === 'all') return reports.value
  return reports.value.filter(r => r.requestType === activeTab.value)
})

// ============ 工具方法 ============

const getReportIcon = (type: string) => {
  const map: Record<string, string> = {
    INSPECTION: 'records-o',
    CHECK: 'scan-o',
    IMAGE: 'photo-o'
  }
  return map[type] || 'file-o'
}

const getReportColor = (type: string) => {
  const map: Record<string, string> = {
    INSPECTION: '#4CAF50',
    CHECK: '#2196F3',
    IMAGE: '#FF9800'
  }
  return map[type] || '#6B6B7E'
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    PENDING: 'warning',
    PROCESSING: 'primary',
    COMPLETED: 'success',
    CANCELLED: 'danger'
  }
  return map[status] || 'default'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    PENDING: '待审核',
    PROCESSING: '处理中',
    COMPLETED: '已完成',
    CANCELLED: '已取消'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  if (!date) return ''
  return dayjs(date).format('MM-DD')
}

const formatDateTime = (date: string) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// ============ 操作方法 ============

const viewReport = (report: any) => {
  currentReport.value = report
  showDetail.value = true
  // 标记已读
  if (!report.isViewed) {
    markAsRead(report)
  }
}

const markAsRead = (report: any) => {
  const target = reports.value.find(r => r.id === report.id)
  if (target) {
    target.isViewed = true
  }
  // 如果详情弹窗打开，更新当前显示
  if (currentReport.value?.id === report.id) {
    currentReport.value.isViewed = true
  }
}

const downloadReport = (report: any) => {
  showToast('报告下载功能开发中')
  // 实际项目中：window.open(report.reportFileUrl) 或调用下载 API
}

// ============ 加载数据 ============

const loadReports = async () => {
  try {
    await new Promise(resolve => setTimeout(resolve, 300))
    reports.value = mockReports.map(r => ({ ...r }))
  } catch {
    showToast('加载报告失败')
  }
}

// ============ 生命周期 ============

onMounted(() => {
  loadReports()
})
</script>

<style lang="scss" scoped>
.reports-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

// ===== 统计卡片 =====
.stats-row {
  display: flex;
  align-items: center;
  background: white;
  margin: 12px 16px;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-item {
  flex: 1;
  text-align: center;
  .stat-number {
    display: block;
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
  }
  .stat-label {
    font-size: 12px;
    color: #6B6B7E;
  }
}
.stat-divider {
  width: 1px;
  height: 36px;
  background: #E8E8E8;
}

// ===== Tab =====
.report-tabs {
  background: white;
  :deep(.van-tabs__line) {
    background-color: #4CAF50;
  }
}

// ===== 报告列表 =====
.report-list {
  padding: 12px 16px;
}

.report-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.2s;
  border-left: 4px solid transparent;

  &.unread {
    border-left-color: #E76F51;
    background: #FFF8F6;
  }

  &:active {
    transform: scale(0.98);
  }
}

.report-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.report-info {
  flex: 1;
  min-width: 0;
  .report-top {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    .report-title {
      font-size: 15px;
      font-weight: 500;
      color: #1A1A2E;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .report-meta {
    font-size: 12px;
    color: #6B6B7E;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  .report-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    .abnormal-tag {
      font-size: 12px;
      color: #E76F51;
    }
  }
}

.report-arrow {
  color: #C4C4D6;
  flex-shrink: 0;
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #C4C4D6;
  p {
    font-size: 16px;
    color: #6B6B7E;
    margin-top: 12px;
  }
  .empty-desc {
    font-size: 13px;
    color: #6B6B7E;
  }
}

// ===== 报告详情弹窗 =====
.report-detail {
  padding: 20px 16px 80px;
  height: 100%;
  overflow-y: auto;
}

.detail-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #E8E8E8;
  margin-bottom: 16px;
  .detail-title {
    font-size: 20px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .detail-subtitle {
    font-size: 14px;
    color: #6B6B7E;
    display: flex;
    gap: 16px;
    margin-top: 4px;
  }
}

.detail-section {
  margin-bottom: 16px;
  .section-title {
    font-size: 15px;
    font-weight: 600;
    color: #1A1A2E;
    margin-bottom: 10px;
    padding-left: 10px;
    border-left: 3px solid #4CAF50;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  .info-item {
    display: flex;
    flex-direction: column;
    padding: 6px 12px;
    background: #F5F7FA;
    border-radius: 6px;
    .label {
      font-size: 11px;
      color: #6B6B7E;
    }
    .value {
      font-size: 14px;
      color: #1A1A2E;
      font-weight: 500;
    }
  }
}

.report-content {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 14px 16px;
  .content-text {
    font-size: 14px;
    line-height: 1.8;
    color: #1A1A2E;
    white-space: pre-wrap;
  }
  .content-placeholder {
    font-size: 14px;
    color: #6B6B7E;
    text-align: center;
    padding: 20px 0;
  }
}

.abnormal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.abnormal-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #FFEBEE;
  border-radius: 8px;
  flex-wrap: wrap;
  .item-name {
    font-size: 14px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .item-value {
    font-size: 14px;
    color: #E76F51;
    font-weight: 500;
  }
  .item-range {
    font-size: 12px;
    color: #6B6B7E;
  }
}

.detail-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  border-top: 1px solid #E8E8E8;
  .van-button {
    flex: 1;
    height: 40px;
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}
</style>