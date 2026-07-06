<!-- src/views/patient/Services.vue -->
<template>
  <div class="services-page">
    <van-nav-bar title="全部服务" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 搜索 -->
    <van-search
        v-model="keyword"
        placeholder="搜索服务名称"
        shape="round"
        background="transparent"
        @search="onSearch"
    />

    <!-- 服务分类 -->
    <div class="category-tabs">
      <span
          v-for="cat in categories"
          :key="cat.key"
          class="category-tab"
          :class="{ active: activeCategory === cat.key }"
          @click="activeCategory = cat.key"
      >
        {{ cat.label }}
      </span>
    </div>

    <!-- 服务列表 -->
    <div class="service-grid">
      <div
          v-for="service in filteredServices"
          :key="service.key"
          class="service-item"
          @click="goToService(service)"
      >
        <div class="service-icon" :style="{ background: service.bg, color: service.color }">
          <van-icon :name="service.icon" size="28" />
        </div>
        <span class="service-name">{{ service.label }}</span>
        <span class="service-desc">{{ service.desc }}</span>
      </div>

      <div v-if="filteredServices.length === 0" class="empty-state">
        <van-icon name="search" size="48" color="#C4C4D6" />
        <p>未找到相关服务</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()
const keyword = ref('')
const activeCategory = ref('all')

const categories = [
  { key: 'all', label: '全部' },
  { key: 'appointment', label: '挂号预约' },
  { key: 'exam', label: '检查检验' },
  { key: 'records', label: '记录查询' },
  { key: 'consult', label: '在线服务' },
  { key: 'settings', label: '个人设置' }
]

const allServices = [
  // ===== 挂号预约 =====
  {
    key: 'appointment',
    label: '预约挂号',
    icon: 'calendar-o',
    desc: '在线预约专家号',
    category: 'appointment',
    bg: '#E8F5E9',
    color: '#4CAF50',
    path: '/patient/appointment'
  },
  {
    key: 'checkin',
    label: '就诊报到',
    icon: 'location-o',
    desc: '到院报到',
    category: 'appointment',
    bg: '#E3F2FD',
    color: '#2196F3',
    path: '/patient/checkin'
  },
  {
    key: 'revisit',
    label: '复诊预约',
    icon: 'replay',
    desc: '快速复诊预约',
    category: 'appointment',
    bg: '#F3E5F5',
    color: '#9C27B0',
    path: '/patient/revisit'
  },

  // ===== 检查检验 =====
  {
    key: 'lab',
    label: '检验预约',
    icon: 'filter-o',
    desc: '在线预约检验',
    category: 'exam',
    bg: '#E3F2FD',
    color: '#2196F3',
    path: '/patient/lab-booking'
  },
  {
    key: 'exam',
    label: '检查预约',
    icon: 'scan',
    desc: '在线预约检查',
    category: 'exam',
    bg: '#E8F5E9',
    color: '#4CAF50',
    path: '/patient/exam-booking'
  },
  {
    key: 'physical',
    label: '健康体检',
    icon: 'medal',
    desc: '体检套餐预约',
    category: 'exam',
    bg: '#E0F7FA',
    color: '#00BCD4',
    path: '/patient/physical-exam'
  },

  // ===== 记录查询 =====
  {
    key: 'records',
    label: '病历查询',
    icon: 'records-o',
    desc: '查看就诊记录',
    category: 'records',
    bg: '#FCE4EC',
    color: '#E91E63',
    path: '/patient/records'
  },
  {
    key: 'reports',
    label: '报告查询',
    icon: 'description-o',
    desc: '查看检验检查报告',
    category: 'records',
    bg: '#FFF3E0',
    color: '#FF9800',
    path: '/patient/reports'
  },
  {
    key: 'prescriptions',
    label: '处方查询',
    icon: 'shop-o',
    desc: '查看处方明细',
    category: 'records',
    bg: '#F3E5F5',
    color: '#9C27B0',
    path: '/patient/prescriptions'
  },
  {
    key: 'orders',
    label: '缴费记录',
    icon: 'gold-coin-o',
    desc: '查看缴费记录',
    category: 'records',
    bg: '#FFF3E0',
    color: '#FF9800',
    path: '/patient/orders'
  },

  // ===== 在线服务 =====
  {
    key: 'consult',
    label: '在线咨询',
    icon: 'chat-o',
    desc: '在线问诊咨询',
    category: 'consult',
    bg: '#FFF3E0',
    color: '#FF9800',
    path: '/patient/consult'
  },
  {
    key: 'ai',
    label: '智能问答',
    icon: 'chat-o',
    desc: 'AI智能问诊',
    category: 'consult',
    bg: '#E0F7FA',
    color: '#00BCD4',
    path: '/patient/ai'
  },
  {
    key: 'doctor-schedule',
    label: '出诊查询',
    icon: 'user-circle-o',
    desc: '查看医生排班',
    category: 'consult',
    bg: '#E8EAF6',
    color: '#3F51B5',
    path: '/patient/doctor-schedule'
  },

  // ===== 个人设置 =====
  {
    key: 'patient-manager',
    label: '就诊人管理',
    icon: 'contact-o',
    desc: '管理就诊人信息',
    category: 'settings',
    bg: '#F5F5F5',
    color: '#6B6B7E',
    path: '/patient/patient-manager'
  },
  {
    key: 'messages',
    label: '消息中心',
    icon: 'more-o',
    desc: '查看系统消息',
    category: 'settings',
    bg: '#F5F5F5',
    color: '#6B6B7E',
    path: '/patient/messages'
  },
  {
    key: 'guide',
    label: '就诊指南',
    icon: 'guide-o',
    desc: '就诊流程指引',
    category: 'settings',
    bg: '#E8EAF6',
    color: '#3F51B5',
    path: ''
  },
  {
    key: 'customer-service',
    label: '联系客服',
    icon: 'service-o',
    desc: '在线客服支持',
    category: 'settings',
    bg: '#FBE9E7',
    color: '#FF5722',
    path: ''
  }
]

const filteredServices = computed(() => {
  let result = allServices
  if (activeCategory.value !== 'all') {
    result = result.filter(s => s.category === activeCategory.value)
  }
  if (keyword.value.trim()) {
    result = result.filter(s =>
        s.label.includes(keyword.value.trim()) ||
        s.desc.includes(keyword.value.trim())
    )
  }
  return result
})

const onSearch = () => {
  // 由 computed 处理
}

const goToService = (service: any) => {
  if (service.path) {
    router.push(service.path)
  } else if (service.key === 'guide') {
    router.push('/patient/guide')
  } else if (service.key === 'customer-service') {
    router.push('/patient/customer-service')
  } else {
    showToast('功能开发中')
  }
}
</script>

<style lang="scss" scoped>
.services-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.category-tabs {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px;
  overflow-x: auto;
  &::-webkit-scrollbar { height: 0; }
}

.category-tab {
  flex-shrink: 0;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  color: #6B6B7E;
  background: white;
  cursor: pointer;
  &.active {
    background: #4CAF50;
    color: white;
  }
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 0 16px;
}

.service-item {
  background: white;
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: transform 0.1s;
  &:active { transform: scale(0.96); }
}

.service-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
}

.service-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #1A1A2E;
}

.service-desc {
  display: block;
  font-size: 11px;
  color: #C4C4D6;
  margin-top: 2px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px 0;
  color: #C4C4D6;
  p { font-size: 16px; color: #6B6B7E; margin-top: 12px; }
}
</style>