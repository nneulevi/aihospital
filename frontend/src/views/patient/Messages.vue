<template>
  <div class="message-page">
    <van-nav-bar title="消息中心" fixed placeholder left-arrow @click-left="router.back()" />
    <article v-for="item in messages" :key="item.title" class="message-card">
      <strong>{{ item.title }}</strong>
      <p>{{ item.content }}</p>
      <small>{{ item.time }}</small>
    </article>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
const messages = [
  { title: '挂号提醒', content: '请按预约时间提前到达候诊区。', time: '系统消息' },
  { title: '报告提醒', content: '检查报告发布后可在报告查询或病历详情中查看。', time: '系统消息' },
]
</script>

<style lang="scss" scoped>
.message-page { min-height: 100vh; background: #f5f7fa; padding: 12px 16px 80px; }
.message-card { margin-bottom: 10px; padding: 14px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.message-card strong { color: #1a1a2e; }
.message-card p { margin: 8px 0 4px; color: #5b6b80; line-height: 1.6; }
.message-card small { color: #8b8b9e; }
</style>
