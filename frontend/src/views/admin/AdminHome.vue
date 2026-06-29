<!-- src/views/admin/AdminHome.vue -->
<template>
  <div class="admin-home">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">128</div>
        <div class="stat-label">今日挂号</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">¥3,560</div>
        <div class="stat-label">待收费金额</div>
      </div>
      <div class="stat-card">
        <div class="stat-value warning">5</div>
        <div class="stat-label">库存预警</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">42</div>
        <div class="stat-label">在诊患者</div>
      </div>
    </div>

    <div class="module-section">
      <div class="section-title">快捷入口</div>
      <div class="module-grid">
        <div class="module-item" @click="$router.push('/admin/staff/create')">
          <div class="module-icon">👤</div>
          <div class="module-name">创建档案</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/doctor-stats')">
          <div class="module-icon">📊</div>
          <div class="module-name">医生统计</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/dept-stats')">
          <div class="module-icon">🏥</div>
          <div class="module-name">部门统计</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/schedule')">
          <div class="module-icon">📅</div>
          <div class="module-name">AI排班</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/finance')">
          <div class="module-icon">💰</div>
          <div class="module-name">收费管理</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/drug')">
          <div class="module-icon">💊</div>
          <div class="module-name">药房管理</div>
        </div>
        <div class="module-item" @click="$router.push('/admin/finance')">
          <div class="module-icon">📋</div>
          <div class="module-name">日结统计</div>
        </div>
        <div class="module-item" @click="showToast('开发中')">
          <div class="module-icon">⚙️</div>
          <div class="module-name">更多</div>
        </div>
      </div>
    </div>

    <div class="notice-section">
      <div class="section-title">系统公告</div>
      <div class="notice-card">
        <div class="notice-item">
          <span class="notice-dot"></span>
          <span class="notice-text">系统将于今晚23:00进行例行维护</span>
        </div>
        <div class="notice-item">
          <span class="notice-dot"></span>
          <span class="notice-text">新版本AI影像分析模块已上线</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast } from 'vant'
</script>

<style lang="scss" scoped>
.admin-home {
  padding: 12px;
}
.stats-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #F4A261;
  margin-bottom: 4px;
  &.warning {
    color: #E76F51;
  }
}
.stat-label {
  font-size: 13px;
  color: #8B7A6B;
}
.module-section {
  margin-bottom: 16px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #F4A261;
}
.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.module-item {
  background: white;
  border-radius: 12px;
  padding: 16px 8px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
}
.module-icon {
  font-size: 28px;
  margin-bottom: 8px;
}
.module-name {
  font-size: 13px;
  color: #5C4B3A;
}
.notice-section {
  background: white;
  border-radius: 12px;
  padding: 16px;
}
.notice-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #F5F5F5;
  &:last-child {
    border-bottom: none;
  }
}
.notice-dot {
  width: 6px;
  height: 6px;
  background: #F4A261;
  border-radius: 50%;
  flex-shrink: 0;
}
.notice-text {
  font-size: 13px;
  color: #5C4B3A;
}
</style>