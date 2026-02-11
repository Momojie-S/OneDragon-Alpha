<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑配置' : '新建配置'"
    width="700px"
    @update:model-value="handleVisibleChange"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <!-- 配置名称 -->
      <el-form-item label="配置名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入配置名称，如：DeepSeek 官方"
          maxlength="255"
          show-word-limit
        />
      </el-form-item>

      <!-- Provider -->
      <el-form-item label="Provider" prop="provider">
        <el-select
          v-model="formData.provider"
          placeholder="选择提供商"
          :disabled="isEdit"
          @change="handleProviderChange"
        >
          <el-option label="OpenAI" value="openai" />
          <el-option label="Qwen" value="qwen" />
        </el-select>
        <span style="margin-left: 10px; color: var(--el-text-color-secondary); font-size: 12px">
          {{ providerHint }}
        </span>
      </el-form-item>

      <!-- OpenAI 字段：Base URL 和 API Key -->
      <template v-if="formData.provider === 'openai'">
        <!-- Base URL -->
        <el-form-item label="Base URL" prop="base_url">
          <el-input
            v-model="formData.base_url"
            placeholder="https://api.deepseek.com"
            maxlength="500"
          />
        </el-form-item>

        <!-- API Key -->
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="formData.api_key"
            type="password"
            :placeholder="isEdit ? '留空则不修改' : '请输入 API Key'"
            show-password
            maxlength="500"
          />
          <div
            v-if="isEdit"
            style="margin-top: 5px; color: var(--el-text-color-secondary); font-size: 12px"
          >
            为了安全，不显示已保存的 API Key。留空则不修改。
          </div>
        </el-form-item>
      </template>

      <!-- Qwen 字段：OAuth 认证 -->
      <template v-if="formData.provider === 'qwen'">
        <el-form-item label="Qwen 账号" prop="oauth_status">
          <div style="width: 100%">
            <!-- 已认证状态 -->
            <div v-if="isAuthenticated" class="oauth-authenticated">
              <el-tag type="success" size="large">
                <el-icon><CircleCheck /></el-icon>
                已认证
              </el-tag>
              <span v-if="tokenExpireTime" style="margin-left: 10px; color: var(--el-text-color-secondary); font-size: 12px">
                Token 过期时间: {{ tokenExpireTime }}
              </span>
              <el-button type="primary" link style="margin-left: 10px" @click="handleReAuth">
                重新登录
              </el-button>
            </div>
            <!-- 未认证状态 -->
            <div v-else class="oauth-unauthenticated">
              <el-button type="primary" @click="handleStartOAuth" :loading="oauthLoading">
                <el-icon><User /></el-icon>
                登录 Qwen 账号
              </el-button>
              <div style="margin-top: 8px; color: #909399; font-size: 12px">
                <el-icon><InfoFilled /></el-icon>
                点击按钮将打开 Qwen 账号授权页面
              </div>
            </div>
          </div>
        </el-form-item>
      </template>

      <!-- 模型列表 -->
      <el-form-item label="模型列表" prop="models">
        <div style="width: 100%">
          <div style="margin-bottom: 10px">
            <el-button
              type="primary"
              size="small"
              @click="handleAddModel"
              :disabled="formData.models.length >= 50"
            >
              <el-icon><Plus /></el-icon>
              添加模型
            </el-button>
            <span style="margin-left: 10px; color: var(--el-text-color-secondary); font-size: 12px">
              至少需要添加一个模型
            </span>
          </div>

          <!-- 模型卡片列表 -->
          <div class="model-list">
            <div v-for="(model, index) in formData.models" :key="index" class="model-card">
              <div class="model-card-header">
                <span class="model-index">#{{ index + 1 }}</span>
                <div class="model-actions">
                  <el-button type="primary" size="small" link @click="handleEditModel(index)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" link @click="handleDeleteModel(index)">
                    删除
                  </el-button>
                </div>
              </div>
              <div class="model-card-body">
                <div><strong>模型 ID:</strong> {{ model.model_id }}</div>
                <div class="model-capabilities">
                  <el-tag v-if="model.support_vision" type="success" size="small">视觉</el-tag>
                  <el-tag v-if="model.support_thinking" type="warning" size="small">思考</el-tag>
                  <el-tag
                    v-if="!model.support_vision && !model.support_thinking"
                    type="info"
                    size="small"
                  >
                    无特殊能力
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-form-item>

      <!-- 测试连接 -->
      <el-form-item label="测试连接">
        <div>
          <el-button
            @click="handleTestConnection"
            :loading="testing"
            :disabled="!formData.base_url || !formData.api_key"
          >
            <el-icon><Connection /></el-icon>
            测试连接
          </el-button>
          <div style="margin-top: 8px; color: #909399; font-size: 12px">
            <el-icon><InfoFilled /></el-icon>
            测试连接会发送一条 "hi" 消息，将消耗少量 token
          </div>
        </div>
        <span
          v-if="testResult"
          style="margin-left: 10px"
          :class="testResult.success ? 'test-success' : 'test-error'"
        >
          {{ testResult.message }}
        </span>
      </el-form-item>

      <!-- 是否启用 -->
      <el-form-item label="是否启用" prop="is_active">
        <el-switch v-model="formData.is_active" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="saving"> 保存 </el-button>
    </template>

    <!-- 模型编辑对话框 -->
    <el-dialog
      v-model="modelDialogVisible"
      :title="editingModelIndex >= 0 ? '编辑模型' : '添加模型'"
      width="500px"
      append-to-body
    >
      <el-form :model="editingModel" label-width="100px">
        <el-form-item label="模型 ID" required>
          <el-input
            v-model="editingModel.model_id"
            placeholder="如：deepseek-chat"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="能力标识">
          <el-checkbox v-model="editingModel.support_vision"> 支持视觉 </el-checkbox>
          <el-checkbox v-model="editingModel.support_thinking" style="margin-left: 20px">
            支持思考
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveModel">确定</el-button>
      </template>
    </el-dialog>

    <!-- OAuth 用户码对话框 -->
    <el-dialog
      v-model="oauthDialogVisible"
      title="Qwen 账号授权"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      append-to-body
    >
      <div class="oauth-dialog-content">
        <div class="oauth-steps">
          <el-steps :active="0" finish-status="success" simple>
            <el-step title="获取用户码" icon="CircleCheck" />
            <el-step title="用户授权" icon="User" />
            <el-step title="完成认证" icon="CircleCheck" />
          </el-steps>
        </div>

        <div class="oauth-instructions">
          <p>请按以下步骤完成 Qwen 账号授权：</p>
          <ol>
            <li>点击下方按钮打开 Qwen 授权页面</li>
            <li>在页面中输入以下用户码（或直接点击完整链接）</li>
            <li>完成登录和授权</li>
            <li>等待本页面自动检测到授权完成</li>
          </ol>
        </div>

        <div class="user-code-section">
          <div class="user-code-label">您的用户码</div>
          <div class="user-code-display" @click="copyUserCode">
            <span class="user-code-text">{{ deviceCodeData?.user_code || '加载中...' }}</span>
            <el-icon class="copy-icon"><DocumentCopy /></el-icon>
          </div>
          <div class="user-code-hint">点击用户码可复制到剪贴板</div>
        </div>

        <div class="oauth-actions">
          <el-button type="primary" size="large" @click="openVerificationUrl">
            <el-icon><Link /></el-icon>
            打开授权页面
          </el-button>
          <el-button size="large" @click="copyUserCode">
            <el-icon><DocumentCopy /></el-icon>
            复制用户码
          </el-button>
        </div>

        <div class="oauth-status">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>等待您完成授权...</span>
        </div>
      </div>

      <template #footer>
        <el-button type="danger" @click="handleCloseOAuthDialog">取消授权</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Connection, InfoFilled, CircleCheck, User, DocumentCopy, Link, Loading } from '@element-plus/icons-vue'
