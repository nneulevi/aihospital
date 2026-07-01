<!-- src/views/patient/Guide.vue -->
<template>
  <div class="guide-page">
    <van-nav-bar title="就诊指南" fixed placeholder left-arrow @click-left="() => router.back()" />

    <div class="guide-list">
      <div
          v-for="item in guideItems"
          :key="item.id"
          class="guide-card"
          @click="viewGuide(item)"
      >
        <div class="guide-icon" :style="{ background: item.bg }">
          <van-icon :name="item.icon" size="24" color="white" />
        </div>
        <div class="guide-info">
          <div class="guide-title">{{ item.title }}</div>
          <div class="guide-desc">{{ item.desc }}</div>
        </div>
        <van-icon name="arrow" class="guide-arrow" />
      </div>
    </div>

    <!-- 指南详情弹窗 -->
    <van-popup
        v-model:show="showDetail"
        position="bottom"
        :style="{ height: '70%', borderRadius: '16px 16px 0 0' }"
        closeable
        close-icon-position="top-right"
    >
      <div class="guide-detail" v-if="currentGuide">
        <div class="detail-title">{{ currentGuide.title }}</div>
        <div class="detail-content" v-html="currentGuide.content"></div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const guideItems = ref([
  {
    id: 1,
    title: '预约挂号指南',
    desc: '线上预约挂号流程说明',
    icon: 'calendar-o',
    bg: '#4CAF50',
    content: `
      <h3>📋 预约挂号流程</h3>
      <p>1. 进入「预约挂号」页面</p>
      <p>2. 选择就诊科室</p>
      <p>3. 选择医生和就诊时间</p>
      <p>4. 确认就诊人信息</p>
      <p>5. 提交挂号申请</p>
      <p>6. 收到挂号成功通知</p>
      <br>
      <h3>💡 温馨提示</h3>
      <p>• 可提前7天预约</p>
      <p>• 就诊前1小时可取消预约</p>
    `
  },
  {
    id: 2,
    title: '就诊报到流程',
    desc: '到院后如何报到就诊',
    icon: 'location-o',
    bg: '#2196F3',
    content: `
      <h3>🏥 就诊报到流程</h3>
      <p>1. 到达医院后，打开「就诊报到」</p>
      <p>2. 选择您的挂号记录</p>
      <p>3. 确认信息后点击报到</p>
      <p>4. 获取排队序号</p>
      <p>5. 前往候诊区等待叫号</p>
      <br>
      <h3>💡 温馨提示</h3>
      <p>• 请提前15分钟到达</p>
      <p>• 携带身份证和医保卡</p>
    `
  },
  {
    id: 3,
    title: '检查检验须知',
    desc: '各项检查的注意事项',
    icon: 'scan-o',
    bg: '#FF9800',
    content: `
      <h3>🔬 检验注意事项</h3>
      <p>• 血常规：无需空腹</p>
      <p>• 肝功能：需空腹8小时以上</p>
      <p>• 血脂：需空腹12小时以上</p>
      <p>• 尿常规：留取中段尿</p>
      <br>
      <h3>📷 检查注意事项</h3>
      <p>• CT/MRI：需取下金属物品</p>
      <p>• 彩超：腹部彩超需空腹</p>
      <p>• X光：孕妇请提前告知</p>
    `
  },
  {
    id: 4,
    title: '医保报销指南',
    desc: '医保报销流程和比例',
    icon: 'gold-coin-o',
    bg: '#9C27B0',
    content: `
      <h3>💰 医保报销流程</h3>
      <p>1. 就诊时出示医保卡</p>
      <p>2. 费用结算时自动报销</p>
      <p>3. 查看报销明细</p>
      <br>
      <h3>📊 报销比例</h3>
      <p>• 门诊统筹：70%</p>
      <p>• 住院统筹：85%</p>
      <p>• 特殊病种：90%</p>
      <br>
      <h3>💡 温馨提示</h3>
      <p>• 请确保医保卡余额充足</p>
      <p>• 异地就医需提前备案</p>
    `
  },
  {
    id: 5,
    title: '常见问题解答',
    desc: '就诊常见问题汇总',
    icon: 'question-o',
    bg: '#E76F51',
    content: `
      <h3>❓ 常见问题</h3>
      <p><b>Q：如何取消挂号？</b></p>
      <p>A：在挂号记录中点击「取消挂号」即可。</p>
      <br>
      <p><b>Q：如何查看报告？</b></p>
      <p>A：在「报告查询」中查看检验检查报告。</p>
      <br>
      <p><b>Q：如何联系医生？</b></p>
      <p>A：使用「在线咨询」功能联系医生。</p>
      <br>
      <p><b>Q：如何切换就诊人？</b></p>
      <p>A：在首页点击就诊人名称，或在「就诊人管理」中切换。</p>
    `
  }
])

const showDetail = ref(false)
const currentGuide = ref<any>(null)

const viewGuide = (item: any) => {
  currentGuide.value = item
  showDetail.value = true
}
</script>

<style lang="scss" scoped>
.guide-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 20px;
}

.guide-list {
  padding-top: 12px;
}

.guide-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  &:active { transform: scale(0.98); }
}

.guide-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-info {
  flex: 1;
  .guide-title { font-size: 15px; font-weight: 500; color: #1A1A2E; }
  .guide-desc { font-size: 13px; color: #6B6B7E; }
}

.guide-arrow { color: #C4C4D6; }

// ===== 详情弹窗 =====
.guide-detail {
  padding: 20px 16px 80px;
  height: 100%;
  overflow-y: auto;
  .detail-title {
    font-size: 20px;
    font-weight: 600;
    color: #1A1A2E;
    padding-bottom: 16px;
    border-bottom: 1px solid #E8E8E8;
    margin-bottom: 16px;
  }
  .detail-content {
    font-size: 14px;
    line-height: 1.8;
    color: #1A1A2E;
    h3 {
      font-size: 16px;
      color: #4CAF50;
      margin: 12px 0 8px;
    }
    p {
      margin: 4px 0;
      padding-left: 8px;
    }
    b { color: #1A1A2E; }
  }
}
</style>