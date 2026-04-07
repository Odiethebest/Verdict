import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Experiment } from '@/types'
import * as api from '@/api/experiments'

export const useExperimentsStore = defineStore('experiments', () => {
  const experiments = ref<Experiment[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      experiments.value = await api.listExperiments()
    } finally {
      loading.value = false
    }
  }

  async function create(payload: { name: string; dataset_id: number; dimension_ids: number[] }) {
    return api.createExperiment(payload)
  }

  async function addVariant(experimentId: number, payload: { name: string; model: string; system_prompt: string; temperature: number }) {
    return api.addVariant(experimentId, payload)
  }

  return { experiments, loading, fetchAll, create, addVariant }
})
