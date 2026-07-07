<template>
  <div class="plain-page">
    <van-nav-bar title="就诊指南" fixed placeholder left-arrow @click-left="router.back()" />
    <section v-for="item in items" :key="item.title" class="guide-card">
      <strong>{{ item.title }}</strong>
      <p>{{ item.text }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
const items = [
  { title: '预约挂号', text: '选择科室、医生、日期和午别后提交挂号，成功后可在挂号记录中查看。' },
  { title: '到院就诊', text: '请携带身份证或医保卡，按预约时间提前到达候诊区。' },
  { title: '缴费与报告', text: '医生开立检查、检验、处方后，可在门诊缴费中查看待缴项目。' },
]
</script>

<style lang="scss" scoped>
.plain-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.guide-card { margin-bottom: 10px; padding: 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.guide-card strong { color: #1a1a2e; }
.guide-card p { margin: 8px 0 0; color: #5b6b80; line-height: 1.65; }
</style>
