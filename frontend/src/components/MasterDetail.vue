<template>
  <div class="master-detail">
    <div class="master-panel">
      <slot name="master" />
    </div>
    <div class="detail-panel">
      <slot name="detail" />
    </div>
  </div>
</template>

<style scoped>
.master-detail {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 0;
}
.master-panel {
  width: 380px;
  flex-shrink: 0;
  border-right: 0.5px solid var(--border);
  overflow-y: auto;
  padding: 20px 16px;
}
.detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  background: var(--cream);
}
</style>
