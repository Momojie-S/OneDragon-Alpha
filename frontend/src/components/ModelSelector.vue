<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElSelect, ElOption, ElButton } from 'element-plus'
import { getActiveModelConfigs } from '../services/modelApi'
import type { ModelConfig } from '../services/modelApi'

/**
 * 组件 Props
 */
interface Props {
  /** 占位符文本 */
  placeholder?: string
}

/**
 * 组件 Emits
 */
interface Emits {
  /** 选中模型 ID 变化事件 */
  (e: 'update:selectedModelId', value: number): void
  /** 加载状态变化事件 */
  (e: 'loading', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择模型',
})

const emit = defineEmits<Emits>()

// 常量定义
const STORAGE_KEY = 'chat-selected-model-config-id'

// 响应式状态
const modelConfigs = ref<ModelConfig[]>([])
const selectedModelId = ref<number | null>(null)
const isLoading = ref<boolean>(false)
const error = ref<string | null>(null)

// 计算属性：是否有可用的模型配置
const hasAvailableModels = computed(() => modelConfigs.value.length > 0)

// 计算属性：选择器是否应该被禁用
const isDisabled = computed(() => !hasAvailableModels.value && !isLoading.value)

// 计算属性：占位符文本
const placeholderText = computed(() => {
  if (isLoading.value) {
    return '加载中...'
  }
  if (!hasAvailableModels.value) {
    return '暂无可用模型，请先添加模型配置'
  }
  return props.placeholder
})

/**
 * 从 localStorage 加载选中的模型 ID
 */
const loadSelectedModelId = (): number | null => {
  try {
    const savedId = localStorage.getItem(STORAGE_KEY)
    return savedId ? parseInt(savedId, 10) : null
  } catch (err) {
    console.error('读取 localStorage 失败:', err)
    return null
  }
}

/**
 * 保存选中的模型 ID 到 localStorage
 */
const saveSelectedModelId = (modelId: number): void => {
  try {
    localStorage.setItem(STORAGE_KEY, String(modelId))
  } catch (err) {
    console.error('保存到 localStorage 失败:', err)
  }
}

/**
 * 格式化选项显示文本
 */
const formatOptionLabel = (config: ModelConfig): string => {
  const modelCount = config.models.length
  return `${config.name} (${modelCount}个模型)`
}

/**
 * 截断配置名称（如果超过 30 个字符）
 */
const truncateConfigName = (name: string): string => {
  return name.length > 30 ? name.substring(0, 30) + '...' : name
}

/**
 * 获取模型配置列表
 */
const fetchModelConfigs = async () => {
  isLoading.value = true
  error.value = null
  emit('loading', true)

  try {
    const response = await getActiveModelConfigs()
    modelConfigs.value = response.items

    // 恢复上次选择的模型
    const savedId = loadSelectedModelId()
    if (savedId !== null) {
      // 验证保存的 ID 是否仍在可用配置中
      const isValid = modelConfigs.value.some((config) => config.id === savedId)
      if (isValid) {
        selectedModelId.value = savedId
      } else if (modelConfigs.value.length > 0) {
        // 如果无效，选择第一个可用配置
        selectedModelId.value = modelConfigs.value[0].id
      }
    } else if (modelConfigs.value.length > 0) {
      // 如果没有保存的选择，选择第一个可用配置
      selectedModelId.value = modelConfigs.value[0].id
    }
  } catch (err) {
    console.error('获取模型配置失败:', err)
    error.value = err instanceof Error ? err.message : '获取模型配置失败'
  } finally {
    isLoading.value = false
    emit('loading', false)
  }
}

/**
 * 处理模型选择变化
 */
const handleModelChange = (modelId: number) => {
  if (modelId) {
    saveSelectedModelId(modelId)
    emit('update:selectedModelId', modelId)
  }
}

/**
 * 重试获取模型配置
 */
const retryFetch = () => {
  fetchModelConfigs()
}

// 组件挂载时获取模型配置
onMounted(() => {
  fetchModelConfigs()
})
</script>

<template>
  <div class="model-selector">
    <el-select
      v-model="selectedModelId"
      :placeholder="placeholderText"
      :disabled="isDisabled"
      :loading="isLoading"
      clearable
      class="model-selector-select"
      @change="handleModelChange"
    >
      <el-option
        v-for="config in modelConfigs"
        :key="config.id"
        :label="formatOptionLabel(config)"
        :value="config.id"
        :title="config.name"
      >
        <span class="option-text">
          {{ truncateConfigName(config.name) }} ({{ config.models.length }}个模型)
        </span>
      </el-option>
    </el-select>

    <div v-if="error && !isLoading" class="model-selector-error">
      <span class="error-message">{{ error }}</span>
      <el-button type="text" @click="retryFetch">重试</el-button>
    </div>
  </div>
</template>

<style scoped>
.model-selector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 840px;
  margin: 0 auto 20px;
}

.model-selector-select {
  width: 100%;
}

.option-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-selector-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: var(--el-color-danger);
  font-size: 14px;
}

.error-message {
  flex: 1;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .model-selector {
    padding: 0 10px;
  }

  .option-text {
    font-size: 14px;
  }
}
</style>
