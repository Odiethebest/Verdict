import client from './client'
import type { Dimension } from '@/types'

export const listDimensions = () =>
  client.get<Dimension[]>('/dimensions').then((r) => r.data)

export const createDimension = (payload: {
  name: string
  weight: number
  scorer_prompt: string
}) => client.post<Dimension>('/dimensions', payload).then((r) => r.data)

export const updateDimension = (
  id: number,
  payload: { name?: string; weight?: number; scorer_prompt?: string },
) => client.put<Dimension>(`/dimensions/${id}`, payload).then((r) => r.data)

export const deleteDimension = (id: number) =>
  client.delete(`/dimensions/${id}`)
