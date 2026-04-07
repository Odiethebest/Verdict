<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Dimensions</h1>
      <el-button type="primary" @click="openForm()" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        New dimension
      </el-button>
    </div>

    <!-- Weight warning -->
    <el-alert
      v-if="totalWeight > 1.001"
      type="warning"
      :closable="false"
      style="margin-bottom:16px;border-radius:8px"
      :title="`Total weight is ${(totalWeight * 100).toFixed(0)}% — consider normalizing to 100%`"
      show-icon
    />

    <!-- Loading -->
    <div v-if="store.loading" style="display:flex;flex-direction:column;gap:12px">
      <el-skeleton v-for="i in 3" :key="i" animated class="card">
        <template #template>
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <el-skeleton-item variant="h3" style="width:40%" />
            <el-skeleton-item variant="button" style="width:60px" />
          </div>
          <el-skeleton-item variant="text" style="width:100%" />
          <el-skeleton-item variant="text" style="width:80%" />
        </template>
      </el-skeleton>
    </div>

    <!-- Empty state -->
    <div v-else-if="store.dimensions.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
      </svg>
      <p>No dimensions defined — create a scoring rubric</p>
      <el-button type="primary" @click="openForm()" style="background:var(--matcha-600);border-color:var(--matcha-600)">
        Create dimension
      </el-button>
    </div>

    <!-- Dimension list -->
    <div v-else style="display:flex;flex-direction:column;gap:12px">
      <div v-for="dim in store.dimensions" :key="dim.id" class="card dim-card">
        <div class="dim-header">
          <div style="display:flex;align-items:center;gap:10px">
            <span class="dim-name">{{ dim.name }}</span>
            <span class="badge">{{ (dim.weight * 100).toFixed(0) }}%</span>
          </div>
          <div class="dim-actions">
            <button class="icon-btn" title="Edit" @click="openForm(dim)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <el-popconfirm title="Delete this dimension?" confirm-button-text="Delete" cancel-button-text="Cancel" @confirm="handleDelete(dim.id)">
              <template #reference>
                <button class="icon-btn danger" title="Delete">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                  </svg>
                </button>
              </template>
            </el-popconfirm>
          </div>
        </div>
        <p class="dim-prompt">{{ dim.scorer_prompt }}</p>
      </div>
    </div>

    <!-- Create / Edit dialog -->
    <el-dialog
      v-model="showForm"
      :title="editingId ? 'Edit dimension' : 'New dimension'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="e.g. Accuracy" />
        </el-form-item>
        <el-form-item label="Weight" prop="weight">
          <el-input-number
            v-model="form.weight"
            :min="0.01"
            :max="1.0"
            :step="0.01"
            :precision="2"
            style="width:100%"
          />
          <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">
            Value between 0.01 and 1.00
          </div>
        </el-form-item>
        <el-form-item label="Scorer prompt" prop="scorer_prompt">
          <el-input
            v-model="form.scorer_prompt"
            type="textarea"
            :rows="4"
            placeholder="Score the factual accuracy of the answer from 0.0 to 1.0 where 1.0 means fully accurate..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave" style="background:var(--matcha-600);border-color:var(--matcha-600)">
          {{ editingId ? 'Save' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useDimensionsStore } from '@/stores/dimensions'
import type { Dimension } from '@/types'

const store = useDimensionsStore()
onMounted(() => store.fetchAll())

const totalWeight = computed(() =>
  store.dimensions.reduce((sum, d) => sum + d.weight, 0),
)

const showForm = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({ name: '', weight: 0.5, scorer_prompt: '' })

const rules: FormRules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  weight: [{ required: true, message: 'Weight is required', trigger: 'blur' }],
  scorer_prompt: [{ required: true, message: 'Scorer prompt is required', trigger: 'blur' }],
}

function openForm(dim?: Dimension) {
  editingId.value = dim?.id ?? null
  form.name = dim?.name ?? ''
  form.weight = dim?.weight ?? 0.5
  form.scorer_prompt = dim?.scorer_prompt ?? ''
  showForm.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingId.value) {
      await store.update(editingId.value, { name: form.name, weight: form.weight, scorer_prompt: form.scorer_prompt })
      ElMessage({ type: 'success', message: 'Dimension updated' })
    } else {
      await store.create({ name: form.name, weight: form.weight, scorer_prompt: form.scorer_prompt })
      ElMessage({ type: 'success', message: 'Dimension created' })
    }
    showForm.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await store.remove(id)
  ElMessage({ type: 'success', message: 'Dimension deleted' })
}
</script>

<style scoped>
.dim-card { transition: box-shadow 0.15s; }
.dim-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }

.dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.dim-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.dim-prompt {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dim-actions { display: flex; gap: 6px; }

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
  transition: background 0.1s, color 0.1s;
}
.icon-btn:hover       { background: var(--matcha-50); color: var(--matcha-600); }
.icon-btn.danger:hover { background: #FDEAEA; color: #8B2E2E; }
</style>
