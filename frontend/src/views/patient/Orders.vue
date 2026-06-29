<!-- src/views/patient/Orders.vue -->
<template>
  <div class="orders-page">
    <van-nav-bar title="门诊缴费" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-tabs v-model:active="activeTab" class="order-tabs">
      <van-tab title="待缴费" name="unpaid">
        <div class="order-list">
          <!-- 按挂号分组展示 -->
          <div
              v-for="group in unpaidGroups"
              :key="group.registerId"
              class="order-group"
          >
            <div class="group-header">
              <span class="group-dept">{{ group.deptName }}</span>
              <span class="group-date">{{ group.visitDate }}</span>
            </div>
            <div
                v-for="order in group.orders"
                :key="order.itemId"
                class="order-card"
            >
              <div class="order-header">
                <van-checkbox v-model="order.checked" @click.stop />
                <div class="order-info">
                  <div class="order-type">
                    <van-tag :type="getItemTypeTag(order.itemType)" size="small">
                      {{ getItemTypeName(order.itemType) }}
                    </van-tag>
                    <span class="order-name">{{ order.itemName }}</span>
                  </div>
                  <div class="order-time">{{ formatDateTime(order.createTime) }}</div>
                </div>
              </div>
              <div class="order-footer">
                <div class="order-amount">¥{{ order.amount?.toFixed(2) }}</div>
              </div>
            </div>
          </div>

          <div v-if="unpaidOrders.length === 0" class="empty-state">
            <van-icon name="bill-o" size="64" color="#C4C4D6" />
            <p>暂无待缴费项目</p>
          </div>
        </div>
      </van-tab>

      <van-tab title="已缴费" name="paid">
        <div class="order-list">
          <div
              v-for="order in paidOrders"
              :key="order.itemId"
              class="order-card paid"
          >
            <div class="order-header">
              <div class="order-info">
                <div class="order-type">
                  <van-tag :type="getItemTypeTag(order.itemType)" size="small">
                    {{ getItemTypeName(order.itemType) }}
                  </van-tag>
                  <span class="order-name">{{ order.itemName }}</span>
                </div>
                <div class="order-time">{{ formatDateTime(order.payTime || order.createTime) }}</div>
              </div>
              <van-icon name="success" color="#4CAF50" size="20" />
            </div>
            <div class="order-footer">
              <div class="order-amount paid-amount">¥{{ order.amount?.toFixed(2) }}</div>
            </div>
          </div>

          <div v-if="paidOrders.length === 0" class="empty-state">
            <van-icon name="records-o" size="64" color="#C4C4D6" />
            <p>暂无缴费记录</p>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 底部结算栏（仅待缴费且有选中时显示） -->
    <div v-if="activeTab === 'unpaid' && unpaidOrders.length > 0" class="settlement-bar">
      <div class="settlement-left">
        <van-checkbox v-model="selectAll">全选</van-checkbox>
        <div class="total-amount">
          合计：<span class="amount">¥{{ totalAmount.toFixed(2) }}</span>
        </div>
      </div>
      <van-button
          type="primary"
          round
          :disabled="selectedCount === 0"
          @click="handlePay"
      >
        立即支付 ({{ selectedCount }})
      </van-button>
    </div>

    <!-- 支付方式选择 -->
    <van-action-sheet v-model:show="showPaySheet" title="选择支付方式">
      <div class="pay-methods">
        <div class="pay-method" @click="payWith('WECHAT')">
          <van-icon name="wechat" size="28" color="#07C160" />
          <span>微信支付</span>
          <van-icon name="arrow" />
        </div>
        <div class="pay-method" @click="payWith('ALIPAY')">
          <van-icon name="alipay" size="28" color="#1677FF" />
          <span>支付宝支付</span>
          <van-icon name="arrow" />
        </div>
        <div class="pay-method" @click="payWith('BALANCE')">
          <van-icon name="gold-coin-o" size="28" color="#FF9800" />
          <span>余额支付（模拟）</span>
          <van-icon name="arrow" />
        </div>
      </div>
    </van-action-sheet>

    <!-- 支付结果弹窗 -->
    <van-dialog
        v-model:show="showResultDialog"
        :title="payResult === 'success' ? '🎉 支付成功' : '❌ 支付失败'"
        :show-cancel-button="false"
        :confirm-button-text="payResult === 'success' ? '完成' : '重试'"
        @confirm="onResultConfirm"
    >
      <div class="pay-result">
        <div v-if="payResult === 'success'" class="result-success">
          <van-icon name="checked" size="48" color="#4CAF50" />
          <p class="result-amount">支付金额：¥{{ payAmount.toFixed(2) }}</p>
          <p class="result-time">支付时间：{{ payTime }}</p>
        </div>
        <div v-else class="result-fail">
          <van-icon name="cross" size="48" color="#E76F51" />
          <p class="result-msg">{{ payErrorMsg || '支付失败，请稍后重试' }}</p>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

