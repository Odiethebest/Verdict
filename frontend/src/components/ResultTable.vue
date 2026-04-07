<template>
  <div>
    <!-- Filter bar -->
    <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
      <span style="font-size:13px;color:var(--text-secondary)">Variant:</span>
      <el-select v-model="filterVariantId" placeholder="All" clearable style="width:160px">
        <el-option
          v-for="v in variants"
          :key="v.id"
          :label="v.name"
          :value="v.id"
        />
      </el-select>
    </div>

    <el-table
      :data="filteredResults"
      row-key="id"
      style="width:100%"
      :expand-row-keys="expandedRows"
      @row-click="toggleRow"
    >
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-content">
            <div class="expand-output">
              <div class="expand-label">Raw output</div>
              <p>{{ (row as EvalResult).raw_output }}</p>
            </div>
            <div v-if="(row as EvalResult).dimension_scores.length" class="expand-dims">
              <div class="expand-label">Dimension scores</div>
              <div v-for="ds in (row as EvalResult).dimension_scores" :key="ds.id" class="dim-score-row">
                <div class="dim-score-header">
                  <span>Dimension #{{ ds.dimension_id }}</span>
                  <span :class="['score-pill', scorePillClass(ds.score)]">{{ ds.score.toFixed(2) }}</span>
                </div>
                <div class="dim-bar-track">
                  <div class="dim-bar-fill" :style="{ width: `${ds.score * 100}%` }" />
                </div>
                <p v-if="ds.reasoning" class="dim-reasoning">{{ ds.reasoning }}</p>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="Variant" width="130">
        <template #default="{ row }">
          <span class="badge">{{ variantName((row as EvalResult).variant_id) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="Input" min-width="180">
        <template #default="{ row }">
          <el-tooltip :content="getInput((row as EvalResult).test_case_id)" placement="top" :show-after="300">
            <span class="truncate-cell">{{ getInput((row as EvalResult).test_case_id) }}</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column label="ROUGE" width="80" align="center">
        <template #default="{ row }">
          <span v-if="(row as EvalResult).rouge_score != null" :class="['score-pill', scorePillClass((row as EvalResult).rouge_score!)]">
            {{ (row as EvalResult).rouge_score!.toFixed(2) }}
          </span>
          <span v-else class="score-pill none">—</span>
        </template>
      </el-table-column>

      <el-table-column label="Judge" width="80" align="center">
        <template #default="{ row }">
          <span v-if="(row as EvalResult).judge_score != null" :class="['score-pill', scorePillClass((row as EvalResult).judge_score!)]">
            {{ (row as EvalResult).judge_score!.toFixed(2) }}
          </span>
          <span v-else class="score-pill none">—</span>
        </template>
      </el-table-column>

      <el-table-column label="Human" width="130" align="center">
        <template #default="{ row }">
          <el-input-number
            v-model="(row as EvalResult).human_score"
            :min="0"
            :max="1"
            :step="0.01"
            :precision="2"
            :placeholder="!(row as EvalResult).human_score ? '—' : undefined"
            size="small"
            style="width:100px"
            @change="(val: number | null) => onFeedbackChange(row as EvalResult, val)"
          />
        </template>
      </el-table-column>

      <el-table-column label="Golden" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="(row as EvalResult).is_golden"
            :active-color="'var(--matcha-600)'"
            @change="(val: boolean) => onGoldenChange(row as EvalResult, val)"
          />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { EvalResult, Variant, TestCase } from '@/types'
import { submitFeedback } from '@/api/results'

const props = defineProps<{
  results: EvalResult[]
  variants: Variant[]
  testCases: TestCase[]
}>()

const filterVariantId = ref<number | null>(null)
const expandedRows = ref<string[]>([])

const filteredResults = computed(() =>
  filterVariantId.value
    ? props.results.filter((r) => r.variant_id === filterVariantId.value)
    : props.results,
)

function toggleRow(row: EvalResult) {
  const key = String(row.id)
  const idx = expandedRows.value.indexOf(key)
  if (idx === -1) expandedRows.value.push(key)
  else expandedRows.value.splice(idx, 1)
}

function variantName(variantId: number) {
  return props.variants.find((v) => v.id === variantId)?.name ?? `#${variantId}`
}

function getInput(testCaseId: number) {
  return props.testCases.find((t) => t.id === testCaseId)?.input ?? ''
}

function scorePillClass(score: number) {
  if (score >= 0.6) return 'high'
  if (score >= 0.3) return 'mid'
  return 'low'
}

async function onFeedbackChange(row: EvalResult, val: number | null) {
  if (val === null) return
  await submitFeedback(row.id, { human_score: val, is_golden: row.is_golden })
}

async function onGoldenChange(row: EvalResult, val: boolean) {
  if (val && (!row.human_score || row.human_score <= 0)) {
    ElMessage({ type: 'warning', message: 'Set a human score before marking as golden' })
    row.is_golden = false
    return
  }
  await submitFeedback(row.id, { human_score: row.human_score ?? 0, is_golden: val })
}
</script>

<style scoped>
.truncate-cell {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
  font-size: 13px;
}

.expand-content {
  padding: 14px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.expand-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.expand-output p {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.dim-score-row { margin-bottom: 10px; }

.dim-score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 13px;
}

.dim-bar-track {
  height: 6px;
  background: var(--matcha-100);
  border-radius: 3px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  background: var(--matcha-400);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.dim-reasoning {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  line-height: 1.5;
}
</style>
