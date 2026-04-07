export interface Dataset {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface TestCase {
  id: number
  dataset_id: number
  input: string
  reference_output: string
  metadata_: Record<string, unknown> | null
}

export interface Dimension {
  id: number
  name: string
  weight: number
  scorer_prompt: string
  created_at: string
}

export interface Variant {
  id: number
  experiment_id: number
  name: string
  model: string
  system_prompt: string
  temperature: number
}

export interface LeaderboardEntry {
  variant_id: number
  variant_name: string
  aggregate_score: number
  rank: number
}

export interface Experiment {
  id: number
  name: string
  dataset_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  variants?: Variant[]
  leaderboard?: LeaderboardEntry[]
}

export interface DimensionScore {
  id: number
  dimension_id: number
  score: number
  reasoning: string | null
}

export interface EvalResult {
  id: number
  variant_id: number
  test_case_id: number
  raw_output: string
  rouge_score: number | null
  judge_score: number | null
  judge_reasoning: string | null
  exact_match: boolean | null
  human_score: number | null
  is_golden: boolean
  created_at: string
  dimension_scores: DimensionScore[]
}
