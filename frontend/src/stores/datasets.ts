import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Dataset, TestCase } from '@/types'
import * as api from '@/api/datasets'

export const useDatasetsStore = defineStore('datasets', () => {
  const datasets = ref<Dataset[]>([])
  const loading = ref(false)
  const casesByDataset = ref<Record<number, TestCase[]>>({})

  async function fetchAll() {
    loading.value = true
    try {
      datasets.value = await api.listDatasets()
    } finally {
      loading.value = false
    }
  }

  async function fetchCases(datasetId: number) {
    const cases = await api.listCases(datasetId)
    casesByDataset.value[datasetId] = cases
    return cases
  }

  async function create(payload: { name: string; description?: string }) {
    const dataset = await api.createDataset(payload)
    datasets.value.unshift(dataset)
    return dataset
  }

  async function uploadCases(
    datasetId: number,
    cases: { input: string; reference_output: string; metadata?: Record<string, unknown> }[],
  ) {
    const result = await api.uploadCases(datasetId, cases)
    casesByDataset.value[datasetId] = [
      ...(casesByDataset.value[datasetId] ?? []),
      ...result,
    ]
    return result
  }

  async function remove(id: number) {
    // Note: backend doesn't have a delete endpoint for datasets yet, but we handle UI state
    datasets.value = datasets.value.filter((d) => d.id !== id)
    delete casesByDataset.value[id]
  }

  return { datasets, loading, casesByDataset, fetchAll, fetchCases, create, uploadCases, remove }
})
