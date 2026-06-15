<template>
  <section>
    <PageHeader eyebrow="Orders" title="采购订单管理">
      <button class="primary-btn" @click="submitOrder">创建订单</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          订单号
          <input v-model="form.orderNo" />
        </label>
        <label>
          供应商
          <select v-model.number="form.supplierId">
            <option disabled :value="null">选择供应商</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
              {{ supplier.name }}
            </option>
          </select>
        </label>
        <label>
          预计到货
          <input v-model="form.expectedDate" type="date" />
        </label>
        <label>
          备注
          <input v-model="form.remark" />
        </label>
      </div>

      <div class="line-editor">
        <select v-model.number="line.ingredientId">
          <option disabled :value="null">选择原料</option>
          <option v-for="item in ingredients" :key="item.id" :value="item.id">
            {{ item.name }} / {{ item.unit }}
          </option>
        </select>
        <input v-model.number="line.quantity" type="number" min="1" placeholder="数量" />
        <input v-model.number="line.unitPrice" type="number" min="0" placeholder="单价" />
        <button class="secondary-btn" @click="addLine">添加明细</button>
      </div>

      <DataTable :columns="lineColumns" :rows="form.items">
        <template #ingredientName="{ row }">{{ ingredientName(row.ingredientId) }}</template>
        <template #amount="{ row }">¥{{ (row.quantity * row.unitPrice).toFixed(2) }}</template>
      </DataTable>
    </section>

    <DataTable :columns="columns" :rows="orders">
      <template #status="{ row }">
        <div class="status-cell" :class="{ 'is-submitting': submittingOrderId === row.id }">
          <template v-if="submittingOrderId === row.id">
            <span class="status-loading" aria-label="处理中">
              <span class="spinner"></span>
              <span>处理中…</span>
            </span>
          </template>
          <template v-else>
            <select
              :value="row.status"
              :disabled="hasNoTransitions(row)"
              @change="requestChangeStatus(row, $event.target.value)"
            >
              <option v-for="opt in getStatusOptions(row)" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
            <span class="status-hint" :title="row.nextActionsHint">
              {{ row.nextActionsHint }}
            </span>
          </template>
          <div v-if="submittingOrderId === row.id" class="status-mask" aria-hidden="true"></div>
        </div>
      </template>
      <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
    </DataTable>

    <div v-if="confirmDialog.visible" class="modal-mask" @click.self="cancelConfirm">
      <div class="modal-card" role="dialog" aria-modal="true">
        <h3 class="modal-title">确认状态变更</h3>
        <p class="modal-body">
          确定要将订单「<strong>{{ confirmDialog.orderNo }}</strong>」的状态
          <br />
          从「<strong>{{ confirmDialog.currentLabel }}</strong>」改为「<strong>{{ confirmDialog.targetLabel }}</strong>」吗？
        </p>
        <div class="modal-actions">
          <button class="secondary-btn" @click="cancelConfirm">取消</button>
          <button class="primary-btn" :disabled="confirmSubmitting" @click="confirmChangeStatus">
            <span v-if="confirmSubmitting" class="btn-spinner"></span>
            {{ confirmSubmitting ? '处理中…' : '确认变更' }}
          </button>
        </div>
      </div>
    </div>

    <transition name="toast">
      <div v-if="toast.visible" class="toast" :class="toast.type">
        {{ toast.message }}
      </div>
    </transition>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { ordersApi } from '../api/orders'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import { STATUS_LABELS } from '../utils/orderStatus'

const orders = ref([])
const suppliers = ref([])
const ingredients = ref([])
const submittingOrderId = ref(null)
const form = reactive({
  orderNo: `PO${new Date().toISOString().slice(0, 10).replaceAll('-', '')}001`,
  supplierId: null,
  expectedDate: '',
  remark: '',
  items: []
})
const line = reactive({ ingredientId: null, quantity: 1, unitPrice: 0 })

