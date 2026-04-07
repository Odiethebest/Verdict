import client from './client'
import type { Dataset, TestCase } from '@/types'

export const listDatasets = () =>
  client.get<Dataset[]>('/datasets').then((r) => r.data)

export const createDataset = (payload: { name: string; description?: string }) =>
  client.post<Dataset>('/datasets', payload).then((r) => r.data)

export const uploadCases = (
  datasetId: number,
  cases: { input: string; reference_output: string; metadata?: Record<string, unknown> }[],
) => client.post<TestCase[]>(`/datasets/${datasetId}/cases`, { cases }).then((r) => r.data)

export const listCases = (datasetId: number) =>
  client.get<TestCase[]>(`/datasets/${datasetId}/cases`).then((r) => r.data)
