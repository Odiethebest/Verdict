<template>
  <MasterDetail>
    <template #master>
      <SectionHeader title="Dimensions" />

      <button class="new-btn" @click="showNew">
        + New dimension
      </button>

      <!-- Total weight indicator -->
      <div v-if="store.dimensions.length > 0" class="weight-bar">
        <span class="weight-label">Total weight</span>
        <span :class="['weight-value', totalWeight > 1.001 ? 'over' : 'ok']">
          {{ (totalWeight * 100).toFixed(0) }}%
        </span>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" style="display:flex;flex-direction:column;gap:8px;margin-top:8px">
        <el-skeleton v-for="i in 3" :key="i" animated style="height:58px;border-radius:8px" />
      </div>

      <!-- Empty -->
      <div v-else-if="store.dimensions.length === 0" style="margin-top:32px;text-align:center;color:var(--text-secondary);font-size:13px">
        No dimensions yet
      </div>

      <!-- List -->
      <div v-else class="item-list">
        <div
          v-for="dim in store.dimensions"
          :key="dim.id"
          class="item-row"
          :class="{ active: selectedId === dim.id }"
          @click="selectDimension(dim)"
        >
          <div class="item-main">
            <span class="item-name">{{ dim.name }}</span>
            <span class="weight-badge">{{ (dim.weight * 100).toFixed(0) }}%</span>
          </div>
          <div class="item-sub">{{ dim.scorer_prompt }}</div>
        </div>
      </div>
    </template>

    <template #detail>
      <PanelPlaceholder
        v-if="panelMode === 'placeholder'"
        icon="dimension"
        title="Select a dimension to edit"
        subtitle="Or create a new one"
      />

      <div v-else class="panel-form">
        <div class="panel-form-header">
          <span class="panel-form-title">{{ selectedId ? `Edit ${form.name || 'dimension'}` : 'New dimension' }}</span>
          <div style="display:flex;gap:6px;align-items:center">
            <el-popconfirm
              v-if="selectedId"
              title="Delete this dimension?"
              confirm-button-text="Delete"
              cancel-button-text="Cancel"
              @confirm="handleDelete"
            >
              <template #reference>
                <button class="delete-btn">Delete</button>
              </template>
            </el-popconfirm>
            <button class="close-btn" @click="closePanel">×</button>
          </div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="Name" prop="name">
            <el-input v-model="form.name" placeholder="e.g. Accuracy" />
          </el-form-item>

          <el-form-item prop="weight">
            <template #label>
              <div style="display:flex;justify-content:space-between;width:100%">
                <span>Weight</span>
                <span style="font-weight:600;color:var(--matcha-600)">{{ form.weight.toFixed(2) }}</span>
              </div>
            </template>
            <el-slider v-model="form.weight" :min="0.01" :max="1.0" :step="0.01" />
            <div class="weight-total-row">
              <span>Total across all dimensions:</span>
              <span :class="['weight-total-val', projectedTotal > 1.001 ? 'over' : 'ok']">
                {{ (projectedTotal * 100).toFixed(0) }}%
                <span v-if="projectedTotal > 1.001"> ⚠ exceeds 100%</span>
                <span v-else> ✓</span>
              </span>
            </div>
          </el-form-item>

          <el-form-item label="Scorer prompt" prop="scorer_prompt">
            <template #label>
              <div>
                <span>Scorer prompt</span>
                <p style="font-size:11px;color:var(--text-secondary);margin-top:2px;font-weight:400">
                  Instruct the judge how to score this dimension. Variables: <code>{input}</code>, <code>{output}</code>, <code>{reference}</code>
                </p>
              </div>
            </template>
            <el-input
              v-model="form.scorer_prompt"
              type="textarea"
              :rows="5"
              placeholder="Score the factual accuracy of the answer from 0.0 to 1.0 where 1.0 means fully accurate and 0.0 means completely wrong."
            />
          </el-form-item>
        </el-form>

        <div class="panel-form-actions">
          <el-button @click="closePanel">Cancel</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave" style="background:var(--matcha-600);border-color:var(--matcha-600)">
            {{ selectedId ? 'Save changes' : 'Create dimension' }}
          </el-button>
        </div>
      </div>
    </template>
  </MasterDetail>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import MasterDetail from '@/components/MasterDetail.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import PanelPlaceholder from '@/components/PanelPlaceholder.vue'
