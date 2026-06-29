<!-- src/views/patient/Orders.vue -->
<template>
  <div class="orders-page">
    <van-nav-bar title="门诊缴费" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-tabs v-model:active="activeTab" class="order-tabs">
      <van-tab title="待缴费" name="unpaid">
        <div class="order-list">
          <div v-for="order in unpaidOrders" :key="order.registerId + '-' + order.itemId" class="order-card">
            <div class="order-header">
              <van-checkbox v-model="order.checked" @click.stop />
              <div class="order-info">
                <div class="order-type">
                  <van-tag :type="getItemTypeTag(order.itemType)">{{ getItemTypeName(order.itemType) }}</van-tag>
                  <span class="order-name">{{ order.itemName }}</span>
                </div>
                <div class="order-time">{{ formatDateTime(order.createTime) }}</div>
              </div>
            </div>
            <div class="order-footer">
              <div class="order-amount">¥{{ order.amount?.toFixed(2) }}</div>
            </div>
          </div>
          <div v-if="unpaidOrders.length === 0" class="empty-state"><van-icon name="bill-o" size="64" color="#C4B8A8" /><p>暂无待缴费项目</p></div>
        </div>
      </van-tab>

      <van-tab title="已缴费" name="paid">
        <div class="order-list">
          <div v-for="order in paidOrders" :key="order.registerId + '-' + order.itemId" class="order-card paid">
            <div class="order-header">
              <div class="order-info">
                <div class="order-type">
                  <van-tag :type="getItemTypeTag(order.itemType)">{{ getItemTypeName(order.itemType) }}</van-tag>
                  <span class="order-name">{{ order.itemName }}</span>
                </div>
                <div class="order-time">{{ formatDateTime(order.createTime) }}</div>
              </div>
              <van-icon name="success" color="#8CB369" size="20" />
            </div>
            <div class="order-footer">
              <div class="order-amount paid-amount">¥{{ order.amount?.toFixed(2) }}</div>
            </div>
          </div>
          <div v-if="paidOrders.length === 0" class="empty-state"><van-icon name="records-o" size="64" color="#C4B8A8" /><p>暂无缴费记录</p></div>
        </div>
      </van-tab>
    </van-tabs>

    <div v-if="activeTab === 'unpaid' && unpaidOrders.length > 0" class="settlement-bar">
      <div class="settlement-left">
        <van-checkbox v-model="selectAll">全选</van-checkbox>
        <div class="total-amount">合计：<span class="amount">¥{{ totalAmount.toFixed(2) }}</span></div>
      </div>
      <van-button type="primary" round :disabled="selectedCount === 0" @click="handlePay">立即支付 ({{ selectedCount }})</van-button>
    </div>

    <van-action-sheet v-model:show="showPaySheet" title="选择支付方式">
      <div class="pay-methods">
        <div class="pay-method" @click="payWith('WECHAT')"><van-icon name="wechat" size="28" color="#07C160" /><span>微信支付</span><van-icon name="arrow" /></div>
        <div class="pay-method" @click="payWith('ALIPAY')"><van-icon name="alipay" size="28" color="#1677FF" /><span>支付宝支付</span><van-icon name="arrow" /></div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getOrders, charge } from '@/api'
import type { OrderListVO, PageResultOrderListVO, ChargeRequestDTO } from '@/api/model'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

type OrderRow = OrderListVO & { checked?: boolean; createTime?: string }

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('unpaid')
const orderList = ref<OrderRow[]>([])
const showPaySheet = ref(false)

const getPatientId = () => {
  const user = userStore.userInfo
  if (user?.patientId) return user.patientId
  const stored = localStorage.getItem('patientId')
  if (stored) return Number(stored)
  return 1
}

const unpaidOrders = computed(() => {
  return orderList.value.filter((o: any) => o.orderState === 'UNPAID')
})

const paidOrders = computed(() => orderList.value.filter((o: any) => o.orderState === 'PAID'))
const selectedOrders = computed(() => unpaidOrders.value.filter((o: any) => o.checked))
const selectedCount = computed(() => selectedOrders.value.length)
const totalAmount = computed(() => selectedOrders.value.reduce((sum, o) => sum + (o.amount || 0), 0))

