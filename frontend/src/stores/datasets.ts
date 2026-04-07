import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Dataset } from '@/types'
import * as api from '@/api/datasets'

export const useDatasetsStore = defineStore('datasets', () => {
  const datasets = ref<Dataset[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      datasets.value = await api.listDatasets()
    } finally {
      loading.value = false
    }
  }

  async function create(payload: { name: string; description?: string }) {
    const dataset = await api.createDataset(payload)
    datasets.value.unshift(dataset)
    return dataset
  }

  async function uploadCases(
    datasetId: number,
    cases: { input: string; reference_output: string }[],
  ) {
    return api.uploadCases(datasetId, cases)
  }

  return { datasets, loading, fetchAll, create, uploadCases }
})
