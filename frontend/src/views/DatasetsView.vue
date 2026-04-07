<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Datasets</h1>
      <el-button type="primary" @click="showCreate = true" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        New dataset
      </el-button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="grid-2">
      <el-skeleton v-for="i in 3" :key="i" animated class="card" style="padding:20px">
        <template #template>
          <el-skeleton-item variant="h3" style="width:60%;margin-bottom:8px" />
          <el-skeleton-item variant="text" style="width:90%" />
          <el-skeleton-item variant="text" style="width:40%;margin-top:12px" />
        </template>
      </el-skeleton>
    </div>

    <!-- Empty state -->
    <div v-else-if="store.datasets.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
      <p>No datasets yet — upload your first test cases</p>
      <el-button type="primary" @click="showCreate = true" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        Create dataset
      </el-button>
    </div>

    <!-- Dataset grid -->
    <div v-else class="grid-2">
      <div v-for="ds in store.datasets" :key="ds.id" class="card">
        <div class="ds-header">
          <span class="ds-name">{{ ds.name }}</span>
          <span class="ds-date">{{ formatDate(ds.created_at) }}</span>
        </div>
        <p v-if="ds.description" class="ds-desc">{{ ds.description }}</p>
        <div class="ds-footer">
          <el-button size="small" @click="openUpload(ds)">Upload cases</el-button>
        </div>
      </div>
    </div>

    <!-- Create dialog -->
    <el-dialog v-model="showCreate" title="New dataset" width="480px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-position="top">
        <el-form-item label="Name" prop="name">
          <el-input v-model="createForm.name" placeholder="e.g. RAG Q&A v1" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="Optional" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">Cancel</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate" style="background:var(--matcha-600);border-color:var(--matcha-600)">
          Create
        </el-button>
      </template>
    </el-dialog>

    <!-- Upload cases dialog -->
    <el-dialog v-model="showUpload" :title="`Upload cases — ${activeDataset?.name}`" width="560px" :close-on-click-modal="false">
      <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
        Paste a JSON array of objects with <code>input</code> and <code>reference_output</code> fields.
      </p>
      <el-input
        v-model="casesJson"
        type="textarea"
        :rows="10"
        placeholder='[{"input": "Question?", "reference_output": "Answer."}]'
        :class="{ 'is-error': jsonError }"
      />
      <p v-if="jsonError" style="color:#8B2E2E;font-size:12px;margin-top:6px">{{ jsonError }}</p>
      <template #footer>
        <el-button @click="showUpload = false">Cancel</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload" style="background:var(--matcha-600);border-color:var(--matcha-600)">
          Upload
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useDatasetsStore } from '@/stores/datasets'
import type { Dataset } from '@/types'

const store = useDatasetsStore()

onMounted(() => store.fetchAll())

const showCreate = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({ name: '', description: '' })
const createRules: FormRules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
}

async function handleCreate() {
  await createFormRef.value?.validate()
  creating.value = true
  try {
    await store.create({ name: createForm.name, description: createForm.description || undefined })
    ElMessage({ type: 'success', message: 'Dataset created' })
    showCreate.value = false
    createForm.name = ''
    createForm.description = ''
  } finally {
    creating.value = false
  }
}

const showUpload = ref(false)
const uploading = ref(false)
const activeDataset = ref<Dataset | null>(null)
const casesJson = ref('')
const jsonError = ref('')

function openUpload(ds: Dataset) {
  activeDataset.value = ds
  casesJson.value = ''
  jsonError.value = ''
  showUpload.value = true
}

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
    const result = await store.uploadCases(activeDataset.value!.id, cases)
    ElMessage({ type: 'success', message: `Uploaded ${result.length} cases` })
    showUpload.value = false
  } finally {
    uploading.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.ds-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.ds-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.ds-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.ds-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 14px;
  line-height: 1.5;
}

.ds-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 0.5px solid var(--border);
}

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