const selectAll = computed({
  get: () => unpaidOrders.value.length > 0 && unpaidOrders.value.every((o: any) => o.checked),
  set: (val) => unpaidOrders.value.forEach((o: any) => o.checked = val)
})

const getItemTypeName = (type?: string) => {
  switch (type) {
    case 'CHECK': return '检查费'
    case 'INSPECTION': return '检验费'
    case 'DRUG': return '药费'
    case 'PRESCRIPTION': return '处方费'
    case 'DISPOSAL': return '处置费'
    case 'REGISTER': return '挂号费'
    default: return type || '其他'
  }
}
const getItemTypeTag = (type?: string) => {
  switch (type) {
    case 'CHECK': return 'primary'
    case 'INSPECTION': return 'warning'
    case 'DRUG': return 'success'
    case 'PRESCRIPTION': return 'success'
    case 'DISPOSAL': return 'primary'
    case 'REGISTER': return 'danger'
    default: return 'default'
  }
}
const formatDateTime = (date?: string) => date ? dayjs(date).format('MM-DD HH:mm') : ''

const loadOrders = async () => {
  try {
    const res = await getOrders({ query: { patientId: getPatientId(), pageNum: 1, pageSize: 50 } })
    orderList.value = (res.data?.records || []).map((o: any) => ({ ...o, checked: false }))
  } catch { showToast('加载失败') }
}

const handlePay = () => {
  if (selectedCount.value === 0) { showToast('请选择要支付的项目'); return }
  showPaySheet.value = true
}

const payWith = async (method: string) => {
  showPaySheet.value = false
  showLoadingToast({ message: '支付处理中...', forbidClick: true })
  try {
    const allItemIds: number[] = []
    const registerIds = new Set<number>()
    selectedOrders.value.forEach((o: any) => {
      if (o.itemId) allItemIds.push(o.itemId)
      if (o.registerId) registerIds.add(o.registerId)
    })
    if (registerIds.size !== 1) {
      closeToast()
      showToast('请选择同一次就诊下的项目')
      return
    }
    await charge({
      registerId: Array.from(registerIds)[0] || 0,
      itemIds: allItemIds,
      itemTypes: selectedOrders.value.map((o: any) => o.itemType),
      chargeMethod: method,
      amount: totalAmount.value
    })
    closeToast()
    showToast({ message: '支付成功', type: 'success' })
    await loadOrders()
  } catch (error: any) {
    closeToast()
    showToast(error.message || '支付失败')
  }
}

onMounted(loadOrders)
</script>

<style lang="scss" scoped>
.orders-page { min-height: 100vh; background: #FFF9F0; padding-bottom: 70px; }
.order-tabs :deep(.van-tabs__line) { background-color: #F4A261; }
.order-list { padding: 12px; }
.order-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.order-card.paid { background: #FAF3E8; }
.order-header { display: flex; gap: 8px; margin-bottom: 8px; }
.order-info { flex: 1; .order-type { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; } .order-name { font-size: 14px; color: #5C4B3A; } .order-time { font-size: 12px; color: #8B7A6B; } }
.order-footer { display: flex; justify-content: flex-end; padding-top: 8px; border-top: 1px solid #E8DCC8; }
.order-amount { font-size: 18px; font-weight: 700; color: #E76F51; }
.order-amount.paid-amount { color: #8CB369; }
.settlement-bar { position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 12px 16px; border-top: 1px solid #E8DCC8; display: flex; justify-content: space-between; align-items: center; }
.settlement-left { display: flex; align-items: center; gap: 16px; .total-amount { font-size: 14px; color: #8B7A6B; .amount { font-size: 18px; font-weight: 700; color: #E76F51; } } }
.settlement-bar .van-button--primary { background: #F4A261; border-color: #F4A261; }
.empty-state { text-align: center; padding: 60px 0; color: #C4B8A8; }
.pay-method { display: flex; align-items: center; gap: 16px; padding: 16px; border-bottom: 1px solid #E8DCC8; cursor: pointer; span:first-of-type { flex: 1; font-size: 16px; } }
</style>
