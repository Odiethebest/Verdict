<template>
  <nav class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-mark">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M4 9l3.5 3.5L14 6" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <div class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.routeName) }"
        :title="item.label"
      >
        <component :is="item.icon" />
      </RouterLink>
    </div>

    <div class="sidebar-bottom">
      <button class="nav-item" title="Settings" style="background:none;border:none;cursor:pointer;">
        <SettingsIcon />
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { defineComponent, h } from 'vue'

const route = useRoute()

function isActive(routeName: string) {
  const name = String(route.name ?? '')
  return name === routeName || name.startsWith(routeName)
}

// Inline SVG icon components
const ExperimentsIcon = defineComponent({
  render: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18' }),
  ]),
})

const DatasetsIcon = defineComponent({
  render: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('ellipse', { cx: 12, cy: 5, rx: 9, ry: 3 }),
    h('path', { d: 'M21 12c0 1.66-4 3-9 3s-9-1.34-9-3' }),
    h('path', { d: 'M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5' }),
  ]),
})

const DimensionsIcon = defineComponent({
  render: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('polygon', { points: '12 2 2 7 12 12 22 7 12 2' }),
    h('polyline', { points: '2 17 12 22 22 17' }),
    h('polyline', { points: '2 12 12 17 22 12' }),
  ]),
})

const SettingsIcon = defineComponent({
  render: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('circle', { cx: 12, cy: 12, r: 3 }),
    h('path', { d: 'M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z' }),
  ]),
})

const navItems = [
  { name: 'experiments', label: 'Experiments', to: '/experiments', routeName: 'experiment', icon: ExperimentsIcon },
  { name: 'datasets',    label: 'Datasets',    to: '/datasets',    routeName: 'datasets',    icon: DatasetsIcon },
  { name: 'dimensions',  label: 'Dimensions',  to: '/dimensions',  routeName: 'dimensions',  icon: DimensionsIcon },
]
</script>

<style scoped>
.sidebar {
  width: 56px;
  min-height: 100vh;
  background: var(--matcha-800);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  flex-shrink: 0;
  position: sticky;
  top: 0;
}

.sidebar-logo {
  margin-bottom: 24px;
}

.logo-mark {
  width: 32px;
  height: 32px;
  background: var(--matcha-400);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.sidebar-bottom {
  margin-top: auto;
}

.nav-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: white;
  opacity: 0.45;
  text-decoration: none;
  transition: opacity 0.15s, background 0.15s;
}

.nav-item:hover {
  opacity: 0.75;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  opacity: 1;
}
</style>
