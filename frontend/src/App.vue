<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElTabs, ElTabPane } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import ChatAnalysis from './views/ChatAnalysis.vue'
import DevOptions from './views/DevOptions.vue'

const router = useRouter()
const route = useRoute()
const activeTab = ref('ad-hoc')

// 是否在开发环境
const isDevelopment = computed(() => import.meta.env.DEV)

// 监听路由变化，同步标签页状态
const watchRoute = () => {
  if (route.path === '/') {
    activeTab.value = 'ad-hoc'
  } else if (route.path === '/dev-options') {
    activeTab.value = 'dev-options'
  } else if (route.path === '/model-management') {
    activeTab.value = 'model-management'
  }
}

// 初始化和监听路由
watchRoute()
watch(() => route.path, watchRoute, { immediate: true })

// 处理标签页切换
const handleTabChange = (tab: any) => {
  const tabName = tab.paneName

  if (tabName === 'ad-hoc') {
    router.push('/')
  } else if (tabName === 'dev-options') {
    router.push('/dev-options')
  } else if (tabName === 'model-management') {
    router.push('/model-management')
  }
}
</script>

<template>
  <div class="app-container">
    <div class="tabs-container">
      <ElTabs v-model="activeTab" @tab-click="handleTabChange" @change="handleTabChange">
        <ElTabPane label="即席分析" name="ad-hoc" />
        <ElTabPane label="模型配置" name="model-management" />
        <ElTabPane v-if="isDevelopment" label="开发选项" name="dev-options" />
      </ElTabs>
    </div>
    <div class="content-container">
      <!-- 路由视图 -->
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tabs-container {
  padding: 0 24px;
  background-color: #fff;
}

/* Element Plus Tabs 样式重置 */
:deep(.el-tabs__nav-wrap) {
  padding: 0;
}

:deep(.el-tabs__nav-scroll) {
  padding: 0;
}

:deep(.el-tabs__nav) {
  border: none;
}

:deep(.el-tabs__item) {
  padding: 16px 0;
  margin-right: 32px;
  border: none;
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
}

:deep(.el-tabs__active-bar) {
  background-color: #409eff;
  height: 3px;
  border-radius: 2px;
}

.content-container {
  flex: 1;
  padding: 0;
  overflow: hidden;
  display: flex;
}
</style>