const columns = [
  { key: 'orderNo', label: '订单号' },
  { key: 'supplierName', label: '供应商' },
  { key: 'expectedDate', label: '预计到货' },
  { key: 'status', label: '状态' },
  { key: 'totalAmount', label: '金额' }
]
const lineColumns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'quantity', label: '数量' },
  { key: 'unitPrice', label: '单价' },
  { key: 'amount', label: '小计' }
]

const confirmDialog = reactive({
  visible: false,
  orderId: null,
  orderNo: '',
  targetStatus: '',
  currentLabel: '',
  targetLabel: ''
})
const confirmSubmitting = ref(false)

const toast = reactive({
  visible: false,
  type: 'success',
  message: ''
})
let toastTimer = null

function showToast(message, type = 'success', duration = 2500) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.visible = true
  toastTimer = setTimeout(() => {
    toast.visible = false
  }, duration)
}

function ingredientName(id) {
  return ingredients.value.find((item) => item.id === id)?.name || '-'
}

function addLine() {
  if (!line.ingredientId || !line.quantity) return
  form.items.push({ id: Date.now(), ...line })
  Object.assign(line, { ingredientId: null, quantity: 1, unitPrice: 0 })
}

function labelOf(status) {
  return STATUS_LABELS[status] || status
}

function hasNoTransitions(row) {
  const available = row.availableTransitions || []
  return available.length === 0
}

function getStatusOptions(row) {
  const available = row.availableTransitions || []
  const options = [{ value: row.status, label: `${row.statusLabel || labelOf(row.status)} (当前)` }]
  available.forEach((s) => {
    options.push({ value: s, label: `→ ${labelOf(s)}` })
  })
  return options
}

async function loadOrders() {
  const res = await ordersApi.list()
  orders.value = res.data
}

async function submitOrder() {
  if (!form.supplierId || !form.items.length) return
  await ordersApi.create({ ...form })
  Object.assign(form, {
    orderNo: `PO${new Date().toISOString().slice(0, 10).replaceAll('-', '')}${Date.now()
      .toString()
      .slice(-3)}`,
    supplierId: null,
    expectedDate: '',
    remark: '',
    items: []
  })
  await loadOrders()
}

function requestChangeStatus(order, targetStatus) {
  if (targetStatus === order.status) return
  if (submittingOrderId.value) {
    showToast('当前有订单正在处理，请稍候', 'error')
    return
  }

  confirmDialog.visible = true
  confirmDialog.orderId = order.id
  confirmDialog.orderNo = order.orderNo
  confirmDialog.targetStatus = targetStatus
  confirmDialog.currentLabel = order.statusLabel || labelOf(order.status)
  confirmDialog.targetLabel = labelOf(targetStatus)
}

function cancelConfirm() {
  if (confirmSubmitting.value) return
  confirmDialog.visible = false
  loadOrders()
}

async function confirmChangeStatus() {
  if (confirmSubmitting.value) return

  confirmSubmitting.value = true
  submittingOrderId.value = confirmDialog.orderId
  try {
    await ordersApi.updateStatus(confirmDialog.orderId, confirmDialog.targetStatus)
    await loadOrders()
    showToast(`订单「${confirmDialog.orderNo}」状态已更新为「${confirmDialog.targetLabel}」`, 'success')
    confirmDialog.visible = false
  } catch (err) {
    const resp = err?.response?.data
    const msg = resp?.error
      ? `${resp.error}${resp.nextActionsHint ? ' — ' + resp.nextActionsHint : ''}`
      : '状态更新失败，请稍后重试'
    showToast(msg, 'error', 4000)
    await loadOrders()
  } finally {
    confirmSubmitting.value = false
    submittingOrderId.value = null
  }
}

onMounted(async () => {
  const [optionsRes] = await Promise.all([inventoryApi.options(), loadOrders()])
  ingredients.value = optionsRes.data.ingredients
  suppliers.value = optionsRes.data.suppliers
})
</script>
