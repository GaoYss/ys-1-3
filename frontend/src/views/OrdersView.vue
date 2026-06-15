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
        <div class="status-cell">
          <select
            :value="row.status"
            :disabled="isStatusDisabled(row)"
            @change="changeStatus(row, $event.target.value)"
          >
            <option v-for="opt in getStatusOptions(row)" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <span class="status-hint" :title="row.nextActionsHint">
            {{ row.nextActionsHint }}
          </span>
        </div>
      </template>
      <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
    </DataTable>
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

function isStatusDisabled(row) {
  if (submittingOrderId.value === row.id) return true
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

async function changeStatus(order, targetStatus) {
  if (targetStatus === order.status) return
  if (submittingOrderId.value) return

  const currentLabel = order.statusLabel || labelOf(order.status)
  const targetLabel = labelOf(targetStatus)
  const confirmed = window.confirm(
    `确定要将订单「${order.orderNo}」的状态从「${currentLabel}」改为「${targetLabel}」吗？`
  )
  if (!confirmed) {
    await loadOrders()
    return
  }

  submittingOrderId.value = order.id
  try {
    await ordersApi.updateStatus(order.id, targetStatus)
    await loadOrders()
  } catch (err) {
    const resp = err?.response?.data
    if (resp?.error) {
      alert(`${resp.error}\n\n${resp.nextActionsHint || ''}`)
    } else {
      alert('状态更新失败，请稍后重试')
    }
    await loadOrders()
  } finally {
    submittingOrderId.value = null
  }
}

onMounted(async () => {
  const [optionsRes] = await Promise.all([inventoryApi.options(), loadOrders()])
  ingredients.value = optionsRes.data.ingredients
  suppliers.value = optionsRes.data.suppliers
})
</script>