import {
  createModelConfig,
  updateModelConfig,
  testConnection,
  type CreateModelConfigRequest,
  type UpdateModelConfigRequest,
  type ModelInfo,
  type ModelConfig,
} from '../../../services/modelApi'
import {
  getDeviceCode,
  pollWithRetry,
  type OAuthToken,
} from '../../../services/qwenOAuthApi'

// ============================================================================
// Props
// ============================================================================

interface Props {
  visible: boolean
  config?: ModelConfig
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

// ============================================================================
// 状态
// ============================================================================

const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

// OAuth 相关状态
const oauthLoading = ref(false)
const oauthToken = ref<OAuthToken | null>(null)
const oauthDialogVisible = ref(false)
const oauthAbortController = ref<AbortController | null>(null)
const deviceCodeData = ref<{
  device_code: string
  user_code: string
  verification_uri_complete: string
  expires_in: number
} | null>(null)

const modelDialogVisible = ref(false)
const editingModelIndex = ref(-1)
const editingModel = reactive<ModelInfo>({
  model_id: '',
  support_vision: false,
  support_thinking: false,
})

// 表单数据
const formData = reactive<CreateModelConfigRequest & { updated_at?: string }>({
  name: '',
  provider: 'openai',
  base_url: '',
  api_key: '',
  models: [],
  is_active: true,
  updated_at: undefined,
})

// 表单验证规则（动态计算）
const formRules = computed<FormRules>(() => {
  const baseRules: FormRules = {
    name: [
      { required: true, message: '请输入配置名称', trigger: 'blur' },
      { min: 2, max: 255, message: '长度在 2 到 255 个字符', trigger: 'blur' },
    ],
    provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
    models: [
      {
        validator: (rule, value, callback) => {
          if (!value || value.length === 0) {
            callback(new Error('至少需要添加一个模型'))
          } else {
            callback()
          }
        },
        trigger: 'change',
      },
    ],
  }

  // OpenAI Provider 需要验证 base_url 和 api_key
  if (formData.provider === 'openai') {
    baseRules.base_url = [
      { required: true, message: '请输入 Base URL', trigger: 'blur' },
      { type: 'url', message: '请输入有效的 URL', trigger: 'blur' },
    ]
    baseRules.api_key = [
      {
        validator: (rule, value, callback) => {
          if (!isEdit.value && !value) {
            callback(new Error('请输入 API Key'))
          } else {
            callback()
          }
        },
        trigger: 'blur',
      },
    ]
  }

  // Qwen Provider 需要验证 OAuth 认证
  if (formData.provider === 'qwen') {
    baseRules.oauth_status = [
      {
        validator: (rule, value, callback) => {
          if (!isAuthenticated.value) {
            callback(new Error('请先完成 Qwen 账号授权'))
          } else {
            callback()
          }
        },
        trigger: 'change',
      },
    ]
  }

  return baseRules
})

// 是否为编辑模式
const isEdit = computed(() => !!props.config)

// Provider 提示文字
const providerHint = computed(() => {
  if (isEdit.value) {
    return '编辑模式下不能修改 Provider 类型'
  }
  if (formData.provider === 'openai') {
    return '支持 OpenAI 兼容接口的提供商'
  }
  if (formData.provider === 'qwen') {
    return '使用 Qwen 官方 OAuth 账号授权'
  }
  return ''
})

// 是否已认证
const isAuthenticated = computed(() => !!oauthToken.value)

// Token 过期时间显示
const tokenExpireTime = computed(() => {
  if (!oauthToken.value?.expires_at) return ''
  const date = new Date(oauthToken.value.expires_at)
  return date.toLocaleString('zh-CN')
})

// ============================================================================
// 监听
// ============================================================================

watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      resetForm()
      if (props.config) {
        // 编辑模式：填充现有数据
        Object.assign(formData, {
          name: props.config.name,
          provider: props.config.provider,
          base_url: props.config.base_url,
          api_key: '', // API Key 不回填
          models: [...props.config.models],
          is_active: props.config.is_active,
          updated_at: props.config.updated_at,
        })
      }
    }
  },
)

