<template>
  <div class="page exp-page">
    <div class="page-header">
      <h1 class="page-title">Experiments</h1>
      <button class="new-btn-pill" @click="toggleCreate">
        <span v-if="!showForm">+ New experiment</span>
        <span v-else>Cancel</span>
      </button>
    </div>

    <!-- Inline create form (collapsible) -->
    <div class="create-form-wrap" :class="{ open: showForm }">
      <div class="create-form-inner card">
        <div class="create-form-header">
          <span style="font-size:15px;font-weight:600">New experiment</span>
        </div>

        <div class="form-grid">
          <!-- Name + Dataset row -->
          <el-form ref="formRef" :model="form" :rules="formRules" label-position="top" style="display:contents">
            <el-form-item label="Name" prop="name" class="form-col">
              <el-input v-model="form.name" placeholder="e.g. Prompt A vs B" />
            </el-form-item>
            <el-form-item label="Dataset" prop="dataset_id" class="form-col">
              <el-select v-model="form.dataset_id" placeholder="Select dataset" style="width:100%">
                <el-option v-for="ds in datasetsStore.datasets" :key="ds.id" :label="ds.name" :value="ds.id" />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- Dimensions -->
          <div class="form-full">
            <div class="form-label">Dimensions</div>
            <div class="dim-chips">
              <label
                v-for="dim in dimensionsStore.dimensions"
                :key="dim.id"
                class="dim-chip"
                :class="{ selected: form.dimension_ids.includes(dim.id) }"
              >
                <input type="checkbox" :value="dim.id" v-model="form.dimension_ids" style="display:none" />
                {{ dim.name }}
              </label>
            </div>
          </div>

          <!-- Variants -->
          <div class="form-full">
            <div class="form-label-row">
              <span class="form-label">Variants</span>
              <button class="add-variant-btn" @click="addVariant">+ Add variant</button>
            </div>
            <div v-if="variantError" class="variant-error">Add at least one variant with a system prompt.</div>
            <div class="variants-list">
              <div v-for="(v, idx) in form.variants" :key="idx" class="variant-row">
                <div class="variant-row-top">
                  <el-input v-model="v.name" placeholder="Name" style="width:140px" />
                  <el-select v-model="v.model" style="width:160px">
                    <el-option label="gpt-4o-mini" value="gpt-4o-mini" />
                    <el-option label="gpt-4o" value="gpt-4o" />
                    <el-option label="claude-3-5-haiku-20241022" value="claude-3-5-haiku-20241022" />
                  </el-select>
                  <span style="font-size:12px;color:var(--text-secondary);white-space:nowrap">Temp {{ v.temperature.toFixed(1) }}</span>
                  <el-slider v-model="v.temperature" :min="0" :max="2" :step="0.1" style="width:80px" />
                  <button v-if="form.variants.length > 1" class="remove-variant-btn" @click="form.variants.splice(idx, 1)">×</button>
                </div>
                <el-input v-model="v.system_prompt" type="textarea" :rows="2" placeholder="System prompt..." style="margin-top:6px" />
              </div>
            </div>
          </div>
        </div>

        <div class="create-form-footer">
          <el-button @click="toggleCreate">Cancel</el-button>
          <el-button type="primary" :loading="creating" @click="handleCreate" style="background:var(--matcha-600);border-color:var(--matcha-600)">
            Create &amp; run →
          </el-button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" style="display:flex;flex-direction:column;gap:8px">
      <el-skeleton v-for="i in 3" :key="i" animated class="exp-card" style="height:88px" />
    </div>

    <!-- Empty -->
    <div v-else-if="store.experiments.length === 0 && !showForm" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
      </svg>
      <p>No experiments yet — run your first evaluation</p>
      <button class="new-btn-pill" @click="toggleCreate">+ New experiment</button>
    </div>

    <!-- Experiment cards -->
    <div v-else class="exp-list">
      <div
        v-for="exp in store.experiments"
        :key="exp.id"
        class="exp-card card"
        @click="$router.push({ name: 'experiment-detail', params: { id: exp.id } })"
      >
        <div class="exp-card-top">
          <span class="exp-name">{{ exp.name }}</span>
          <span :class="['status-badge', exp.status]">
            <span v-if="exp.status === 'running'" class="pulse-dot" />
            {{ exp.status }}
          </span>
        </div>
        <div class="exp-card-mid">
          <span class="badge">Dataset #{{ exp.dataset_id }}</span>
          <span class="tag">{{ (exp.variants ?? []).length }} {{ (exp.variants ?? []).length === 1 ? 'variant' : 'variants' }}</span>
        </div>
        <div class="exp-card-bot">
          <span class="exp-date">{{ formatDate(exp.created_at) }}</span>
          <span v-if="exp.status === 'completed' && (exp.leaderboard ?? []).length" class="exp-best">
            Best: {{ exp.leaderboard![0].aggregate_score.toFixed(2) }} — {{ exp.leaderboard![0].variant_name }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useExperimentsStore } from '@/stores/experiments'
