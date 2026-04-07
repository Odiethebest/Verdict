import { ref, onUnmounted } from 'vue'

interface ProgressEvent {
  variant_id: number
  completed: number
  total: number
}

export function useRunProgress(experimentId: number) {
  const progress = ref<Record<number, { completed: number; total: number }>>({})
  let source: EventSource | null = null

  function start() {
    if (source) return
    source = new EventSource(`/api/experiments/${experimentId}/stream`)
    source.onmessage = (event) => {
      const data: ProgressEvent = JSON.parse(event.data)
      progress.value[data.variant_id] = { completed: data.completed, total: data.total }
    }
    source.onerror = () => {
      source?.close()
      source = null
    }
  }

  function stop() {
    source?.close()
    source = null
  }

  onUnmounted(stop)

  return { progress, start, stop }
}