// Provider 切换时清理相关字段
watch(
  () => formData.provider,
  (newProvider, oldProvider) => {
    if (newProvider !== oldProvider && oldProvider) {
      // 清理 OAuth 相关状态
      oauthToken.value = null
      stopOAuthPolling()
    }
  },
)

// 组件销毁时清理轮询
onUnmounted(() => {
  stopOAuthPolling()
})

// ============================================================================
// 方法
// ============================================================================

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    provider: 'openai',
    base_url: '',
    api_key: '',
    models: [],
    is_active: true,
    updated_at: undefined,
  })
  testResult.value = null
  formRef.value?.clearValidate()
}

/**
 * 对话框可见性改变
 */
const handleVisibleChange = (value: boolean) => {
  emit('update:visible', value)
}

/**
 * 取消
 */
const handleCancel = () => {
  handleVisibleChange(false)
}

/**
 * 添加模型
 */
const handleAddModel = () => {
  editingModelIndex.value = -1
  Object.assign(editingModel, {
    model_id: '',
    support_vision: false,
    support_thinking: false,
  })
  modelDialogVisible.value = true
}

/**
 * 编辑模型
 */
const handleEditModel = (index: number) => {
  editingModelIndex.value = index
  const model = formData.models[index]
  Object.assign(editingModel, model)
  modelDialogVisible.value = true
}

/**
 * 删除模型
 */
const handleDeleteModel = (index: number) => {
  formData.models.splice(index, 1)
  // 触发验证
  formRef.value?.validateField('models')
}

/**
 * 保存模型
 */
