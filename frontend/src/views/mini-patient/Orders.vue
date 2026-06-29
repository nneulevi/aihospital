<template>
  <main class="mini-page">
    <van-nav-bar title="门诊缴费" />
    <van-tabs v-model:active="activeTab">
      <van-tab title="待缴费" name="unpaid">
        <section class="order-list">
          <article v-for="order in unpaidOrders" :key="orderKey(order)" class="order-card">
            <div>
              <strong>{{ order.itemName || getItemTypeName(order.itemType) }}</strong>
              <span>{{ getItemTypeName(order.itemType) }} · {{ formatDate((order as any).createTime) }}</span>
            </div>
            <b>¥{{ formatAmount(order.amount) }}</b>
          </article>
          <van-empty v-if="!unpaidOrders.length" description="暂无待缴费项目" />
        </section>
      </van-tab>
      <van-tab title="已缴费" name="paid">
        <section class="order-list">
          <article v-for="order in paidOrders" :key="orderKey(order)" class="order-card paid">
            <div>
              <strong>{{ order.itemName || getItemTypeName(order.itemType) }}</strong>
              <span>{{ getItemTypeName(order.itemType) }} · {{ formatDate((order as any).createTime) }}</span>
            </div>
            <b>¥{{ formatAmount(order.amount) }}</b>
          </article>
          <van-empty v-if="!paidOrders.length" description="暂无缴费记录" />
        </section>
      </van-tab>
    </van-tabs>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { getOrders } from '@/api'
import { useUserStore } from '@/stores/user'
import type { OrderListVO } from '@/api/model'

const userStore = useUserStore()
const activeTab = ref('unpaid')
const orders = ref<OrderListVO[]>([])
const unpaidOrders = computed(() => orders.value.filter((item: any) => item.orderState === 'UNPAID'))
const paidOrders = computed(() => orders.value.filter((item: any) => item.orderState === 'PAID'))
const formatAmount = (value?: number) => Number(value || 0).toFixed(2)
const formatDate = (value?: string) => value ? dayjs(value).format('MM-DD HH:mm') : '时间待确认'
const orderKey = (order: any) => `${order.registerId || 0}-${order.itemType || 'ITEM'}-${order.itemId || order.itemName}`

const getItemTypeName = (type?: string) => {
  switch (type) {
    case 'CHECK': return '检查费'
    case 'INSPECTION': return '检验费'
    case 'DRUG': return '药费'
    case 'PRESCRIPTION': return '处方费'
    case 'DISPOSAL': return '处置费'
    case 'REGISTER': return '挂号费'
    default: return type || '其他费用'
  }
}

const loadOrders = async () => {
  if (!userStore.patientId) return
  try {
    const res = await getOrders({ query: { patientId: userStore.patientId, pageNum: 1, pageSize: 50 } })
    orders.value = res.data?.records || res.records || []
  } catch {
    orders.value = []
  }
}

onMounted(loadOrders)
</script>

<style lang="scss" scoped>
.order-list {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
}

.order-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-radius: 8px;
  background: #ffffff;
  padding: 15px;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.order-card.paid {
  background: #f7fffb;
}

.order-card strong,
.order-card span {
  display: block;
}

.order-card strong {
  color: #1f2a37;
  font-size: 15px;
}

.order-card span {
  margin-top: 6px;
  color: #687789;
  font-size: 12px;
}

.order-card b {
  flex: none;
  color: #e76f51;
  font-size: 17px;
}

:deep(.van-tabs__line) {
  background: #2375ff;
}
</style>
