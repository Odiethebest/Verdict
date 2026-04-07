<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Experiments</h1>
      <el-button type="primary" @click="openWizard" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        New experiment
      </el-button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="store.loading" style="display:flex;flex-direction:column;gap:8px">
      <el-skeleton v-for="i in 3" :key="i" animated class="exp-row">
        <template #template>
          <div style="display:flex;align-items:center;gap:16px">
            <el-skeleton-item variant="h3" style="width:200px" />
            <el-skeleton-item variant="button" style="width:80px" />
            <el-skeleton-item variant="button" style="width:80px;margin-left:auto" />
          </div>
        </template>
      </el-skeleton>
    </div>

    <!-- Empty state -->
    <div v-else-if="store.experiments.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
      </svg>
      <p>No experiments yet — run your first evaluation</p>
      <el-button type="primary" @click="openWizard" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        New experiment
      </el-button>
    </div>

    <!-- Experiment list -->
    <div v-else style="display:flex;flex-direction:column;gap:6px">
      <div v-for="exp in store.experiments" :key="exp.id" class="exp-row">
        <div class="exp-left">
          <span class="exp-name">{{ exp.name }}</span>
          <span class="exp-date">{{ formatDate(exp.created_at) }}</span>
        </div>
        <div class="exp-center">
          <span class="badge">Dataset #{{ exp.dataset_id }}</span>
        </div>
        <div class="exp-right">
          <span :class="['status-badge', exp.status]">
            <span v-if="exp.status === 'running'" class="pulse-dot" />
            {{ exp.status }}
          </span>
          <el-button size="small" @click="$router.push({ name: 'experiment-detail', params: { id: exp.id } })">
            View
          </el-button>
        </div>
      </div>
    </div>

    <!-- Wizard dialog -->
    <el-dialog v-model="showWizard" title="New experiment" width="600px" :close-on-click-modal="false" @close="resetWizard">
      <el-steps :active="wizardStep" finish-status="success" simple style="margin-bottom:24px">
        <el-step title="Details" />
        <el-step title="Dimensions" />
        <el-step title="Variants" />
      </el-steps>

      <!-- Step 1 -->
      <div v-if="wizardStep === 0">
        <el-form ref="step1Ref" :model="wiz" :rules="step1Rules" label-position="top">
          <el-form-item label="Experiment name" prop="name">
            <el-input v-model="wiz.name" placeholder="e.g. Prompt A vs B" />
          </el-form-item>
          <el-form-item label="Dataset" prop="dataset_id">
            <el-select v-model="wiz.dataset_id" placeholder="Select a dataset" style="width:100%" @visible-change="(v: boolean) => v && datasetsStore.fetchAll()">
              <el-option v-for="ds in datasetsStore.datasets" :key="ds.id" :label="ds.name" :value="ds.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2 -->
      <div v-else-if="wizardStep === 1">
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">Select the dimensions to score against.</p>
        <el-checkbox-group v-model="wiz.dimension_ids">
          <div style="display:flex;flex-direction:column;gap:8px">
            <el-checkbox
              v-for="dim in dimensionsStore.dimensions"
              :key="dim.id"
              :value="dim.id"
              style="margin-right:0"
            >
              <span style="font-weight:500">{{ dim.name }}</span>
              <span class="badge" style="margin-left:8px">{{ (dim.weight * 100).toFixed(0) }}%</span>
            </el-checkbox>
          </div>
        </el-checkbox-group>
        <p v-if="dimensionsStore.dimensions.length === 0" style="color:var(--text-secondary);font-size:13px">
          No dimensions yet. <RouterLink to="/dimensions">Create one first.</RouterLink>
        </p>
      </div>

      <!-- Step 3 -->
      <div v-else-if="wizardStep === 2">
        <div v-for="(variant, idx) in wiz.variants" :key="idx" class="variant-block">
          <div class="variant-block-header">
            <span style="font-weight:500;font-size:13px">Variant {{ idx + 1 }}</span>
            <button v-if="wiz.variants.length > 1" class="icon-btn danger" @click="wiz.variants.splice(idx, 1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <el-form label-position="top">
            <el-form-item label="Name">
              <el-input v-model="variant.name" :placeholder="`Variant ${idx + 1}`" />
            </el-form-item>
            <el-form-item label="Model">
              <el-select v-model="variant.model" style="width:100%">
                <el-option label="gpt-4o-mini" value="gpt-4o-mini" />
                <el-option label="gpt-4o" value="gpt-4o" />
                <el-option label="claude-3-5-haiku-20241022" value="claude-3-5-haiku-20241022" />
              </el-select>
            </el-form-item>
            <el-form-item label="System prompt">
              <el-input v-model="variant.system_prompt" type="textarea" :rows="3" placeholder="You are a helpful assistant..." />
            </el-form-item>
            <el-form-item :label="`Temperature: ${variant.temperature}`">
              <el-slider v-model="variant.temperature" :min="0" :max="2" :step="0.1" show-stops style="flex:1" />
            </el-form-item>
          </el-form>
        </div>
        <el-button style="width:100%;margin-top:8px" @click="addVariantSlot">+ Add another variant</el-button>
      </div>

      <template #footer>
        <el-button v-if="wizardStep > 0" @click="wizardStep--">Back</el-button>
        <el-button v-if="wizardStep < 2" type="primary" @click="nextStep" style="background:var(--matcha-600);border-color:var(--matcha-600)">
          Next
        </el-button>
        <el-button v-else type="primary" :loading="creating" @click="handleFinish" style="background:var(--matcha-600);border-color:var(--matcha-600)">
          Create &amp; go
        </el-button>
      </template>
    </el-dialog>
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

