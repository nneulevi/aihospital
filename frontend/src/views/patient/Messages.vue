<!-- src/views/patient/Messages.vue -->
<template>
  <div class="messages-page">
    <van-nav-bar title="消息中心" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-tabs v-model:active="activeTab" class="message-tabs">
      <van-tab title="全部" name="all" />
      <van-tab title="系统通知" name="SYSTEM" />
      <van-tab title="就诊提醒" name="VISIT" />
      <van-tab title="报告通知" name="REPORT" />
    </van-tabs>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多消息了"
          @load="onLoad"
      >
        <div
            v-for="msg in messageList"
            :key="msg.id"
            class="message-card"
            :class="{ unread: !msg.isRead }"
            @click="viewMessage(msg)"
        >
          <div class="message-icon" :style="{ background: getIconBg(msg.type) }">
            <van-icon :name="getIcon(msg.type)" size="22" color="white" />
          </div>
          <div class="message-info">
            <div class="message-top">
              <span class="message-title">{{ msg.title }}</span>
              <span class="message-time">{{ formatTime(msg.createTime) }}</span>
            </div>
            <div class="message-preview">{{ msg.content }}</div>
            <div class="message-tags">
              <van-tag v-if="!msg.isRead" type="danger" size="mini">未读</van-tag>
              <van-tag :type="getTagType(msg.type)" size="mini">{{ getTagText(msg.type) }}</van-tag>
            </div>
          </div>
          <van-icon name="arrow" class="message-arrow" />
        </div>

        <div v-if="messageList.length === 0 && !loading" class="empty-state">
          <van-icon name="bell-o" size="64" color="#C4C4D6" />
          <p class="empty-title">暂无消息</p>
          <p class="empty-desc">您还没有收到任何消息</p>
        </div>
      </van-list>
    </van-pull-refresh>

    <!-- 消息详情弹窗 -->
    <van-popup
        v-model:show="showDetail"
        position="bottom"
        :style="{ height: '60%', borderRadius: '16px 16px 0 0' }"
        closeable
        close-icon-position="top-right"
    >
      <div class="message-detail" v-if="currentMessage">
        <div class="detail-header">
          <div class="detail-title">{{ currentMessage.title }}</div>
          <div class="detail-time">{{ formatDateTime(currentMessage.createTime) }}</div>
        </div>
        <div class="detail-content">{{ currentMessage.fullContent || currentMessage.content }}</div>
        <div class="detail-actions">
          <van-button v-if="!currentMessage.isRead" type="primary" round block @click="markAsRead(currentMessage)">
            标记已读
          </van-button>
          <van-button v-else plain round block disabled>已读</van-button>
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

const activeTab = ref('all')
const messageList = ref<any[]>([])
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const showDetail = ref(false)
const currentMessage = ref<any>(null)
const pageNum = ref(1)
const pageSize = ref(10)

// ============ 模拟数据 ============
const mockMessages = [
  {
    id: 1,
    type: 'SYSTEM',
    title: '系统升级维护通知',
    content: '尊敬的用户，系统将于2026年7月1日凌晨2:00-5:00进行升级维护...',
    fullContent: '尊敬的用户，系统将于2026年7月1日凌晨2:00-5:00进行升级维护，届时部分功能可能无法使用，给您带来不便敬请谅解。',
    isRead: false,
    createTime: '2026-06-30 10:00:00'
  },
  {
    id: 2,
    type: 'VISIT',
    title: '就诊提醒：明日您有预约',
    content: '您已预约2026年7月1日上午呼吸内科张敏主任医师的门诊...',
    fullContent: '您已预约2026年7月1日上午呼吸内科张敏主任医师的门诊，请提前15分钟到达候诊区，携带身份证和医保卡。',
    isRead: false,
    createTime: '2026-06-30 08:30:00'
  },
  {
    id: 3,
    type: 'REPORT',
    title: '检验报告已生成',
    content: '您的血常规检验报告已生成，请登录查看详细结果...',
    fullContent: '您的血常规检验报告已生成，各项指标均在正常范围内。点击查看完整报告。',
    isRead: true,
    createTime: '2026-06-29 16:20:00'
  },
  {
    id: 4,
    type: 'SYSTEM',
    title: '欢迎使用智慧云脑诊疗平台',
    content: '感谢您注册智慧云脑诊疗平台，我们将为您提供优质的医疗服务...',
    fullContent: '感谢您注册智慧云脑诊疗平台，我们将为您提供优质的医疗服务。您可以使用预约挂号、在线问诊、报告查询等功能。',
    isRead: true,
    createTime: '2026-06-28 09:00:00'
  },
  {
    id: 5,
    type: 'VISIT',
    title: '就诊提醒：2小时后您有预约',
    content: '您已预约今天上午10:30心血管内科李为民副主任医师...',
    fullContent: '您已预约今天上午10:30心血管内科李为民副主任医师的门诊，请提前15分钟到达候诊区。',
    isRead: true,
    createTime: '2026-06-27 08:00:00'
  },
  {
    id: 6,
    type: 'REPORT',
    title: 'CT检查报告已生成',
    content: '您的头颅CT平扫报告已生成，请登录查看详细结果...',
    fullContent: '您的头颅CT平扫报告已生成，未见明显异常。如有疑问请咨询您的医生。',
    isRead: false,
    createTime: '2026-06-26 14:30:00'
  }
]

