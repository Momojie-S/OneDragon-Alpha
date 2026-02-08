import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/ChatAnalysis.vue'),
    },
    {
      path: '/dev-options',
      name: 'dev-options',
      component: () => import('../views/DevOptions.vue'),
    },
    {
      path: '/model-management',
      name: 'model-management',
      component: () => import('../views/model-management/ModelConfigList.vue'),
      meta: {
        title: '模型配置',
      },
    },
  ],
})

export default router