import { useDimensionsStore } from '@/stores/dimensions'
import type { Dimension } from '@/types'

const store = useDimensionsStore()
onMounted(() => store.fetchAll())

type PanelMode = 'placeholder' | 'form'
const panelMode = ref<PanelMode>('placeholder')
const selectedId = ref<number | null>(null)
const saving = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', weight: 0.5, scorer_prompt: '' })

const rules: FormRules = {
  name: [{ required: true, message: 'Required', trigger: 'blur' }],
  weight: [{ required: true, message: 'Required', trigger: 'change' }],
  scorer_prompt: [{ required: true, message: 'Required', trigger: 'blur' }],
}

const totalWeight = computed(() =>
  store.dimensions.reduce((s, d) => s + d.weight, 0),
)

// Projected total: replace current dim's weight with slider value
const projectedTotal = computed(() => {
  if (!selectedId.value) {
    return totalWeight.value + form.weight
  }
  const others = store.dimensions.filter((d) => d.id !== selectedId.value)
  return others.reduce((s, d) => s + d.weight, 0) + form.weight
})

function selectDimension(dim: Dimension) {
  selectedId.value = dim.id
  form.name = dim.name
  form.weight = dim.weight
  form.scorer_prompt = dim.scorer_prompt
  panelMode.value = 'form'
}

function showNew() {
  selectedId.value = null
  form.name = ''
  form.weight = 0.5
  form.scorer_prompt = ''
  panelMode.value = 'form'
}

function closePanel() {
  panelMode.value = 'placeholder'
  selectedId.value = null
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (selectedId.value) {
      await store.update(selectedId.value, { name: form.name, weight: form.weight, scorer_prompt: form.scorer_prompt })
      ElMessage({ type: 'success', message: 'Dimension updated' })
    } else {
      await store.create({ name: form.name, weight: form.weight, scorer_prompt: form.scorer_prompt })
      ElMessage({ type: 'success', message: 'Dimension created' })
      closePanel()
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!selectedId.value) return
  await store.remove(selectedId.value)
  ElMessage({ type: 'success', message: 'Dimension deleted' })
  closePanel()
}
</script>

<style scoped>
.new-btn {
  display: block;
  width: 100%;
  padding: 8px 0;
  margin-bottom: 10px;
  border: 1px solid var(--matcha-400);
  border-radius: 8px;
  background: transparent;
  color: var(--matcha-600);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.new-btn:hover { background: var(--matcha-50); }

.weight-bar {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 4px 2px;
  margin-bottom: 10px;
  color: var(--text-secondary);
}
.weight-value.ok    { color: var(--matcha-600); font-weight: 600; }
.weight-value.over  { color: #D4800A;            font-weight: 600; }

.item-list { display: flex; flex-direction: column; gap: 4px; }

.item-row {
  padding: 10px 10px 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}
.item-row:hover  { background: var(--matcha-50); }
.item-row.active { background: var(--matcha-50); border-left-color: var(--matcha-600); }

.item-main { display: flex; justify-content: space-between; align-items: baseline; }
.item-name { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.item-sub  { font-size: 11px; color: var(--text-secondary); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

.weight-badge {
  font-size: 11px;
  font-weight: 500;
  background: var(--matcha-100);
  color: var(--matcha-800);
  border-radius: 10px;
  padding: 2px 7px;
}

.panel-form { max-width: 540px; }
.panel-form-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.panel-form-title  { font-size: 18px; font-weight: 600; color: var(--text-primary); }

.close-btn {
  width: 28px; height: 28px;
  border: none; background: none; cursor: pointer;
  font-size: 18px; color: var(--text-secondary);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
}
.close-btn:hover { background: var(--matcha-50); }

.delete-btn {
  font-size: 12px;
  padding: 4px 10px;
  border: 0.5px solid #F0C0C0;
  border-radius: 6px;
  background: transparent;
  color: #8B2E2E;
  cursor: pointer;
}
.delete-btn:hover { background: #FDEAEA; }

.weight-total-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
}
.weight-total-val.ok   { color: var(--matcha-600); font-weight: 500; }
.weight-total-val.over { color: #D4800A;            font-weight: 500; }

.panel-form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
</style>
