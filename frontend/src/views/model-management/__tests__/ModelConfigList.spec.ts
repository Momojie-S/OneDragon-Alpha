/**
 * ModelConfigList 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import ModelConfigList from '../ModelConfigList.vue'
import type { ModelConfig } from '../../../services/modelApi'
import * as modelApi from '../../../services/modelApi'

// Mock API 服务
vi.mock('../../../services/modelApi', async () => {
  const actual = await vi.importActual('../../../services/modelApi')
  return {
    ...actual,
    getModelConfigs: vi.fn(),
    deleteModelConfig: vi.fn(),
    toggleConfigStatus: vi.fn(),
  }
})

// Mock Element Plus Message
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
  }
})

describe('ModelConfigList.vue', () => {
  let wrapper: VueWrapper<any>

  const mockConfigs: ModelConfig[] = [
    {
      id: 1,
      name: 'test_config_deepseek',
      provider: 'openai',
      base_url: 'https://api.deepseek.com',
      models: [
        { model_id: 'deepseek-chat', support_vision: true, support_thinking: false },
        { model_id: 'deepseek-coder', support_vision: false, support_thinking: true },
      ],
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 2,
      name: 'test_config_moonshot',
      provider: 'openai',
      base_url: 'https://api.moonshot.cn',
      models: [{ model_id: 'moonshot-v1-8k', support_vision: false, support_thinking: false }],
      is_active: false,
      created_at: '2025-01-02T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    },
  ]

  beforeEach(() => {
    const mockedGetModelConfigs = vi.mocked(modelApi.getModelConfigs)
    mockedGetModelConfigs.mockResolvedValue({
      total: 2,
      page: 1,
      page_size: 20,
      items: mockConfigs,
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染列表页面', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      // 等待数据加载
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 0))

      expect(wrapper.find('.model-config-list').exists()).toBe(true)
    })

    it('应该显示配置列表数据', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      // 等待数据加载
      await wrapper.vm.$nextTick()
      await new Promise((resolve) => setTimeout(resolve, 0))

      expect(wrapper.vm.configs).toEqual(mockConfigs)
      expect(wrapper.vm.pagination.total).toBe(2)
    })
  })

  describe('过滤器功能', () => {
    it('应该支持按启用状态过滤', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockGetModelConfigs = vi.mocked(modelApi.getModelConfigs)

      // 设置过滤条件
      wrapper.vm.filters.active = true
      await wrapper.vm.handleFilterChange()

      expect(mockGetModelConfigs).toHaveBeenCalledWith(
        expect.objectContaining({
          active: true,
          page: 1,
        }),
      )
    })

    it('应该支持按 provider 过滤', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockGetModelConfigs = vi.mocked(modelApi.getModelConfigs)

      // 设置过滤条件
      wrapper.vm.filters.provider = 'openai'
      await wrapper.vm.handleFilterChange()

      expect(mockGetModelConfigs).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'openai',
        }),
      )
    })
  })

  describe('分页功能', () => {
    it('应该正确处理页码改变', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockGetModelConfigs = vi.mocked(modelApi.getModelConfigs)

      await wrapper.vm.handlePageChange(2)

      expect(wrapper.vm.pagination.page).toBe(2)
      expect(mockGetModelConfigs).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }))
    })

    it('应该正确处理每页数量改变', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockGetModelConfigs = vi.mocked(modelApi.getModelConfigs)

      await wrapper.vm.handleSizeChange(50)

      expect(wrapper.vm.pagination.page_size).toBe(50)
      expect(wrapper.vm.pagination.page).toBe(1) // 重置到第一页
    })
  })

  describe('操作功能', () => {
    it('应该打开创建对话框', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      await wrapper.vm.handleCreate()

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.currentConfig).toBeUndefined()
    })

    it('应该打开编辑对话框并填充数据', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      await wrapper.vm.handleEdit(mockConfigs[0])

      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.currentConfig).toEqual(mockConfigs[0])
    })

    it('应该打开删除确认对话框', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      await wrapper.vm.handleDelete(mockConfigs[0])

      expect(wrapper.vm.deleteDialogVisible).toBe(true)
      expect(wrapper.vm.currentConfig).toEqual(mockConfigs[0])
    })
  })

  describe('切换状态功能', () => {
    it('应该成功切换启用状态', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockToggleConfigStatus = vi.mocked(modelApi.toggleConfigStatus)
      mockToggleConfigStatus.mockResolvedValue({
        ...mockConfigs[0],
        is_active: false,
      })

      const config = { ...mockConfigs[0] }
      // 模拟 switch 切换：先更新值，再调用处理函数
      config.is_active = !config.is_active
      await wrapper.vm.handleToggleStatus(config)

      expect(mockToggleConfigStatus).toHaveBeenCalledWith(1, false)
      expect(ElMessage.success).toHaveBeenCalledWith('已禁用')
      expect(config.is_active).toBe(false)
    })

    it('应该处理切换失败并显示错误消息', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockToggleConfigStatus = vi.mocked(modelApi.toggleConfigStatus)
      mockToggleConfigStatus.mockRejectedValue(new Error('网络错误'))

      const config = { ...mockConfigs[0], is_active: true }
      // 模拟 switch 切换
      config.is_active = !config.is_active
      await wrapper.vm.handleToggleStatus(config)

      expect(ElMessage.error).toHaveBeenCalled()
      expect(mockToggleConfigStatus).toHaveBeenCalled()
    })

    it('应该处理乐观锁冲突', async () => {
      wrapper = mount(ModelConfigList, {
        global: {
          stubs: {
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-select': true,
            'el-option': true,
            'el-pagination': true,
            'el-switch': true,
            'el-icon': true,
            ModelConfigDialog: true,
          },
        },
      })

      const mockToggleConfigStatus = vi.mocked(modelApi.toggleConfigStatus)
      mockToggleConfigStatus.mockRejectedValue(new Error('配置已被其他用户修改，请刷新'))

      const config = { ...mockConfigs[0] }
      await wrapper.vm.handleToggleStatus(config)

      expect(ElMessage.error).toHaveBeenCalledWith(expect.stringContaining('已被其他用户修改'))
    })
  })
})

// 辅助函数
function afterEach(fn: () => void) {
  // Vitest 会在每个测试后自动清理
}