import { useDatasetsStore } from '@/stores/datasets'
import { useDimensionsStore } from '@/stores/dimensions'

const router = useRouter()
const store = useExperimentsStore()
const datasetsStore = useDatasetsStore()
const dimensionsStore = useDimensionsStore()

onMounted(() => {
  store.fetchAll()
  datasetsStore.fetchAll()
  dimensionsStore.fetchAll()
  pollInterval = setInterval(() => {
    if (store.experiments.some((e) => e.status === 'running')) store.fetchAll()
  }, 5000)
})

let pollInterval: ReturnType<typeof setInterval>
onUnmounted(() => clearInterval(pollInterval))

const showForm = ref(false)
const creating = ref(false)
const variantError = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  dataset_id: null as number | null,
  dimension_ids: [] as number[],
  variants: [{ name: 'Variant 1', model: 'gpt-4o-mini', system_prompt: '', temperature: 0 }],
})

const formRules: FormRules = {
  name: [{ required: true, message: 'Required', trigger: 'blur' }],
  dataset_id: [{ required: true, message: 'Required', trigger: 'change' }],
}

function toggleCreate() {
  showForm.value = !showForm.value
  if (!showForm.value) resetForm()
}

function resetForm() {
  form.name = ''
  form.dataset_id = null
  form.dimension_ids = []
  form.variants = [{ name: 'Variant 1', model: 'gpt-4o-mini', system_prompt: '', temperature: 0 }]
  variantError.value = false
}

function addVariant() {
  form.variants.push({ name: `Variant ${form.variants.length + 1}`, model: 'gpt-4o-mini', system_prompt: '', temperature: 0 })
}

async function handleCreate() {
  await formRef.value?.validate()
  variantError.value = false
  if (form.variants.some((v) => !v.system_prompt.trim())) {
    variantError.value = true
    return
  }
  creating.value = true
  try {
    const exp = await store.create({
      name: form.name,
      dataset_id: form.dataset_id!,
      dimension_ids: form.dimension_ids,
    })
    for (const v of form.variants) {
      await store.addVariant(exp.id, v)
    }
    // Trigger the run immediately
    const { triggerRun } = await import('@/api/experiments')
    await triggerRun(exp.id)
    ElMessage({ type: 'success', message: 'Experiment created and run started' })
    showForm.value = false
    resetForm()
    router.push({ name: 'experiment-detail', params: { id: exp.id } })
  } finally {
    creating.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.exp-page { padding: 28px 36px; max-width: 860px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title { font-size: 22px; font-weight: 600; }

.new-btn-pill {
  padding: 7px 16px;
  border-radius: 8px;
  border: none;
  background: var(--matcha-600);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.new-btn-pill:hover { background: var(--matcha-800); }

/* Collapsible create form */
.create-form-wrap {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s ease;
  margin-bottom: 0;
  overflow: hidden;
}
.create-form-wrap.open {
  grid-template-rows: 1fr;
  margin-bottom: 20px;
}
.create-form-inner {
  min-height: 0;
  overflow: hidden;
}
.create-form-header { margin-bottom: 16px; }
.create-form-footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.form-col { grid-column: span 1; }
.form-full { grid-column: span 2; margin-bottom: 12px; }

.form-label { font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-bottom: 8px; }
.form-label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }

.dim-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.dim-chip {
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--border);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.12s;
  color: var(--text-secondary);
}
.dim-chip.selected {
  background: var(--matcha-100);
  border-color: var(--matcha-400);
  color: var(--matcha-800);
  font-weight: 500;
}

.add-variant-btn {
  font-size: 12px;
  color: var(--matcha-600);
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 500;
}
.variant-error { font-size: 12px; color: #8B2E2E; margin-bottom: 8px; }

.variants-list { display: flex; flex-direction: column; gap: 10px; }
.variant-row {
  padding: 12px;
  border: 0.5px solid var(--border);
  border-radius: 8px;
  background: var(--cream);
}
.variant-row-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.remove-variant-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-secondary);
  width: 24px;
  height: 24px;
  border-radius: 4px;
}
.remove-variant-btn:hover { background: #FDEAEA; color: #8B2E2E; }

/* Experiment cards */
.exp-list { display: flex; flex-direction: column; gap: 8px; }
.exp-card {
  padding: 16px 18px;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.exp-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

.exp-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.exp-name { font-size: 15px; font-weight: 600; }

.exp-card-mid { display: flex; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.tag {
  font-size: 12px;
  color: var(--text-secondary);
  background: #F0EDE6;
  border-radius: 6px;
  padding: 2px 8px;
}

.exp-card-bot { display: flex; justify-content: space-between; align-items: center; }
.exp-date { font-size: 12px; color: var(--text-secondary); }
.exp-best { font-size: 12px; color: var(--matcha-600); font-weight: 500; }
</style>
