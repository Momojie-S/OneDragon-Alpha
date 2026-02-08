<template>
  <div class="model-config-list">
    <el-card>
      <!-- 页面标题和操作栏 -->
      <template #header>
        <div class="card-header">
          <h2>模型配置管理</h2>
          <div class="header-actions">
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建配置
            </el-button>
            <el-button @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 过滤器 -->
      <div class="filter-bar">
        <el-select
          v-model="filters.active"
          placeholder="启用状态"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>

        <el-select
          v-model="filters.provider"
          placeholder="提供商"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="OpenAI" value="openai" />
        </el-select>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="configs"
        style="width: 100%; margin-top: 20px"
        stripe
        border
      >
        <el-table-column prop="name" label="配置名称" width="200" />
        <el-table-column prop="provider" label="Provider" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="Base URL" min-width="250" show-overflow-tooltip />
        <el-table-column label="模型数量" width="100" align="center">
          <template #default="{ row }">
            <el-badge :value="row.models.length" :max="99" type="primary" />
          </template>
        </el-table-column>
        <el-table-column label="启用状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleToggleStatus(row)"
              :loading="row._toggling"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <ModelConfigDialog
      v-model:visible="dialogVisible"
      :config="currentConfig"
      @saved="handleSaved"
    />

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
    >
      <p>确定要删除配置「{{ currentConfig?.name }}」吗？</p>
      <p style="color: var(--el-color-danger); font-size: 12px">
        此操作不可撤销！
      </p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmDelete"
          :loading="deleteLoading"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import ModelConfigDialog from './components/ModelConfigDialog.vue'
import {
  getModelConfigs,
  deleteModelConfig,
  toggleConfigStatus,
  type ModelConfig,
  type PaginationParams
} from '../../services/modelApi'

// ============================================================================
// 状态
// ============================================================================

const loading = ref(false)
const configs = ref<ModelConfig[]>([])
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteLoading = ref(false)
const currentConfig = ref<ModelConfig | undefined>(undefined)

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 过滤条件
const filters = reactive({
  active: undefined as boolean | undefined,
  provider: undefined as string | undefined
})

// ============================================================================
// 数据加载
// ============================================================================

/**
 * 加载配置列表
 */
const loadConfigs = async () => {
  loading.value = true
  try {
    const params: PaginationParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      active: filters.active,
      provider: filters.provider
    }

    const response = await getModelConfigs(params)
    configs.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error(`加载配置列表失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    loading.value = false
  }
}

/**
 * 刷新列表
 */
const handleRefresh = () => {
  loadConfigs()
}

// ============================================================================
// 过滤和分页
// ============================================================================

/**
 * 过滤条件改变
 */
const handleFilterChange = () => {
  pagination.page = 1 // 重置到第一页
  loadConfigs()
}

/**
 * 页码改变
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  loadConfigs()
}

/**
 * 每页数量改变
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadConfigs()
}

// ============================================================================
// CRUD 操作
// ============================================================================

/**
 * 创建配置
 */
const handleCreate = () => {
  currentConfig.value = undefined
  dialogVisible.value = true
}

/**
 * 编辑配置
 */
const handleEdit = (config: ModelConfig) => {
  currentConfig.value = config
  dialogVisible.value = true
}

/**
 * 删除配置
 */
const handleDelete = (config: ModelConfig) => {
  currentConfig.value = config
  deleteDialogVisible.value = true
}

/**
 * 确认删除
 */
const confirmDelete = async () => {
  if (!currentConfig.value) return

  deleteLoading.value = true
  try {
    await deleteModelConfig(currentConfig.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    await loadConfigs()
  } catch (error) {
    ElMessage.error(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    deleteLoading.value = false
  }
}

/**
 * 切换启用状态
 */
const handleToggleStatus = async (config: ModelConfig) => {
  // 添加加载状态标记
  ;(config as any)._toggling = true

  try {
    const updated = await toggleConfigStatus(config.id, config.is_active)
    // 更新本地数据
    Object.assign(config, updated)
    ElMessage.success(config.is_active ? '已启用' : '已禁用')
  } catch (error) {
    // 恢复开关状态
    config.is_active = !config.is_active
    ElMessage.error(`操作失败: ${error instanceof Error ? error.message : '未知错误'}`)

    // 检查是否是乐观锁冲突
    if (error instanceof Error && error.message.includes('已被其他用户修改')) {
      ElMessageBox.alert(
        '该配置已被其他用户修改，请刷新页面后重试',
        '数据冲突',
        { type: 'warning' }
      )
    }
  } finally {
    ;(config as any)._toggling = false
  }
}

/**
 * 保存成功回调
 */
const handleSaved = () => {
  dialogVisible.value = false
  loadConfigs()
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.model-config-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .model-config-list {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .el-button {
    flex: 1;
  }

  .filter-bar {
    flex-direction: column;
    gap: 10px;
  }

  .filter-bar .el-select {
    width: 100% !important;
  }
}

/* 表格动画 */
:deep(.el-table__body tr) {
  transition: background-color 0.2s ease;
}

:deep(.el-table__body tr:hover) {
  background-color: var(--el-fill-color-light) !important;
}

/* 按钮悬停效果 */
:deep(.el-button) {
  transition: all 0.2s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

/* 开关动画 */
:deep(.el-switch) {
  transition: all 0.3s ease;
}

/* 标签动画 */
:deep(.el-tag) {
  transition: all 0.2s ease;
}
</style>
