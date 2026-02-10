<template>
  <div class="dev-options-container">
    <div class="dev-header">
      <h1 class="dev-title">开发选项</h1>
      <p class="dev-subtitle">仅在开发环境可见的配置和测试工具</p>
    </div>

    <div class="dev-content">
      <!-- Mock 配置区域 -->
      <div class="config-section">
        <div class="section-header">
          <h2 class="section-title">API 模拟配置</h2>
          <el-tag :type="mockEnabled ? 'success' : 'info'" size="small">
            {{ mockEnabled ? 'Mock 模式' : '真实 API' }}
          </el-tag>
        </div>

        <div class="section-content">
          <div class="mock-description">
            <p>Mock 模式可以模拟后端响应，无需启动真实后端服务进行开发测试。</p>
            <ul class="feature-list">
              <li>✅ 模拟 SSE 流式聊天响应</li>
              <li>✅ 模拟图表数据返回</li>
              <li>✅ 支持实时切换，无需重启应用</li>
              <li>✅ 完整的错误处理和延迟模拟</li>
            </ul>
          </div>

          <div class="mock-controls">
            <div class="switch-item">
              <span class="switch-label">启用 Mock 模式</span>
              <el-switch
                v-model="mockEnabled"
                :active-text="'开启'"
                :inactive-text="'关闭'"
                :active-value="true"
                :inactive-value="false"
                size="large"
                @change="handleMockChange"
              />
            </div>

            <div class="status-info">
              <el-alert
                v-if="mockEnabled"
                title="Mock 模式已启用"
                type="success"
                :closable="false"
                show-icon
              >
                <p>当前所有 API 请求将返回模拟数据。真实后端服务不会被调用。</p>
              </el-alert>

              <el-alert v-else title="真实 API 模式" type="info" :closable="false" show-icon>
                <p>当前所有 API 请求将发送到真实后端服务（{{ apiUrl }}）。</p>
                <p v-if="apiStatus === 'error'" class="error-tip">
                  ⚠️ 真实后端服务可能未启动，请确认服务运行状态。
                </p>
              </el-alert>
            </div>
          </div>
        </div>
      </div>

      <!-- 开发工具区域 -->
      <div class="config-section">
        <div class="section-header">
          <h2 class="section-title">开发工具</h2>
        </div>

        <div class="section-content">
          <div class="tool-grid">
            <div class="tool-item">
              <h3 class="tool-name">API 状态检查</h3>
              <p class="tool-desc">测试后端 API 连接状态</p>
              <el-button type="primary" size="small" @click="checkApiStatus" :loading="checkingApi">
                {{ checkingApi ? '检查中...' : '检查状态' }}
              </el-button>
              <div v-if="apiStatus" class="check-result">
                <el-tag :type="apiStatus === 'success' ? 'success' : 'danger'" size="small">
                  {{ apiStatus === 'success' ? '连接正常' : '连接失败' }}
                </el-tag>
              </div>
            </div>

            <div class="tool-item">
              <h3 class="tool-name">清除缓存</h3>
              <p class="tool-desc">清除浏览器本地存储的 Mock 设置</p>
              <el-button type="warning" size="small" @click="clearCache"> 清除缓存 </el-button>
            </div>

            <div class="tool-item">
              <h3 class="tool-name">重置配置</h3>
              <p class="tool-desc">恢复所有设置到默认状态</p>
              <el-button type="danger" size="small" @click="resetConfig"> 重置配置 </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 环境信息 -->
      <div class="config-section">
        <div class="section-header">
          <h2 class="section-title">环境信息</h2>
        </div>

        <div class="section-content">
          <div class="env-info">
            <div class="info-item">
              <span class="info-label">当前环境：</span>
              <el-tag type="info" size="small">{{ environment }}</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">API 地址：</span>
              <code class="api-url">{{ apiUrl }}</code>
            </div>
            <div class="info-item">
              <span class="info-label">Mock 可用：</span>
              <el-tag :type="mockAvailable ? 'success' : 'warning'" size="small">
                {{ mockAvailable ? '是' : '否' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElSwitch, ElTag, ElAlert, ElButton, ElMessage, ElMessageBox } from 'element-plus'
import { API_BASE_URL, USE_MOCK, ALLOW_RUNTIME_MOCK_SWITCH } from '../config/api'

// Mock 状态管理
const mockEnabled = ref(false)
const checkingApi = ref(false)
const apiStatus = ref<'success' | 'error' | null>(null)

// 环境信息
const environment = computed(() => import.meta.env.MODE || 'development')
const apiUrl = computed(() => API_BASE_URL)
const mockAvailable = computed(() => USE_MOCK || ALLOW_RUNTIME_MOCK_SWITCH)

// 从本地存储读取状态
const loadMockState = () => {
  const saved = localStorage.getItem('mockEnabled')
  if (saved !== null) {
    mockEnabled.value = saved === 'true'
  } else {
    // 默认使用环境变量设置
    mockEnabled.value = USE_MOCK
  }
}

// 保存状态到本地存储
const saveMockState = (enabled: boolean) => {
  localStorage.setItem('mockEnabled', enabled.toString())
}

// 处理 Mock 开关切换
const handleMockChange = (enabled: boolean) => {
  console.log(`Mock mode ${enabled ? 'enabled' : 'disabled'}`)
  saveMockState(enabled)

  ElMessage({
    message: `Mock 模式已${enabled ? '启用' : '禁用'}`,
    type: enabled ? 'success' : 'info',
    duration: 3000,
  })

  // 触发自定义事件通知其他组件
  window.dispatchEvent(
    new CustomEvent('mockModeChanged', {
      detail: { enabled },
    }),
  )

  // 延迟刷新以确保状态保存
  setTimeout(() => {
    window.location.reload()
  }, 500)
}

// 检查 API 状态
const checkApiStatus = async () => {
  checkingApi.value = true
  try {
    const response = await fetch(`${apiUrl.value}/chat/stream`, {
      method: 'OPTIONS',
      timeout: 5000,
    })

    if (response.ok || response.status === 405) {
      apiStatus.value = 'success'
      ElMessage({
        message: 'API 连接正常',
        type: 'success',
      })
    } else {
      apiStatus.value = 'error'
      ElMessage({
        message: 'API 连接失败',
        type: 'error',
      })
    }
  } catch (error) {
    apiStatus.value = 'error'
    ElMessage({
      message: 'API 连接失败：' + error.message,
      type: 'error',
    })
  } finally {
    checkingApi.value = false
  }
}

// 清除缓存
const clearCache = async () => {
  try {
    await ElMessageBox.confirm('确定要清除所有本地存储的 Mock 设置吗？', '确认清除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    localStorage.removeItem('mockEnabled')
    mockEnabled.value = USE_MOCK

    ElMessage({
      message: '缓存已清除',
      type: 'success',
    })
  } catch {
    // 用户取消操作
  }
}

// 重置配置
const resetConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有配置到默认状态吗？这将清除所有本地设置。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    localStorage.clear()
    mockEnabled.value = USE_MOCK
    apiStatus.value = null

    ElMessage({
      message: '配置已重置',
      type: 'success',
    })
  } catch {
    // 用户取消操作
  }
}

