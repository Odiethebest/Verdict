import client from './client'
import type { Experiment, Variant, EvalResult, LeaderboardEntry } from '@/types'

export const listExperiments = () =>
  client.get<Experiment[]>('/experiments').then((r) => r.data)

export const createExperiment = (payload: {
  name: string
  dataset_id: number
  dimension_ids: number[]
}) => client.post<Experiment>('/experiments', payload).then((r) => r.data)

export const getExperiment = (id: number) =>
  client.get<Experiment>(`/experiments/${id}`).then((r) => r.data)

export const addVariant = (
  experimentId: number,
  payload: {
    name: string
    model: string
    system_prompt: string
    temperature: number
  },
) => client.post<Variant>(`/experiments/${experimentId}/variants`, payload).then((r) => r.data)

export const triggerRun = (id: number) =>
  client.post(`/experiments/${id}/run`).then((r) => r.data)

export const getResults = (id: number) =>
  client.get<EvalResult[]>(`/experiments/${id}/results`).then((r) => r.data)

export const getLeaderboard = (id: number) =>
  client.get<LeaderboardEntry[]>(`/experiments/${id}/leaderboard`).then((r) => r.data)

export const exportGolden = (id: number) =>
  client.get(`/experiments/${id}/export`, { responseType: 'blob' }).then((r) => r.data)
