<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElSelect, ElOption, ElButton, ElTag } from 'element-plus'
import { getActiveModelConfigs } from '../services/modelApi'
import type { ModelConfig, ModelInfo } from '../services/modelApi'

/**
 * 组件 Props
 */
interface Props {
  /** 初始模型配置 ID（可选） */
  model_config_id?: number
  /** 初始模型 ID（可选） */
  model_id?: string
  /** 是否自动选择第一个配置和模型（默认 false） */
  autoSelect?: boolean
}

/**
 * 组件 Emits
 */
interface Emits {
  /** 模型选择变化事件 */
  (e: 'change', value: { model_config_id: number; model_id: string }): void
  /** 加载状态变化事件 */
  (e: 'loading', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  autoSelect: false,
})

const emit = defineEmits<Emits>()

// 常量定义
const STORAGE_KEY = 'chat_model_selection'

// 响应式状态
const modelConfigs = ref<ModelConfig[]>([])
const selectedConfigId = ref<number | null>(null)
const selectedModelId = ref<string | null>(null)
const isLoading = ref<boolean>(false)
const error = ref<string | null>(null)

// 计算属性：是否有可用的模型配置
const hasAvailableConfigs = computed(() => modelConfigs.value.length > 0)

// 计算属性：第一层选择器是否应该被禁用
const isConfigSelectorDisabled = computed(() => !hasAvailableConfigs.value && !isLoading.value)

// 计算属性：第二层选择器是否应该被禁用
const isModelSelectorDisabled = computed(() => selectedConfigId.value === null)

// 计算属性：第一层选择器占位符文本
const configPlaceholderText = computed(() => {
  if (isLoading.value) {
    return '加载中...'
  }
  if (!hasAvailableConfigs.value) {
    return '暂无可用模型配置'
  }
  return '请选择模型配置'
})

// 计算属性：第二层选择器占位符文本
const modelPlaceholderText = computed(() => {
  if (selectedConfigId.value === null) {
    return '请先选择配置'
  }
  return '请选择模型'
})

// 计算属性：当前选中配置的模型列表
const currentModels = computed(() => {
  if (selectedConfigId.value === null) {
    return []
  }
  const config = modelConfigs.value.find((c) => c.id === selectedConfigId.value)
  return config?.models || []
})

/**
 * 从 localStorage 加载保存的选择
 */
const loadSelection = (): { model_config_id?: number; model_id?: string } | null => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return null
    const parsed = JSON.parse(saved)
    return {
      model_config_id: parsed.model_config_id,
      model_id: parsed.model_id,
    }
  } catch (err) {
    console.error('读取 localStorage 失败:', err)
    return null
  }
}

/**
 * 保存选择到 localStorage
 */
const saveSelection = (model_config_id: number, model_id: string): void => {
  try {
    const data = { model_config_id, model_id }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (err) {
    console.error('保存到 localStorage 失败:', err)
  }
}

/**
 * 清除 localStorage 中的无效数据
 */
const clearSelection = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (err) {
    console.error('清除 localStorage 失败:', err)
  }
}

/**
 * 格式化配置选项显示文本
 */
const formatConfigLabel = (config: ModelConfig): string => {
  const modelCount = config.models.length
  return `${config.name} (${modelCount} models)`
}

/**
 * 格式化模型选项显示文本
 */
const formatModelLabel = (model: ModelInfo): string => {
  return model.model_id
}

/**
 * 获取模型能力标签
 */