// 监听全局 Mock 状态变化事件
const handleMockModeChanged = (event: any) => {
  mockEnabled.value = event.detail.enabled
  saveMockState(event.detail.enabled)
}

// 初始化
onMounted(() => {
  loadMockState()

  // 监听事件
  window.addEventListener('mockModeChanged', handleMockModeChanged)

  // 自动检查 API 状态（如果不在 Mock 模式）
  if (!mockEnabled.value) {
    // 延迟检查，避免页面加载时的网络请求
    setTimeout(() => {
      checkApiStatus()
    }, 1000)
  }
})
</script>

<style scoped>
.dev-options-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.dev-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e4e7ed;
}

.dev-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.dev-subtitle {
  margin: 0;
  font-size: 16px;
  color: #909399;
  line-height: 1.5;
}

.dev-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-section {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.section-content {
  padding: 24px;
}

.mock-description {
  margin-bottom: 24px;
}

.mock-description p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.feature-list {
  margin: 12px 0 0 0;
  padding-left: 20px;
}

.feature-list li {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.mock-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.switch-label {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.status-info {
  margin-top: 8px;
}

.error-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #e6a23c;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.tool-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.tool-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tool-desc {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.check-result {
  margin-top: 12px;
}

.env-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.api-url {
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  background: #f4f4f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dev-options-container {
    padding: 16px;
  }

  .tool-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .switch-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
