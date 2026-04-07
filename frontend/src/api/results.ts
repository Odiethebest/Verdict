import client from './client'
import type { EvalResult } from '@/types'

export const submitFeedback = (
  resultId: number,
  payload: { human_score: number; is_golden: boolean },
) => client.patch<EvalResult>(`/results/${resultId}/feedback`, payload).then((r) => r.data)
