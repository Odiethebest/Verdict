import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Dimension } from '@/types'
import * as api from '@/api/dimensions'

export const useDimensionsStore = defineStore('dimensions', () => {
  const dimensions = ref<Dimension[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      dimensions.value = await api.listDimensions()
    } finally {
      loading.value = false
    }
  }

  async function create(payload: { name: string; weight: number; scorer_prompt: string }) {
    const dim = await api.createDimension(payload)
    dimensions.value.unshift(dim)
    return dim
  }

  async function update(id: number, payload: { name?: string; weight?: number; scorer_prompt?: string }) {
    const dim = await api.updateDimension(id, payload)
    const idx = dimensions.value.findIndex((d) => d.id === id)
    if (idx !== -1) dimensions.value[idx] = dim
    return dim
  }

  async function remove(id: number) {
    await api.deleteDimension(id)
    dimensions.value = dimensions.value.filter((d) => d.id !== id)
  }

  return { dimensions, loading, fetchAll, create, update, remove }
})
