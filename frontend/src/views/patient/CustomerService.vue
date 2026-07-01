<!-- src/views/patient/CustomerService.vue -->
<template>
  <div class="customer-service-page">
    <van-nav-bar title="联系客服" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 客服信息 -->
    <div class="service-card">
      <div class="service-icon">💬</div>
      <div class="service-info">
        <div class="service-title">在线客服</div>
        <div class="service-desc">工作日 8:00-20:00</div>
      </div>
      <van-button type="primary" size="small" round @click="startChat">
        在线咨询
      </van-button>
    </div>

    <div class="service-card">
      <div class="service-icon">📞</div>
      <div class="service-info">
        <div class="service-title">客服热线</div>
        <div class="service-desc">24小时服务</div>
      </div>
      <van-button type="primary" size="small" round @click="callPhone">
        拨打
      </van-button>
    </div>

    <div class="service-card">
      <div class="service-icon">✉️</div>
      <div class="service-info">
        <div class="service-title">在线留言</div>
        <div class="service-desc">我们会尽快回复</div>
      </div>
      <van-button type="primary" size="small" round @click="leaveMessage">
        留言
      </van-button>
    </div>

    <!-- 常见问题 -->
    <div class="section-card">
      <div class="section-title">常见问题</div>
      <div
          v-for="(faq, index) in faqList"
          :key="index"
          class="faq-item"
          @click="toggleFaq(index)"
      >
        <div class="faq-question">
          <span>{{ faq.question }}</span>
          <van-icon :name="faq.expanded ? 'arrow-up' : 'arrow-down'" />
        </div>
        <div v-if="faq.expanded" class="faq-answer">
          {{ faq.answer }}
        </div>
      </div>
    </div>

    <!-- 留言弹窗 -->
    <van-dialog
        v-model:show="showMessageDialog"
        title="在线留言"
        confirm-button-text="提交"
        @confirm="submitMessage"
    >
      <div class="message-form">
        <van-field
            v-model="messageForm.name"
            label="姓名"
            placeholder="请输入您的姓名"
        />
        <van-field
            v-model="messageForm.phone"
            label="手机号"
            placeholder="请输入手机号"
        />
        <van-field
            v-model="messageForm.content"
            type="textarea"
            label="留言内容"
            placeholder="请详细描述您的问题"
            rows="4"
        />
      </div>
    </van-dialog>

    <!-- 提交成功 -->
    <van-dialog
        v-model:show="showSuccess"
        title="✅ 提交成功"
        :show-cancel-button="false"
        confirm-button-text="知道了"
        @confirm="showSuccess = false"
    >
      <p class="success-text">您的留言已收到，我们会尽快与您联系</p>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()

const faqList = ref([
  {
    question: '如何预约挂号？',
    answer: '您可以通过首页的「预约挂号」功能，选择科室、医生和时间进行预约。',
    expanded: false
  },
  {
    question: '如何取消挂号？',
    answer: '在「挂号记录」中找到对应的挂号记录，点击「取消挂号」即可。',
    expanded: false
  },
  {
    question: '如何查看检查报告？',
    answer: '在「报告查询」中可以查看您的检验和检查报告。',
    expanded: false
  },
  {
    question: '医保如何使用？',
    answer: '就诊时出示医保卡，结算时系统会自动进行医保报销。',
    expanded: false
  },
  {
    question: '如何切换就诊人？',
    answer: '在首页点击就诊人名称，或在「就诊人管理」中切换默认就诊人。',
    expanded: false
  }
])

const showMessageDialog = ref(false)
const showSuccess = ref(false)
const messageForm = ref({
  name: '',
  phone: '',
  content: ''
})

const startChat = () => {
  showToast('正在连接在线客服...')
}

const callPhone = () => {
  showToast('客服热线：400-123-4567')
}

const leaveMessage = () => {
  showMessageDialog.value = true
}

const toggleFaq = (index: number) => {
  faqList.value[index].expanded = !faqList.value[index].expanded
}

const submitMessage = () => {
  showMessageDialog.value = false
  showSuccess.value = true
  messageForm.value = { name: '', phone: '', content: '' }
}
</script>

<style lang="scss" scoped>
.customer-service-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 20px;
}

.service-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .service-icon {
    font-size: 32px;
  }
  .service-info {
    flex: 1;
    .service-title { font-size: 16px; font-weight: 500; color: #1A1A2E; }
    .service-desc { font-size: 13px; color: #6B6B7E; }
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

.section-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1A1A2E;
    margin-bottom: 12px;
  }
}

.faq-item {
  padding: 10px 0;
  border-bottom: 1px solid #F0F0F0;
  &:last-child { border-bottom: none; }

  .faq-question {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #1A1A2E;
    cursor: pointer;
    .van-icon { color: #C4C4D6; }
  }
  .faq-answer {
    font-size: 14px;
    color: #6B6B7E;
    padding: 8px 0 4px;
    line-height: 1.6;
  }
}

.message-form {
  padding: 8px 16px 16px;
}

.success-text {
  text-align: center;
  padding: 16px 0;
  font-size: 16px;
  color: #1A1A2E;
}
</style>