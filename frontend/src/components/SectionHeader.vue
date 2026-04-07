<template>
  <div class="section-header">
    <span class="section-title">{{ title }}</span>
    <span v-if="count !== undefined" class="count-badge">{{ count }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  count?: number
}>()
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.section-title {
  font-size: 20px;
  font-weight: 500;
  color: var(--text-primary);
}
.count-badge {
  font-size: 12px;
  font-weight: 500;
  background: var(--matcha-100);
  color: var(--matcha-800);
  border-radius: 10px;
  padding: 2px 8px;
}
</style>
