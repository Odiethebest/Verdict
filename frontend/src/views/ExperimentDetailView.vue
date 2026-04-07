<template>
  <div class="page">
    <!-- Loading skeleton -->
    <div v-if="loading">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="h3" style="width:40%;margin-bottom:24px" />
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px">
            <el-skeleton-item v-for="i in 4" :key="i" variant="rect" style="height:90px;border-radius:12px" />
          </div>
        </template>
      </el-skeleton>
    </div>

    <template v-else-if="experiment">
      <!-- Breadcrumb + actions -->
      <div class="topbar">
        <div class="breadcrumb">
          <RouterLink to="/experiments" class="breadcrumb-link">Experiments</RouterLink>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">{{ experiment.name }}</span>
        </div>
        <div class="topbar-right">
          <span v-if="experiment.status === 'failed'" style="margin-right:8px">
            <el-alert type="error" :closable="false" title="Run failed — check server logs" style="padding:4px 10px;border-radius:6px" />
          </span>
          <span :class="['status-badge', experiment.status]">
            <span v-if="experiment.status === 'running'" class="pulse-dot" />
            {{ experiment.status }}
          </span>
          <el-tooltip
            :content="experiment.status === 'running' ? 'Already running' : ''"
            :disabled="experiment.status === 'pending'"
          >
            <el-button
              type="primary"
              :disabled="experiment.status !== 'pending'"
              :loading="triggering"
              @click="handleRun"
              style="background:var(--matcha-600);border-color:var(--matcha-600)"
            >
              Run
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <!-- Metric cards -->
      <div class="metrics-grid">
        <div class="card metric-card">
          <div class="metric-label">Variants</div>
          <div class="metric-value">{{ (experiment.variants ?? []).length }}</div>
        </div>
        <div class="card metric-card">
          <div class="metric-label">Test cases</div>
          <div class="metric-value">{{ totalCases }}</div>
        </div>
        <div class="card metric-card">
          <div class="metric-label">Dimensions</div>
          <div class="metric-value">—</div>
        </div>
        <div class="metric-card accent-card">
          <div class="metric-label" style="color:rgba(255,255,255,0.75)">Best score</div>
          <div class="metric-value" style="color:white">
            {{ bestScore }}
          </div>
          <div v-if="bestVariantName" style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:2px">
            {{ bestVariantName }}
          </div>
        </div>
      </div>

      <!-- Two-column area -->
      <div class="two-col">
        <!-- Left panel -->
        <div style="display:flex;flex-direction:column;gap:16px">
          <!-- Leaderboard -->
          <div class="card">
            <div class="section-title">Leaderboard</div>
            <div v-if="(experiment.leaderboard ?? []).length === 0" style="color:var(--text-secondary);font-size:13px;padding:8px 0">
              No results yet
            </div>
            <div v-else class="leaderboard-list">
              <div
                v-for="entry in experiment.leaderboard"
                :key="entry.variant_id"
                class="lb-row"
              >
                <div class="lb-meta">
                  <span class="lb-rank">#{{ entry.rank }}</span>
                  <span class="lb-name">{{ entry.variant_name }}</span>
                </div>
                <div class="lb-bar-track">
                  <div
                    class="lb-bar-fill"
                    :class="{ top: entry.rank === 1 }"
                    :style="{ width: animateBars ? `${entry.aggregate_score * 100}%` : '0%' }"
                  />
                </div>
                <span class="lb-score">{{ entry.aggregate_score.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- Progress -->
          <div class="card">
            <div class="section-title">Run progress</div>
            <div v-if="(experiment.variants ?? []).length === 0" style="color:var(--text-secondary);font-size:13px">
              No variants
            </div>
            <div v-else style="display:flex;flex-direction:column;gap:10px">
              <div v-for="v in experiment.variants" :key="v.id">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                  <span style="color:var(--text-primary)">{{ v.name }}</span>
                  <span style="color:var(--text-secondary)">
                    {{ progress[v.id]?.completed ?? 0 }} / {{ progress[v.id]?.total ?? totalCases }}
                  </span>
                </div>
                <el-progress
                  :percentage="progressPct(v.id)"
                  :stroke-width="6"
                  :show-text="false"
                  :color="experiment.status === 'completed' ? 'var(--matcha-600)' : 'var(--matcha-400)'"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Right panel: results table -->
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
            <div class="section-title" style="margin-bottom:0">Results</div>
            <el-button
              v-if="experiment.status === 'completed'"
              size="small"
              @click="handleExport"
              :loading="exporting"
            >
              Export {{ goldenCount }} golden {{ goldenCount === 1 ? 'sample' : 'samples' }}
            </el-button>
          </div>
          <ResultTable
            v-if="results.length > 0"
            :results="results"
            :variants="experiment.variants ?? []"
            :test-cases="testCases"
          />
          <div v-else style="color:var(--text-secondary);font-size:13px;padding:16px 0">
            No results yet — trigger a run to generate scores.
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>Experiment not found.</p>
      <el-button @click="$router.push('/experiments')">Back</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { Experiment, EvalResult, TestCase } from '@/types'
import * as experimentsApi from '@/api/experiments'
import { listCases } from '@/api/datasets'
import { useRunProgress } from '@/composables/useRunProgress'
import ResultTable from '@/components/ResultTable.vue'

const route = useRoute()
const experimentId = Number(route.params.id)

const experiment = ref<Experiment | null>(null)
const results = ref<EvalResult[]>([])
const testCases = ref<TestCase[]>([])
const loading = ref(true)
const triggering = ref(false)
const exporting = ref(false)
const animateBars = ref(false)

const { progress, start: startSSE, stop: stopSSE } = useRunProgress(experimentId)

// Total cases for progress display
const totalCases = computed(() => {
  const vals = Object.values(progress.value)
  if (vals.length > 0 && vals[0].total) return vals[0].total
  return testCases.value.length
})

const bestScore = computed(() => {
  const lb = experiment.value?.leaderboard ?? []
  if (lb.length === 0) return '—'
  return lb[0].aggregate_score.toFixed(2)
})

const bestVariantName = computed(() => {
  const lb = experiment.value?.leaderboard ?? []
  return lb.length > 0 ? lb[0].variant_name : null
})

const goldenCount = computed(() => results.value.filter((r) => r.is_golden).length)

function progressPct(variantId: number) {
  const p = progress.value[variantId]
  if (!p || !p.total) return 0
  return Math.round((p.completed / p.total) * 100)
}

async function load() {
  loading.value = true
  try {
    experiment.value = await experimentsApi.getExperiment(experimentId)
    if (experiment.value?.dataset_id) {
      testCases.value = await listCases(experiment.value.dataset_id)
    }
    if (experiment.value?.status === 'completed' || experiment.value?.status === 'failed') {
      results.value = await experimentsApi.getResults(experimentId)
    }
    await nextTick()
    setTimeout(() => { animateBars.value = true }, 100)
  } finally {
    loading.value = false
  }
}

async function handleRun() {
  triggering.value = true
  try {
    await experimentsApi.triggerRun(experimentId)
    ElMessage({ type: 'success', message: 'Run started' })
    experiment.value!.status = 'running'
    startSSE()
    pollStatus()
  } finally {
    triggering.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const blob = await experimentsApi.exportGolden(experimentId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `golden_${experimentId}.jsonl`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

let statusPoller: ReturnType<typeof setInterval> | null = null

function pollStatus() {
  if (statusPoller) return
  statusPoller = setInterval(async () => {
    const updated = await experimentsApi.getExperiment(experimentId)
    experiment.value = updated
    if (updated.status === 'completed' || updated.status === 'failed') {
      clearInterval(statusPoller!)
      statusPoller = null
      stopSSE()
      if (updated.status === 'completed') {
        results.value = await experimentsApi.getResults(experimentId)
        animateBars.value = false
        await nextTick()
        setTimeout(() => { animateBars.value = true }, 100)
      }
    }
  }, 2000)
}

onMounted(() => {
  load()
  // If already running, connect SSE immediately
  watch(
    () => experiment.value?.status,
    (status) => {
      if (status === 'running') {
        startSSE()
        pollStatus()
      }
    },
    { immediate: true },
  )
})
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}
.breadcrumb-link { color: var(--text-secondary); text-decoration: none; }
.breadcrumb-link:hover { color: var(--matcha-600); }
.breadcrumb-sep { color: var(--border); }
.breadcrumb-current { font-weight: 600; color: var(--text-primary); }

.topbar-right { display: flex; align-items: center; gap: 10px; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  padding: 18px 20px;
  border-radius: 12px;
  border: 0.5px solid var(--border);
  background: var(--card);
}

.accent-card {
  padding: 18px 20px;
  border-radius: 12px;
  background: var(--matcha-600);
  border: none;
}

.metric-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.two-col {
  display: grid;
  grid-template-columns: 38% 1fr;
  gap: 16px;
  align-items: start;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 14px;
}

.leaderboard-list { display: flex; flex-direction: column; gap: 10px; }

.lb-row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  row-gap: 4px;
  column-gap: 10px;
}

.lb-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  grid-column: 1;
  grid-row: 1;
}
.lb-rank { color: var(--text-secondary); font-size: 11px; }
.lb-name { font-weight: 500; }

.lb-bar-track {
  height: 8px;
  background: var(--matcha-100);
  border-radius: 4px;
  overflow: hidden;
  grid-column: 1;
  grid-row: 2;
}
.lb-bar-fill {
  height: 100%;
  background: var(--matcha-200);
  border-radius: 4px;
  transition: width 0.6s ease;
}
.lb-bar-fill.top { background: var(--matcha-400); }

.lb-score {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  grid-column: 2;
  grid-row: 1 / 3;
  align-self: center;
}

@media (max-width: 900px) {
  .two-col { grid-template-columns: 1fr; }
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