const handleSaveModel = () => {
  if (!editingModel.model_id.trim()) {
    ElMessage.warning('请输入模型 ID')
    return
  }

  const modelData: ModelInfo = {
    model_id: editingModel.model_id.trim(),
    support_vision: editingModel.support_vision,
    support_thinking: editingModel.support_thinking,
  }

  if (editingModelIndex.value >= 0) {
    // 编辑现有模型
    formData.models[editingModelIndex.value] = modelData
  } else {
    // 添加新模型
    formData.models.push(modelData)
  }

  modelDialogVisible.value = false
  // 触发验证
  formRef.value?.validateField('models')
}

/**
 * Provider 切换处理
 */
const handleProviderChange = () => {
  // 清理 OpenAI 字段
  if (formData.provider === 'qwen') {
    formData.base_url = ''
    formData.api_key = ''
  }
  // 清理 OAuth 状态
  oauthToken.value = null
  stopOAuthPolling()
  // 触发验证
  formRef.value?.clearValidate()
}

/**
 * 开始 OAuth 认证流程
 */
const handleStartOAuth = async () => {
  oauthLoading.value = true
  try {
    // 获取设备码
    const deviceCode = await getDeviceCode()
    deviceCodeData.value = {
      device_code: deviceCode.device_code,
      user_code: deviceCode.user_code,
      verification_uri_complete: deviceCode.verification_uri_complete,
      expires_in: deviceCode.expires_in,
    }

    // 显示用户码对话框
    oauthDialogVisible.value = true

    // 开始轮询
    startOAuthPolling(deviceCode.device_code)
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : '获取设备码失败'
    ElMessage.error(`启动认证失败: ${errorMsg}`)
  } finally {
    oauthLoading.value = false
  }
}

/**
 * 开始 OAuth 状态轮询
 */
const startOAuthPolling = (deviceCode: string) => {
  // 创建新的 AbortController
  oauthAbortController.value = new AbortController()

  pollWithRetry(deviceCode, {
    signal: oauthAbortController.value.signal,
    onStatusChange: (status) => {
      // 可以在这里更新 UI 状态
    },
  })
    .then((token) => {
      oauthToken.value = token
      oauthDialogVisible.value = false
      ElMessage.success('Qwen 账号授权成功')
      // 触发验证
      formRef.value?.validateField('oauth_status')
    })
    .catch((error) => {
      if (error.message !== '认证已取消') {
        ElMessage.error(`认证失败: ${error.message}`)
      }
      oauthDialogVisible.value = false
    })
}

/**
 * 停止 OAuth 轮询
 */
const stopOAuthPolling = () => {
  if (oauthAbortController.value) {
    oauthAbortController.value.abort()
    oauthAbortController.value = null
  }
}

/**
 * 重新认证
 */
const handleReAuth = () => {
  oauthToken.value = null
  handleStartOAuth()
}

/**
 * 复制用户码
 */
