<template>
  <div class="result-page">
    <div class="panel">
      <div class="page-title">检查结果详情</div>
      <div class="page-subtitle">结果编号：{{ resultId }}</div>
      <p>当前页面用于承接检查结果、影像报告和医生复核入口。若从患者接诊页进入，请以接诊页的 AI 影像识别与报告生成为准。</p>
      <van-button block round type="primary" @click="$router.push('/doctor')">返回医生工作台</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const resultId = computed(() => route.params.id || route.query.id || '未指定')
</script>

<style lang="scss" scoped>
.result-page {
  padding: 12px;
}
.panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.page-subtitle,
p {
  color: #64748b;
  line-height: 1.6;
}
</style>