let pollInterval: ReturnType<typeof setInterval>

onMounted(() => {
  store.fetchAll()
  datasetsStore.fetchAll()
  dimensionsStore.fetchAll()
  pollInterval = setInterval(() => {
    const hasRunning = store.experiments.some((e) => e.status === 'running')
    if (hasRunning) store.fetchAll()
  }, 5000)
})

onUnmounted(() => clearInterval(pollInterval))

// Wizard state
const showWizard = ref(false)
const wizardStep = ref(0)
const creating = ref(false)
const step1Ref = ref<FormInstance>()

const wiz = reactive({
  name: '',
  dataset_id: null as number | null,
  dimension_ids: [] as number[],
  variants: [{ name: 'Variant 1', model: 'gpt-4o-mini', system_prompt: '', temperature: 0 }],
})

const step1Rules: FormRules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  dataset_id: [{ required: true, message: 'Dataset is required', trigger: 'change' }],
}

function openWizard() {
  resetWizard()
  showWizard.value = true
}

function resetWizard() {
  wizardStep.value = 0
  wiz.name = ''
  wiz.dataset_id = null
  wiz.dimension_ids = []
  wiz.variants = [{ name: 'Variant 1', model: 'gpt-4o-mini', system_prompt: '', temperature: 0 }]
}

async function nextStep() {
  if (wizardStep.value === 0) {
    await step1Ref.value?.validate()
  }
  if (wizardStep.value === 1 && wiz.dimension_ids.length === 0) {
    ElMessage({ type: 'warning', message: 'Select at least one dimension' })
    return
  }
  wizardStep.value++
}

function addVariantSlot() {
  wiz.variants.push({ name: `Variant ${wiz.variants.length + 1}`, model: 'gpt-4o-mini', system_prompt: '', temperature: 0 })
}

async function handleFinish() {
  if (wiz.variants.some((v) => !v.system_prompt.trim())) {
    ElMessage({ type: 'warning', message: 'All variants need a system prompt' })
    return
  }
  creating.value = true
  try {
    const exp = await store.create({
      name: wiz.name,
      dataset_id: wiz.dataset_id!,
      dimension_ids: wiz.dimension_ids,
    })
    for (const v of wiz.variants) {
      await store.addVariant(exp.id, v)
    }
    ElMessage({ type: 'success', message: 'Experiment created' })
    showWizard.value = false
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
.exp-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  transition: box-shadow 0.15s;
}
.exp-row:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

.exp-left { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.exp-name { font-weight: 600; font-size: 14px; }
.exp-date { font-size: 12px; color: var(--text-secondary); }

.exp-center { display: flex; gap: 6px; }

.exp-right { display: flex; align-items: center; gap: 10px; margin-left: auto; }

.variant-block {
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}
.variant-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 0.5px solid var(--border);
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
}
.icon-btn.danger:hover { background: #FDEAEA; color: #8B2E2E; }
</style>