const copyUserCode = async () => {
  if (!deviceCodeData.value?.user_code) return

  try {
    await navigator.clipboard.writeText(deviceCodeData.value.user_code)
    ElMessage.success('用户码已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

/**
 * 打开验证页面
 */
const openVerificationUrl = () => {
  if (deviceCodeData.value?.verification_uri_complete) {
    window.open(deviceCodeData.value.verification_uri_complete, '_blank')
  }
}

/**
 * 关闭 OAuth 对话框
 */
const handleCloseOAuthDialog = () => {
  stopOAuthPolling()
  oauthDialogVisible.value = false
  deviceCodeData.value = null
}

/**
 * 测试连接
 */
const handleTestConnection = async () => {
  if (!formData.base_url || !formData.api_key) {
    ElMessage.warning('请先输入 Base URL 和 API Key')
    return
  }

  if (!formData.models || formData.models.length === 0) {
    ElMessage.warning('请先添加至少一个模型')
    return
  }

  testing.value = true
  testResult.value = null

  try {
    // 使用第一个配置的模型进行测试
    const firstModel = formData.models[0]
    const result = await testConnection({
      base_url: formData.base_url,
      api_key: formData.api_key,
      model_id: firstModel.model_id,
    })

    testResult.value = result

    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(`连接测试失败: ${result.message}`)
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : '未知错误'
    testResult.value = { success: false, message: errorMsg }
    ElMessage.error(`连接测试失败: ${errorMsg}`)
  } finally {
    testing.value = false
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true

  try {
    if (isEdit.value && props.config) {
      // 编辑模式
      const updateData: UpdateModelConfigRequest = {
        name: formData.name,
        provider: formData.provider,
        base_url: formData.base_url,
        models: formData.models,
        is_active: formData.is_active,
        updated_at: formData.updated_at,
      }

      // OpenAI Provider：只有当用户输入了 API Key 时才更新
      if (formData.provider === 'openai' && formData.api_key) {
        updateData.api_key = formData.api_key
      }

      await updateModelConfig(props.config.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 新建模式
      if (formData.provider === 'qwen') {
        // Qwen Provider：需要包含 OAuth token
        const createData: CreateModelConfigRequest & { oauth_token?: OAuthToken } = {
          ...formData,
          base_url: '', // Qwen 不需要 base_url
          api_key: '', // Qwen 不需要 api_key
        }
        if (oauthToken.value) {
          createData.oauth_token = oauthToken.value
        }
        await createModelConfig(createData as unknown as CreateModelConfigRequest)
      } else {
        // OpenAI Provider
        await createModelConfig(formData)
      }
      ElMessage.success('创建成功')
    }

    emit('saved')
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : '未知错误'

    // 检查是否是乐观锁冲突
    if (errorMsg.includes('已被其他用户修改')) {
      ElMessage({
        message: '该配置已被其他用户修改，请刷新后重试',
        type: 'warning',
        duration: 5000,
      })
    } else {
      ElMessage.error(`保存失败: ${errorMsg}`)
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.model-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  transition: all 0.3s ease;
}

/* 滚动条样式 */
.model-list::-webkit-scrollbar {
  width: 6px;
}

.model-list::-webkit-scrollbar-track {
  background: var(--el-fill-color-blank);
  border-radius: 3px;
}

.model-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 3px;
  transition: background 0.3s ease;
}

.model-list::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

.model-card {
  background-color: white;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.model-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: var(--el-color-primary-light-5);
}

.model-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-index {
  font-weight: 600;
  color: var(--el-color-primary);
  font-size: 14px;
}

.model-actions {
  display: flex;
  gap: 5px;
}

.model-card-body {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.model-card-body > div {
  margin-bottom: 5px;
}

.model-capabilities {
  margin-top: 8px;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.model-capabilities .el-tag {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.test-success {
  color: var(--el-color-success);
  font-weight: 500;
  animation: pulseSuccess 0.5s ease;
}

.test-error {
  color: var(--el-color-danger);
  font-weight: 500;
  animation: shake 0.5s ease;
}

@keyframes pulseSuccess {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }

  .model-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }

  .model-card {
    padding: 10px;
  }
}

/* 表单项动画 */
:deep(.el-form-item) {
  transition: all 0.3s ease;
}

:deep(.el-form-item:hover) {
  background-color: var(--el-fill-color-lighter);
  border-radius: 4px;
  padding: 4px;
  margin: -4px;
}

/* 按钮悬停效果 */
:deep(.el-button) {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-button:active) {
  transform: translateY(0);
}

/* 输入框焦点效果 */
:deep(.el-input__wrapper) {
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary-light-5) inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

/* 开关动画 */
:deep(.el-switch) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--el-color-success);
  border-color: var(--el-color-success);
}

/* ============================================================================
   OAuth 相关样式
   ============================================================================ */

.oauth-authenticated {
  display: flex;
  align-items: center;
}

.oauth-unauthenticated {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* OAuth 对话框样式 */
.oauth-dialog-content {
  padding: 10px 0;
}

.oauth-steps {
  margin-bottom: 24px;
}

.oauth-instructions {
  margin-bottom: 24px;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

.oauth-instructions p {
  margin: 0 0 12px 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.oauth-instructions ol {
  margin: 0;
  padding-left: 20px;
}

.oauth-instructions li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.user-code-section {
  margin-bottom: 24px;
  text-align: center;
}

.user-code-label {
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.user-code-display {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background-color: var(--el-fill-color-light);
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-code-display:hover {
  background-color: var(--el-fill-color);
  border-color: var(--el-color-primary);
  transform: scale(1.02);
}

.user-code-text {
  font-size: 28px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  letter-spacing: 4px;
  color: var(--el-color-primary);
}

.copy-icon {
  font-size: 20px;
  color: var(--el-text-color-secondary);
  transition: color 0.3s ease;
}

.user-code-display:hover .copy-icon {
  color: var(--el-color-primary);
}

.user-code-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.oauth-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.oauth-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background-color: var(--el-color-info-light-9);
  border-radius: 6px;
  color: var(--el-color-info);
  font-size: 14px;
}

.oauth-status .el-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Provider 切换过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
