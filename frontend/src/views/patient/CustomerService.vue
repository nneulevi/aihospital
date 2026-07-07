<template>
  <div class="plain-page">
    <van-nav-bar title="联系客服" fixed placeholder left-arrow @click-left="router.back()" />
    <section class="contact-card">
      <van-icon name="service-o" size="44" color="#4CAF50" />
      <strong>智慧医院服务台</strong>
      <p>工作时间：08:00-18:00</p>
      <p>咨询内容：挂号、缴费、报告查询、AI 问诊使用问题</p>
      <van-button type="primary" block round @click="showToast('当前为演示环境，请通过主平台联系管理员')">发起咨询</van-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
const router = useRouter()
</script>

<style lang="scss" scoped>
.plain-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.contact-card { display: grid; gap: 10px; justify-items: center; padding: 24px 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); text-align: center; }
.contact-card strong { color: #1a1a2e; font-size: 18px; }
.contact-card p { margin: 0; color: #5b6b80; line-height: 1.6; }
.contact-card :deep(.van-button--primary) { background: #4caf50; border-color: #4caf50; }
</style>
