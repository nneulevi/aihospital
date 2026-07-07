<template>
  <div class="service-page">
    <van-nav-bar title="全部服务" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="service-section">
      <div class="section-title">门诊服务</div>
      <div class="service-grid">
        <button v-for="item in services" :key="item.title" type="button" class="grid-item" @click="router.push(item.path)">
          <span class="grid-icon" :class="item.tone"><van-icon :name="item.icon" /></span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.desc }}</small>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const services = [
  { title: 'AI 问诊', desc: '症状预问诊与科室推荐', icon: 'chat-o', path: '/patient/ai', tone: 'cyan' },
  { title: '预约挂号', desc: '选择科室医生并提交', icon: 'calendar-o', path: '/patient/appointment', tone: 'green' },
  { title: '挂号记录', desc: '查看历史就诊记录', icon: 'records-o', path: '/patient/appointments', tone: 'blue' },
  { title: '门诊缴费', desc: '查看待缴费项目', icon: 'gold-coin-o', path: '/patient/orders', tone: 'orange' },
  { title: '就诊报到', desc: '到院后确认就诊状态', icon: 'location-o', path: '/patient/checkin', tone: 'pink' },
  { title: '候诊查询', desc: '查看当前队列提示', icon: 'clock-o', path: '/patient/queue', tone: 'purple' },
  { title: '报告查询', desc: '查看检查检验与影像报告', icon: 'file-o', path: '/patient/reports', tone: 'slate' },
  { title: '联系客服', desc: '挂号、缴费、报告与系统使用咨询', icon: 'service-o', path: '/patient/customer-service', tone: 'green' },
  { title: '处方查询', desc: '查看药品与费用记录', icon: 'bill-o', path: '/patient/prescriptions', tone: 'yellow' },
  { title: '检验预约', desc: '常规检验预约入口', icon: 'medical-o', path: '/patient/lab-booking', tone: 'blue' },
  { title: '检查预约', desc: '影像检查预约入口', icon: 'scan-o', path: '/patient/exam-booking', tone: 'green' },
  { title: '复诊预约', desc: '按历史就诊快速复诊', icon: 'calendar-o', path: '/patient/revisit', tone: 'purple' },
  { title: '健康体检', desc: '体检项目浏览与预约', icon: 'heartbeat-o', path: '/patient/physical-exam', tone: 'cyan' },
]
</script>

<style lang="scss" scoped>
.service-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.service-section { padding: 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.section-title { margin-bottom: 14px; color: #1a1a2e; font-size: 16px; font-weight: 600; }
.service-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.grid-item { min-height: 118px; border: 0; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.08); padding: 14px; text-align: left; display: grid; gap: 6px; }
.grid-icon { width: 42px; height: 42px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 22px; }
.grid-item strong { color: #1a1a2e; font-size: 15px; }
.grid-item small { color: #6b6b7e; line-height: 1.4; }
.green { background: #e8f5e9; color: #4caf50; }
.orange { background: #fff3e0; color: #ff9800; }
.cyan { background: #e0f7fa; color: #00bcd4; }
.purple { background: #f3e5f5; color: #9c27b0; }
.blue { background: #e3f2fd; color: #2196f3; }
.slate { background: #f5f5f5; color: #607d8b; }
.pink { background: #fce4ec; color: #e91e63; }
.yellow { background: #fff8e1; color: #ffc107; }
</style>
