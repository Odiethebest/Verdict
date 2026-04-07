import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/experiments' },
    {
      path: '/experiments',
      name: 'experiments',
      component: () => import('@/views/ExperimentsView.vue'),
    },
    {
      path: '/experiments/:id',
      name: 'experiment-detail',
      component: () => import('@/views/ExperimentDetailView.vue'),
    },
    {
      path: '/datasets',
      name: 'datasets',
      component: () => import('@/views/DatasetsView.vue'),
    },
    {
      path: '/dimensions',
      name: 'dimensions',
      component: () => import('@/views/DimensionsView.vue'),
    },
  ],
})

export default router