// ============ 状态 ============
const activeTab = ref('unpaid')
const orderList = ref<any[]>([])
const showPaySheet = ref(false)
const showResultDialog = ref(false)
const payResult = ref<'success' | 'fail' | null>(null)
const payAmount = ref(0)
const payTime = ref('')
const payErrorMsg = ref('')

// ============ 模拟数据 ============

// 模拟订单数据
const mockOrders = [
  {
    registerId: 1001,
    deptName: '呼吸内科',
    visitDate: '2026-06-27',
    itemId: 1,
    itemName: '挂号费',
    itemType: 'REGISTER',
    amount: 100,
    orderState: 'UNPAID',
    createTime: dayjs().subtract(2, 'hour').format('YYYY-MM-DD HH:mm:ss'),
    payTime: null,
  },
  {
    registerId: 1001,
    deptName: '呼吸内科',
    visitDate: '2026-06-27',
    itemId: 2,
    itemName: '血常规检查',
    itemType: 'INSPECTION',
    amount: 45.00,
    orderState: 'UNPAID',
    createTime: dayjs().subtract(1, 'hour').format('YYYY-MM-DD HH:mm:ss'),
    payTime: null,
  },
  {
    registerId: 1001,
    deptName: '呼吸内科',
    visitDate: '2026-06-27',
    itemId: 3,
    itemName: '阿莫西林胶囊',
    itemType: 'DRUG',
    amount: 36.50,
    orderState: 'UNPAID',
    createTime: dayjs().subtract(1, 'hour').format('YYYY-MM-DD HH:mm:ss'),
    payTime: null,
  },
  {
    registerId: 1002,
    deptName: '心血管内科',
    visitDate: '2026-06-26',
    itemId: 4,
    itemName: '挂号费',
    itemType: 'REGISTER',
    amount: 120,
    orderState: 'PAID',
    createTime: dayjs().subtract(3, 'day').format('YYYY-MM-DD HH:mm:ss'),
    payTime: dayjs().subtract(3, 'day').add(5, 'minute').format('YYYY-MM-DD HH:mm:ss'),
  },
  {
    registerId: 1002,
    deptName: '心血管内科',
    visitDate: '2026-06-26',
    itemId: 5,
    itemName: '心电图检查',
    itemType: 'CHECK',
    amount: 80.00,
    orderState: 'PAID',
    createTime: dayjs().subtract(3, 'day').format('YYYY-MM-DD HH:mm:ss'),
    payTime: dayjs().subtract(3, 'day').add(10, 'minute').format('YYYY-MM-DD HH:mm:ss'),
  },
]

// ============ 计算属性 ============

// 待缴费（未支付）
const unpaidOrders = computed(() => {
  return orderList.value
      .filter(o => o.orderState === 'UNPAID')
      .map(o => ({ ...o, checked: false }))
})

// 已缴费
const paidOrders = computed(() => {
  return orderList.value.filter(o => o.orderState === 'PAID')
})

// 按挂号分组（待缴费）
const unpaidGroups = computed(() => {
  const groups: Record<number, any> = {}
  unpaidOrders.value.forEach(order => {
    if (!groups[order.registerId]) {
      groups[order.registerId] = {
        registerId: order.registerId,
        deptName: order.deptName,
        visitDate: formatDate(order.visitDate),
        orders: []
      }
    }
    groups[order.registerId].orders.push(order)
  })
  return Object.values(groups)
})

// 选中的订单
const selectedOrders = computed(() => {
  return unpaidOrders.value.filter(o => o.checked)
})

const selectedCount = computed(() => selectedOrders.value.length)

const totalAmount = computed(() => {
  return selectedOrders.value.reduce((sum, o) => sum + (o.amount || 0), 0)
})

// 全选
const selectAll = computed({
  get: () => {
    return unpaidOrders.value.length > 0 &&
        unpaidOrders.value.every(o => o.checked)
  },
  set: (val) => {
    unpaidOrders.value.forEach(o => o.checked = val)
  }
})

// ============ 工具方法 ============

const getItemTypeName = (type?: string) => {
  const map: Record<string, string> = {
    REGISTER: '挂号费',
    CHECK: '检查费',
    INSPECTION: '检验费',
    DRUG: '药费',
    TREATMENT: '治疗费',
    OTHER: '其他'
  }
  return map[type || ''] || type || '其他'
}

