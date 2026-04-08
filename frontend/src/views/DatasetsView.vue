<template>
  <MasterDetail>
    <template #master>
      <SectionHeader title="Datasets" :count="store.datasets.length" />

      <button class="new-btn" @click="showCreate">
        + New dataset
      </button>

      <!-- Loading -->
      <div v-if="store.loading" style="display:flex;flex-direction:column;gap:8px;margin-top:8px">
        <el-skeleton v-for="i in 3" :key="i" animated style="height:58px;border-radius:8px" />
      </div>

      <!-- Empty -->
      <div v-else-if="store.datasets.length === 0" style="margin-top:32px;text-align:center;color:var(--text-secondary);font-size:13px">
        No datasets yet
      </div>

      <!-- List -->
      <div v-else class="item-list">
        <div
          v-for="ds in store.datasets"
          :key="ds.id"
          class="item-row"
          :class="{ active: selectedDataset?.id === ds.id && panelMode === 'detail' }"
          @click="selectDataset(ds)"
        >
          <div class="item-main">
            <span class="item-name">{{ ds.name }}</span>
            <span class="item-meta">{{ caseCount(ds.id) }}</span>
          </div>
          <div v-if="ds.description" class="item-sub">{{ ds.description }}</div>
        </div>
      </div>
    </template>

    <template #detail>
      <!-- Placeholder -->
      <PanelPlaceholder
        v-if="panelMode === 'placeholder'"
        icon="dataset"
        title="Select a dataset"
        subtitle="Or create a new one to upload test cases"
      />

      <!-- Create form -->
      <div v-else-if="panelMode === 'create'" class="panel-form">
        <div class="panel-form-header">
          <span class="panel-form-title">New dataset</span>
          <button class="close-btn" @click="closePanel">×</button>
        </div>
        <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-position="top">
          <el-form-item label="Name" prop="name">
            <el-input v-model="createForm.name" placeholder="e.g. RAG Q&A v1" />
          </el-form-item>
          <el-form-item label="Description">
            <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="Optional" />
          </el-form-item>
        </el-form>
        <div class="panel-form-actions">
          <el-button type="primary" :loading="saving" @click="handleCreate" style="background:var(--matcha-600);border-color:var(--matcha-600)">
            Create dataset
          </el-button>
        </div>
      </div>

      <!-- Dataset detail -->
      <div v-else-if="panelMode === 'detail' && selectedDataset" class="panel-detail">
        <div class="detail-header">
          <div>
            <h2 class="detail-title">{{ selectedDataset.name }}</h2>
            <p v-if="selectedDataset.description" class="detail-desc">{{ selectedDataset.description }}</p>
            <p class="detail-date">Created {{ formatDate(selectedDataset.created_at) }}</p>
          </div>
        </div>

        <!-- Test cases -->
        <div class="cases-section">
          <div class="cases-header">
            <span class="cases-title">Test cases</span>
            <span class="badge" style="margin-left:8px;font-size:13px;padding:2px 10px">{{ currentCases.length }}</span>
          </div>
          <div v-if="loadingCases" style="color:var(--text-secondary);font-size:13px">Loading...</div>
          <div v-else-if="currentCases.length === 0" style="color:var(--text-secondary);font-size:13px;margin-top:8px">
            No test cases yet — upload some below.
          </div>
          <div v-else class="cases-list">
            <div v-for="tc in currentCases" :key="tc.id" class="case-card">
              <p class="case-input">{{ tc.input }}</p>
              <p class="case-ref">{{ tc.reference_output }}</p>
            </div>
          </div>
        </div>

        <div class="divider" />

        <!-- Upload section -->
        <div class="upload-section">
          <div class="cases-title">Upload cases</div>
          <p class="upload-hint">Paste a JSON array with <code>input</code> and <code>reference_output</code> fields.</p>
          <el-input
            v-model="casesJson"
            type="textarea"
            :rows="5"
            placeholder='[{"input": "Question?", "reference_output": "Answer."}]'
            style="font-size:14px"
            :input-style="{ minHeight: '120px' }"
          />
          <p v-if="jsonError" class="json-error">{{ jsonError }}</p>
          <div style="margin-top:10px;display:flex;justify-content:flex-end">
            <el-button type="primary" :loading="uploading" @click="handleUpload" style="background:var(--matcha-600);border-color:var(--matcha-600);padding:8px 20px;font-size:14px">
              Upload
            </el-button>
          </div>
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
import { useDatasetsStore } from '@/stores/datasets'
import type { Dataset } from '@/types'

const store = useDatasetsStore()
onMounted(() => store.fetchAll())

type PanelMode = 'placeholder' | 'create' | 'detail'
const panelMode = ref<PanelMode>('placeholder')
const selectedDataset = ref<Dataset | null>(null)
const loadingCases = ref(false)