const getModelTags = (model: ModelInfo) => {
  const tags = []
  if (model.support_vision) {
    tags.push({ text: '视觉', type: 'success' as const })
  }
  if (model.support_thinking) {
    tags.push({ text: '思考', type: 'warning' as const })
  }
  if (!model.support_vision && !model.support_thinking) {
    tags.push({ text: '无特殊能力', type: 'info' as const })
  }
  return tags
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

    // 尝试恢复上次的选择
    const saved = loadSelection()

    if (saved && saved.model_config_id) {
      // 验证保存的配置是否存在且启用
      const isValidConfig = modelConfigs.value.some((c) => c.id === saved.model_config_id)
      if (isValidConfig) {
        selectedConfigId.value = saved.model_config_id

        // 验证保存的 model_id 是否在该配置中
        if (saved.model_id) {
          const config = modelConfigs.value.find((c) => c.id === saved.model_config_id)
          const isValidModel = config?.models.some((m) => m.model_id === saved.model_id)
          if (isValidModel) {
            selectedModelId.value = saved.model_id
            emit('change', { model_config_id: saved.model_config_id, model_id: saved.model_id })
          } else {
            // model_id 无效，清除
            clearSelection()
          }
        }
      } else {
        // 配置无效，清除保存的数据
        clearSelection()
      }
    }

    // 如果没有有效的保存选择，且启用了 autoSelect，自动选择第一个
    if ((!selectedConfigId.value || !selectedModelId.value) && props.autoSelect && modelConfigs.value.length > 0) {
      const firstConfig = modelConfigs.value[0]
      selectedConfigId.value = firstConfig.id
      if (firstConfig.models.length > 0) {
        selectedModelId.value = firstConfig.models[0].model_id
        saveSelection(firstConfig.id, firstConfig.models[0].model_id)
        emit('change', { model_config_id: firstConfig.id, model_id: firstConfig.models[0].model_id })
      }
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
 * 处理配置选择变化
 */
const handleConfigChange = (configId: number | null) => {
  if (configId == null) {
    selectedConfigId.value = null
    selectedModelId.value = null
    return
  }

  selectedConfigId.value = configId
  // 切换配置时，重置模型选择
  selectedModelId.value = null
}

/**
 * 处理模型选择变化
 */
const handleModelChange = (modelId: string | null) => {
  if (modelId != null && selectedConfigId.value != null) {
    selectedModelId.value = modelId
    saveSelection(selectedConfigId.value, modelId)
    emit('change', { model_config_id: selectedConfigId.value, model_id: modelId })
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

// 监听 Props 变化
watch(
  () => props.model_config_id,
  (newVal) => {
    if (newVal != null && newVal !== selectedConfigId.value) {
      selectedConfigId.value = newVal
    }
  },
  { immediate: true }
)

watch(
  () => props.model_id,
  (newVal) => {
    if (newVal != null && newVal !== selectedModelId.value) {
      selectedModelId.value = newVal
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="dual-model-selector">
    <!-- 第一层：选择模型配置 -->
    <el-select
      v-model="selectedConfigId"
      :placeholder="configPlaceholderText"
      :disabled="isConfigSelectorDisabled"
      :loading="isLoading"
      clearable
      class="config-selector"
      @change="handleConfigChange"
    >
      <el-option
        v-for="config in modelConfigs"
        :key="config.id"
        :label="formatConfigLabel(config)"
        :value="config.id"
        :title="config.name"
      >
        <span class="option-text">
          {{ config.name }} ({{ config.models.length }} models)
        </span>
      </el-option>
    </el-select>

    <!-- 第二层：选择具体模型 -->
    <el-select
      v-model="selectedModelId"
      :placeholder="modelPlaceholderText"
      :disabled="isModelSelectorDisabled"
      clearable
      class="model-selector"
      @change="handleModelChange"
    >
      <el-option
        v-for="model in currentModels"
        :key="model.model_id"
        :label="formatModelLabel(model)"
        :value="model.model_id"
      >
        <div class="model-option">
          <span class="model-id">{{ model.model_id }}</span>
          <span class="model-tags">
            <el-tag
              v-for="tag in getModelTags(model)"
              :key="tag.text"
              :type="tag.type"
              size="small"
            >
              {{ tag.text }}
            </el-tag>
          </span>
        </div>
      </el-option>
    </el-select>

    <!-- 错误提示 -->
    <div v-if="error && !isLoading" class="dual-model-selector-error">
      <span class="error-message">{{ error }}</span>
      <el-button type="text" size="small" @click="retryFetch">重试</el-button>
    </div>
  </div>
</template>

<style scoped>
.dual-model-selector {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 840px;
  margin: 0 auto 20px;
}

.config-selector,
.model-selector {
  flex: 1;
  min-width: 0;
}

.option-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.model-id {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.dual-model-selector-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: var(--el-color-danger);
  font-size: 14px;
  position: absolute;
  top: 100%;
  left: 0;
}

.error-message {
  flex: 1;
}

/* 响应式布局：移动端垂直排列 */
@media (max-width: 768px) {
  .dual-model-selector {
    flex-direction: column;
    padding: 0 10px;
  }

  .config-selector,
  .model-selector {
    width: 100%;
  }

  .option-text {
    font-size: 14px;
  }
}
</style>
