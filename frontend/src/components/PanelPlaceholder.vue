<template>
  <div class="placeholder">
    <svg v-if="icon === 'dataset'" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
    </svg>
    <svg v-else-if="icon === 'dimension'" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
    </svg>
    <svg v-else width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    <p class="placeholder-title">{{ title }}</p>
    <p v-if="subtitle" class="placeholder-sub">{{ subtitle }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon?: 'dataset' | 'dimension' | 'default'
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.placeholder {
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--matcha-200);
  text-align: center;
}
.placeholder svg {
  width: 56px;
  height: 56px;
  opacity: 0.35;
}
.placeholder-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-top: 4px;
}
.placeholder-sub {
  font-size: 14px;
  color: var(--text-secondary);
  opacity: 0.7;
  max-width: 240px;
}
</style>