const getItemTypeTag = (type?: string) => {
  const map: Record<string, string> = {
    REGISTER: 'danger',
    CHECK: 'primary',
    INSPECTION: 'warning',
    DRUG: 'success',
    TREATMENT: 'info',
  }
  return map[type || ''] || 'default'
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return dayjs(dateStr).format('MM-DD')
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return ''
  return dayjs(dateStr).format('MM-DD HH:mm')
}

// ============ 加载数据 ============

const loadOrders = async () => {
  try {
    // 模拟加载
    await new Promise(resolve => setTimeout(resolve, 300))
    orderList.value = mockOrders.map(o => ({ ...o }))
  } catch {
    showToast('加载失败')
  }
}

// ============ 支付流程 ============

const handlePay = () => {
  if (selectedCount.value === 0) {
    showToast('请选择要支付的项目')
    return
  }
  showPaySheet.value = true
}

const payWith = async (method: string) => {
  showPaySheet.value = false
  payAmount.value = totalAmount.value

  showLoadingToast({
    message: '支付处理中...',
    forbidClick: true,
    duration: 0
  })

  try {
    // 模拟支付请求
    await new Promise((resolve, reject) => {
      setTimeout(() => {
        // 90% 概率成功
        if (Math.random() < 0.9) {
          resolve(true)
        } else {
          reject(new Error('支付接口暂时不可用'))
        }
      }, 1500)
    })

    closeToast()

    // 更新订单状态
    const selectedIds = selectedOrders.value.map(o => o.itemId)
    orderList.value.forEach(o => {
      if (selectedIds.includes(o.itemId)) {
        o.orderState = 'PAID'
        o.payTime = dayjs().format('YYYY-MM-DD HH:mm:ss')
      }
    })

    // 显示成功
    payResult.value = 'success'
    payTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
    showResultDialog.value = true

  } catch (error: any) {
    closeToast()
    payResult.value = 'fail'
    payErrorMsg.value = error.message || '支付失败，请稍后重试'
    showResultDialog.value = true
  }
}

const onResultConfirm = () => {
  showResultDialog.value = false
  if (payResult.value === 'success') {
    // 刷新列表
    loadOrders()
  } else {
    // 重试：重新打开支付方式选择
    // 用户可再次选择
  }
  payResult.value = null
}

// ============ 生命周期 ============

onMounted(() => {
  loadOrders()
})
</script>

<style lang="scss" scoped>
.orders-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 80px;
}

.order-tabs {
  background: white;
  :deep(.van-tabs__line) {
    background-color: #4CAF50;
  }
}

.order-list {
  padding: 12px 16px;
}

// ===== 分组 =====
.order-group {
  margin-bottom: 12px;
}
.group-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 4px 12px;
  .group-dept {
    font-size: 14px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .group-date {
    font-size: 13px;
    color: #6B6B7E;
  }
}

// ===== 订单卡片 =====
.order-card {
  background: white;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: transform 0.1s;

  &.paid {
    background: #FAFAFA;
  }
}

.order-header {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.order-info {
  flex: 1;
  .order-type {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }
  .order-name {
    font-size: 14px;
    color: #1A1A2E;
  }
  .order-time {
    font-size: 12px;
    color: #6B6B7E;
  }
}

.order-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px solid #F0F0F0;
}

.order-amount {
  font-size: 18px;
  font-weight: 700;
  color: #E76F51;
  &.paid-amount {
    color: #4CAF50;
  }
}

// ===== 底部结算栏 =====
.settlement-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  border-top: 1px solid #E8E8E8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}

.settlement-left {
  display: flex;
  align-items: center;
  gap: 16px;
  .total-amount {
    font-size: 14px;
    color: #6B6B7E;
    .amount {
      font-size: 18px;
      font-weight: 700;
      color: #E76F51;
    }
  }
}

.settlement-bar .van-button--primary {
  background: #4CAF50;
  border-color: #4CAF50;
}

// ===== 支付方式 =====
.pay-methods {
  padding: 8px 0 20px;
}
.pay-method {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid #F0F0F0;
  cursor: pointer;
  transition: background 0.1s;
  &:hover { background: #F5F7FA; }
  &:last-child { border-bottom: none; }
  span:first-of-type {
    flex: 1;
    font-size: 16px;
    color: #1A1A2E;
  }
}

// ===== 支付结果 =====
.pay-result {
  text-align: center;
  padding: 20px 0;
}
.result-success, .result-fail {
  p { margin-top: 12px; }
}
.result-amount {
  font-size: 20px;
  font-weight: 700;
  color: #1A1A2E;
}
.result-time {
  font-size: 14px;
  color: #6B6B7E;
}
.result-msg {
  font-size: 16px;
  color: #6B6B7E;
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #C4C4D6;
  p { margin-top: 12px; color: #6B6B7E; }
}
</style>