const currentCases = computed(() =>
  selectedDataset.value ? (store.casesByDataset[selectedDataset.value.id] ?? []) : [],
)

function caseCount(datasetId: number): string {
  const cases = store.casesByDataset[datasetId]
  if (!cases) return ''
  return `${cases.length} ${cases.length === 1 ? 'case' : 'cases'}`
}

async function selectDataset(ds: Dataset) {
  selectedDataset.value = ds
  panelMode.value = 'detail'
  if (!store.casesByDataset[ds.id]) {
    loadingCases.value = true
    try {
      await store.fetchCases(ds.id)
    } finally {
      loadingCases.value = false
    }
  }
}

function showCreate() {
  selectedDataset.value = null
  createForm.name = ''
  createForm.description = ''
  panelMode.value = 'create'
}

function closePanel() {
  panelMode.value = selectedDataset.value ? 'detail' : 'placeholder'
}

// Create form
const createFormRef = ref<FormInstance>()
const saving = ref(false)
const createForm = reactive({ name: '', description: '' })
const createRules: FormRules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
}

async function handleCreate() {
  await createFormRef.value?.validate()
  saving.value = true
  try {
    const ds = await store.create({ name: createForm.name, description: createForm.description || undefined })
    ElMessage({ type: 'success', message: 'Dataset created' })
    await selectDataset(ds)
  } finally {
    saving.value = false
  }
}

// Upload cases
const casesJson = ref('')
const jsonError = ref('')
const uploading = ref(false)

async function handleUpload() {
  jsonError.value = ''
  let cases: { input: string; reference_output: string }[]
  try {
    cases = JSON.parse(casesJson.value)
    if (!Array.isArray(cases)) throw new Error('Must be a JSON array')
  } catch (e) {
    jsonError.value = e instanceof Error ? e.message : 'Invalid JSON'
    return
  }
  uploading.value = true
  try {
    const result = await store.uploadCases(selectedDataset.value!.id, cases)
    ElMessage({ type: 'success', message: `Uploaded ${result.length} cases` })
    casesJson.value = ''
  } finally {
    uploading.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.new-btn {
  display: block;
  width: 100%;
  padding: 12px 0;
  margin-bottom: 14px;
  border: 1px solid var(--matcha-400);
  border-radius: 8px;
  background: transparent;
  color: var(--matcha-600);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.new-btn:hover { background: var(--matcha-50); }

.item-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }

.item-row {
  padding: 14px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}
.item-row:hover { background: var(--matcha-50); }
.item-row.active {
  background: var(--matcha-50);
  border-left-color: var(--matcha-600);
}

.item-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.item-name { font-size: 15px; font-weight: 500; color: var(--text-primary); }
.item-meta { font-size: 13px; color: var(--text-secondary); }
.item-sub { font-size: 13px; color: var(--text-secondary); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Panel form */
.panel-form { max-width: 520px; }
.panel-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.panel-form-title { font-size: 22px; font-weight: 500; color: var(--text-primary); }
.close-btn {
  width: 28px; height: 28px;
  border: none; background: none; cursor: pointer;
  font-size: 18px; color: var(--text-secondary);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
}
.close-btn:hover { background: var(--matcha-50); color: var(--text-primary); }
.panel-form-actions { display: flex; justify-content: flex-end; margin-top: 16px; }
.panel-form-actions :deep(.el-button) { padding: 9px 24px; font-size: 14px; }

/* Detail panel */
.panel-detail { max-width: 640px; }
.detail-header { margin-bottom: 20px; }
.detail-title { font-size: 24px; font-weight: 500; margin-bottom: 4px; }
.detail-desc { font-size: 15px; color: var(--text-secondary); margin-bottom: 4px; }
.detail-date { font-size: 13px; color: var(--text-secondary); }

.cases-section { margin-top: 24px; margin-bottom: 20px; }
.cases-header { display: flex; align-items: center; margin-bottom: 12px; }
.cases-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }

.cases-list { display: flex; flex-direction: column; gap: 8px; }
.case-card {
  padding: 16px 20px;
  border: 0.5px solid var(--border);
  border-radius: 10px;
  background: var(--card);
  margin-bottom: 10px;
}
.case-input { font-size: 15px; font-weight: 500; color: var(--text-primary); margin-bottom: 4px; }
.case-ref { font-size: 14px; color: var(--text-secondary); margin-top: 6px; }

.divider { height: 0.5px; background: var(--border); margin: 20px 0; }

.upload-section { margin-top: 28px; }
.upload-hint { font-size: 14px; color: var(--text-secondary); margin: 6px 0 8px; }
.upload-hint code { background: var(--matcha-50); padding: 1px 4px; border-radius: 3px; }
.json-error { font-size: 12px; color: #8B2E2E; margin-top: 4px; }
</style>
