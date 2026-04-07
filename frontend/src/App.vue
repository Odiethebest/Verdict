<template>
  <el-config-provider :locale="en" size="small">
    <div class="app-layout">
      <AppSidebar />
      <main class="app-main">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import en from 'element-plus/es/locale/lang/en'
import AppSidebar from '@/components/AppSidebar.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}
.app-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}
</style>