// ============ 计算属性 ============
const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messageList.value
  return messageList.value.filter(m => m.type === activeTab.value)
})

// ============ 方法 ============
const getIcon = (type: string) => {
  const map: Record<string, string> = {
    SYSTEM: 'info-o',
    VISIT: 'clock-o',
    REPORT: 'file-o'
  }
  return map[type] || 'bell-o'
}

const getIconBg = (type: string) => {
  const map: Record<string, string> = {
    SYSTEM: '#2196F3',
    VISIT: '#FF9800',
    REPORT: '#4CAF50'
  }
  return map[type] || '#6B6B7E'
}

const getTagText = (type: string) => {
  const map: Record<string, string> = {
    SYSTEM: '系统',
    VISIT: '就诊',
    REPORT: '报告'
  }
  return map[type] || '其他'
}

const getTagType = (type: string) => {
  const map: Record<string, string> = {
    SYSTEM: 'primary',
    VISIT: 'warning',
    REPORT: 'success'
  }
  return map[type] || 'default'
}

const formatTime = (time: string) => {
  if (!time) return ''
  return dayjs(time).format('MM-DD HH:mm')
}

const formatDateTime = (time: string) => {
  if (!time) return ''
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const loadMessages = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 400))
    const start = (pageNum.value - 1) * pageSize.value
    const end = start + pageSize.value
    const all = mockMessages
    const data = all.slice(start, end)
    if (refreshing.value) {
      messageList.value = data
      refreshing.value = false
    } else {
      messageList.value.push(...data)
    }
    if (messageList.value.length >= all.length) finished.value = true
  } catch {
    showToast('加载消息失败')
  } finally {
    loading.value = false
  }
}

const onRefresh = () => {
  pageNum.value = 1
  messageList.value = []
  finished.value = false
  loadMessages()
}

const onLoad = () => {
  if (!finished.value) {
    pageNum.value++
    loadMessages()
  }
}

const viewMessage = (msg: any) => {
  currentMessage.value = msg
  showDetail.value = true
  if (!msg.isRead) {
    markAsRead(msg)
  }
}

const markAsRead = (msg: any) => {
  const target = messageList.value.find(m => m.id === msg.id)
  if (target) {
    target.isRead = true
  }
  if (currentMessage.value?.id === msg.id) {
    currentMessage.value.isRead = true
  }
}

const onTabChange = () => {
  // 切换tab时重置列表
  pageNum.value = 1
  messageList.value = []
  finished.value = false
  loadMessages()
}

// ============ 生命周期 ============
onMounted(() => {
  loadMessages()
})
</script>

<style lang="scss" scoped>
.messages-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.message-tabs {
  background: white;
  :deep(.van-tabs__line) {
    background-color: #4CAF50;
  }
}

.message-card {
  background: white;
  margin: 10px 16px;
  padding: 14px 16px;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  border-left: 4px solid transparent;

  &.unread {
    border-left-color: #4CAF50;
    background: #FAFDFA;
  }

  &:active {
    transform: scale(0.98);
  }
}

.message-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-info {
  flex: 1;
  min-width: 0;
}

.message-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.message-title {
  font-size: 15px;
  font-weight: 500;
  color: #1A1A2E;
}

.message-time {
  font-size: 12px;
  color: #C4C4D6;
  flex-shrink: 0;
}

.message-preview {
  font-size: 13px;
  color: #6B6B7E;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-tags {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.message-arrow {
  color: #C4C4D6;
  margin-top: 4px;
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #C4C4D6;
  .empty-title {
    font-size: 16px;
    color: #6B6B7E;
    margin-top: 12px;
  }
  .empty-desc {
    font-size: 14px;
  }
}

// ===== 详情弹窗 =====
.message-detail {
  padding: 20px 16px 80px;
  height: 100%;
  overflow-y: auto;
}

.detail-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #E8E8E8;
  margin-bottom: 16px;
  .detail-title {
    font-size: 18px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .detail-time {
    font-size: 13px;
    color: #C4C4D6;
    margin-top: 4px;
  }
}

.detail-content {
  font-size: 15px;
  line-height: 1.8;
  color: #1A1A2E;
  white-space: pre-wrap;
  padding: 4px 0;
}

.detail-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  border-top: 1px solid #E8E8E8;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
    height: 44px;
  }
}
</style>