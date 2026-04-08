<template>
  <div class="exp-detail-page">
    <!-- Loading -->
    <div v-if="loading" class="page-inner">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="h3" style="width:40%;margin-bottom:24px" />
          <div style="display:flex;gap:12px;margin-bottom:28px">
            <el-skeleton-item v-for="i in 4" :key="i" variant="rect" style="height:72px;border-radius:10px;flex:1" />
          </div>
          <el-skeleton-item variant="rect" style="height:120px;border-radius:10px;margin-bottom:16px" />
          <el-skeleton-item variant="rect" style="height:200px;border-radius:10px" />
        </template>
      </el-skeleton>
    </div>

    <template v-else-if="experiment">
      <div class="page-inner">
        <!-- Topbar -->
        <div class="topbar">
          <div class="breadcrumb">
            <RouterLink to="/experiments" class="breadcrumb-link">Experiments</RouterLink>
            <span class="breadcrumb-sep">/</span>
            <span class="breadcrumb-current">{{ experiment.name }}</span>
          </div>
          <div class="topbar-right">
            <el-alert
              v-if="experiment.status === 'failed'"
              type="error"
              :closable="false"
              title="Run failed — check server logs"
              style="padding:4px 10px;border-radius:6px;margin-right:8px"
            />
            <span :class="['status-badge', experiment.status]">
              <span v-if="experiment.status === 'running'" class="pulse-dot" />
              {{ experiment.status }}
            </span>
            <el-tooltip :content="experiment.status === 'running' ? 'Already running' : ''">
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

        <!-- Metric chips (single row) -->
        <div class="metric-chips">
          <div class="chip">
            <span class="chip-label">Variants</span>
            <span class="chip-value">{{ (experiment.variants ?? []).length }}</span>
          </div>
          <div class="chip">
            <span class="chip-label">Test cases</span>
            <span class="chip-value">{{ testCases.length }}</span>
          </div>
          <div class="chip">
            <span class="chip-label">Dimensions</span>
            <span class="chip-value">{{ dimensionCount }}</span>
          </div>
          <div class="chip chip-accent">
            <span class="chip-label" style="color:rgba(255,255,255,0.75)">Best score</span>
            <span class="chip-value" style="color:white">{{ bestScore }}</span>
            <span v-if="bestVariantName" class="chip-sub">{{ bestVariantName }}</span>
          </div>
        </div>

        <!-- Leaderboard section -->
        <div class="section-card">
          <div class="section-head">Leaderboard</div>
          <div v-if="(experiment.leaderboard ?? []).length === 0" class="section-empty">
            No results yet
          </div>
          <div v-else class="lb-list">
            <div v-for="entry in experiment.leaderboard" :key="entry.variant_id" class="lb-row">
              <div class="lb-rank-name">
                <span class="lb-rank">#{{ entry.rank }}</span>
                <span class="lb-name">{{ entry.variant_name }}</span>
              </div>
              <div class="lb-bar-wrap">
                <div class="lb-bar-track">
                  <div
                    class="lb-bar-fill"
                    :class="{ top: entry.rank === 1 }"
                    :style="{ width: animateBars ? `${entry.aggregate_score * 100}%` : '0%' }"
                  />
                </div>
              </div>
              <span class="lb-score">{{ entry.aggregate_score.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- Run progress (running only) -->
        <div v-if="experiment.status === 'running'" class="section-card">
          <div class="section-head">Run progress</div>
          <div v-for="v in (experiment.variants ?? [])" :key="v.id" class="progress-row">
            <div class="progress-meta">
              <span>{{ v.name }}</span>
              <span class="progress-count">{{ sseProgress[v.id]?.completed ?? 0 }} / {{ sseProgress[v.id]?.total ?? testCases.length }}</span>
            </div>
            <el-progress
              :percentage="progressPct(v.id)"
              :stroke-width="6"
              :show-text="false"
              color="var(--matcha-400)"
            />
          </div>
        </div>

        <!-- Dimension breakdown (completed only) -->
        <div v-if="experiment.status === 'completed' && dimensionBreakdown.length > 0" class="section-card">
          <div class="section-head">Dimension breakdown</div>
          <div
            class="breakdown-grid"
            :style="{ gridTemplateColumns: `200px ${(experiment.variants ?? []).map(() => '1fr').join(' ')}` }"
          >
            <!-- Header row -->
            <div class="breakdown-dim-label" />
            <div
              v-for="v in (experiment.variants ?? [])"
              :key="v.id"
              class="breakdown-variant-header"
            >
              {{ v.name }}
            </div>
            <!-- Data rows -->
            <template v-for="row in dimensionBreakdown" :key="row.dimensionId">
              <div class="breakdown-dim-label">{{ row.dimensionName }}</div>
              <div
                v-for="v in (experiment.variants ?? [])"
                :key="v.id"
                class="breakdown-cell"
              >
                <div class="bd-bar-track">
                  <div
                    class="bd-bar-fill"
                    :style="{ width: `${(row.scores[v.id] ?? 0) * 100}%` }"
                  />
                </div>
                <span class="bd-score">{{ row.scores[v.id] != null ? row.scores[v.id]!.toFixed(2) : '—' }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Results table -->
        <div class="section-card">
          <div class="section-head-row">
            <span class="section-head" style="margin-bottom:0">Results</span>
            <el-button
              v-if="experiment.status === 'completed'"
              size="small"
              :loading="exporting"
              @click="handleExport"
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
          <div v-else class="section-empty">
            No results yet — trigger a run to generate scores.
          </div>
        </div>
      </div>
    </template>

    <div v-else class="page-inner empty-state">
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

const { progress: sseProgress, start: startSSE, stop: stopSSE } = useRunProgress(experimentId)

// Derive completed-state progress from results
const progressFromResults = computed(() => {
  if (experiment.value?.status !== 'completed') return {}
  const map: Record<number, number> = {}
  for (const r of results.value) map[r.variant_id] = (map[r.variant_id] ?? 0) + 1
  return map
})

function progressPct(variantId: number) {
  const total = testCases.value.length
  if (!total) return 0
  const p = sseProgress.value[variantId]
  if (!p) return 0
  return Math.round((p.completed / p.total) * 100)
}

const dimensionCount = computed(() => {
  if (!results.value.length) return '—'
  const ids = new Set<number>()
  for (const r of results.value) for (const ds of r.dimension_scores) ids.add(ds.dimension_id)
  return ids.size || '—'
})

const bestScore = computed(() => {
  const lb = experiment.value?.leaderboard ?? []
  return lb.length ? lb[0].aggregate_score.toFixed(2) : '—'
})
const bestVariantName = computed(() => {
  const lb = experiment.value?.leaderboard ?? []
  return lb.length ? lb[0].variant_name : null
})

const goldenCount = computed(() => results.value.filter((r) => r.is_golden).length)

// Dimension breakdown: per-dimension, per-variant average scores
const dimensionBreakdown = computed(() => {
  if (!results.value.length) return []
  const dimMap: Record<number, { dimensionId: number; dimensionName: string; scores: Record<number, number[]> }> = {}
  for (const r of results.value) {
    for (const ds of r.dimension_scores) {
      if (!dimMap[ds.dimension_id]) {
        dimMap[ds.dimension_id] = { dimensionId: ds.dimension_id, dimensionName: `Dimension ${ds.dimension_id}`, scores: {} }
      }
      if (!dimMap[ds.dimension_id].scores[r.variant_id]) {
        dimMap[ds.dimension_id].scores[r.variant_id] = []
      }
      dimMap[ds.dimension_id].scores[r.variant_id].push(ds.score)
    }
  }
  // Average scores per variant per dimension
  return Object.values(dimMap).map((d) => ({
    dimensionId: d.dimensionId,
    dimensionName: d.dimensionName,
    scores: Object.fromEntries(
      Object.entries(d.scores).map(([vid, scores]) => [
        Number(vid),
        scores.reduce((a, b) => a + b, 0) / scores.length,
      ]),
    ) as Record<number, number>,
  }))
})

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
.exp-detail-page {
  height: 100%;
  overflow-y: auto;
  background: var(--cream);
}
.page-inner {
  width: 100%;
  padding: 28px 36px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}
.breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 15px; }
.breadcrumb-link { color: var(--text-secondary); text-decoration: none; }
.breadcrumb-link:hover { color: var(--matcha-600); }
.breadcrumb-sep { color: var(--border); }
.breadcrumb-current { font-weight: 600; color: var(--text-primary); }
.topbar-right { display: flex; align-items: center; gap: 10px; }

/* Metric chips */
.metric-chips {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.chip {
  flex: 1;
  min-width: 120px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.chip-accent {
  background: var(--matcha-600);
  border-color: transparent;
}
.chip-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}
.chip-value {
  font-size: 28px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1;
}
.chip-sub {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  margin-top: 2px;
}

/* Sections */
.section-card {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.section-head {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.section-head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.section-empty { font-size: 13px; color: var(--text-secondary); padding: 8px 0; }

/* Leaderboard */
.lb-list { display: flex; flex-direction: column; gap: 12px; }
.lb-row {
  display: grid;
  grid-template-columns: 180px 1fr 48px;
  align-items: center;
  gap: 12px;
}
.lb-rank-name { display: flex; align-items: center; gap: 6px; }
.lb-rank { font-size: 11px; color: var(--text-secondary); min-width: 20px; }
.lb-name { font-size: 13px; font-weight: 500; }
.lb-bar-wrap { flex: 1; }
.lb-bar-track { height: 10px; background: var(--matcha-100); border-radius: 5px; overflow: hidden; }
.lb-bar-fill  { height: 100%; background: var(--matcha-200); border-radius: 5px; transition: width 0.6s ease; }
.lb-bar-fill.top { background: var(--matcha-400); }
.lb-score { font-size: 13px; font-weight: 600; text-align: right; }

/* Run progress */
.progress-row { margin-bottom: 10px; }
.progress-meta { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
.progress-count { color: var(--text-secondary); }

/* Dimension breakdown */
.breakdown-grid {
  display: grid;
  gap: 8px 16px;
  align-items: center;
}
.breakdown-dim-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.breakdown-variant-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
}
.breakdown-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bd-bar-track {
  flex: 1;
  height: 8px;
  background: var(--matcha-100);
  border-radius: 4px;
  overflow: hidden;
}
.bd-bar-fill {
  height: 100%;
  background: var(--matcha-400);
  border-radius: 4px;
  transition: width 0.4s ease;
}
.bd-score { font-size: 12px; font-weight: 600; min-width: 32px; text-align: right; }
</style>
