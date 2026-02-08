/**
 * ModelSelector 组件单元测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { ElSelect } from 'element-plus'
import ModelSelector from '../ModelSelector.vue'
import * as modelApi from '../../services/modelApi'
import type { ModelConfig } from '../../services/modelApi'

// Mock modelApi module
vi.mock('../../services/modelApi', () => ({
  getActiveModelConfigs: vi.fn(),
}))

describe('ModelSelector.vue', () => {
  // Mock 数据
  const mockModelConfigs: ModelConfig[] = [
    {
      id: 1,
      name: 'DeepSeek 官方',
      provider: 'openai',
      base_url: 'https://api.deepseek.com',
      models: [
        { model_id: 'deepseek-chat', support_vision: true, support_thinking: false },
        { model_id: 'deepseek-coder', support_vision: false, support_thinking: true },
      ],
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      name: 'OpenAI GPT-4',
      provider: 'openai',
      base_url: 'https://api.openai.com',
      models: [
        { model_id: 'gpt-4', support_vision: true, support_thinking: true },
      ],
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ]

  beforeEach(() => {
    // 清除 localStorage
    localStorage.clear()
    // 清除所有 mock
    vi.clearAllMocks()
  })

  describe('组件挂载和数据获取', () => {
    it('4.1.2 组件挂载时调用 API 获取模型配置', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      // 等待异步操作完成
      await new Promise(process.nextTick)

      expect(mockGetActiveModelConfigs).toHaveBeenCalledTimes(1)
      wrapper.unmount()
    })

    it('4.1.3 加载状态正确显示', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      // 返回一个不会立即 resolve 的 Promise
      let resolvePromise: (value: any) => void
      mockGetActiveModelConfigs.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        })
      )

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      // 检查初始加载状态
      expect(wrapper.vm.isLoading).toBe(true)

      // 等待一下让 loading 设置生效
      await new Promise(process.nextTick)

      // 检查占位符文本
      const selectEl = wrapper.findComponent(ElSelect)
      expect(selectEl.props('placeholder')).toBe('加载中...')

      // 清理
      resolvePromise!({
        total: 0,
        page: 1,
        page_size: 100,
        items: [],
      })
      await new Promise(process.nextTick)
      wrapper.unmount()
    })
  })

  describe('错误处理', () => {
    it('4.1.4 错误状态正确处理', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockRejectedValue(new Error('网络错误'))

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      // 等待异步操作完成
      await new Promise(process.nextTick)

      expect(wrapper.vm.error).toBe('网络错误')
      expect(wrapper.vm.isLoading).toBe(false)

      wrapper.unmount()
    })
  })

  describe('模型配置显示', () => {
    it('4.1.5 有可用模型时选择器可用', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      expect(wrapper.vm.hasAvailableModels).toBe(true)
      expect(wrapper.vm.isDisabled).toBe(false)

      wrapper.unmount()
    })

    it('4.1.6 无可用模型时选择器禁用', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 0,
        page: 1,
        page_size: 100,
        items: [],
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      expect(wrapper.vm.hasAvailableModels).toBe(false)
      expect(wrapper.vm.isDisabled).toBe(true)

      wrapper.unmount()
    })
  })

  describe('localStorage 持久化', () => {
    it('4.1.7 模型选择变化时正确保存到 localStorage', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      // 模拟用户选择模型
      await wrapper.vm.handleModelChange(2)

      // 检查 localStorage
      const savedId = localStorage.getItem('chat-selected-model-config-id')
      expect(savedId).toBe('2')

      wrapper.unmount()
    })

    it('4.1.8 组件挂载时从 localStorage 恢复选择', async () => {
      // 预设 localStorage
      localStorage.setItem('chat-selected-model-config-id', '2')

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      expect(wrapper.vm.selectedModelId).toBe(2)

      wrapper.unmount()
    })
  })

  describe('默认值处理', () => {
    it('4.1.9 保存的 ID 无效时选择第一个可用模型', async () => {
      // 预设一个无效的 ID（不存在于列表中）
      localStorage.setItem('chat-selected-model-config-id', '999')

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      // 应该选择第一个可用的模型（id=1）
      expect(wrapper.vm.selectedModelId).toBe(1)

      wrapper.unmount()
    })

    it('没有保存的选择时选择第一个可用模型', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockModelConfigs,
      })

      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      await new Promise(process.nextTick)

      // 应该选择第一个可用的模型（id=1）
      expect(wrapper.vm.selectedModelId).toBe(1)

      wrapper.unmount()
    })
  })

  describe('选项显示格式', () => {
    it('4.1.10 选项显示格式正确（配置名称 + 模型数量）', () => {
      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      const config = mockModelConfigs[0]
      const label = wrapper.vm.formatOptionLabel(config)

      expect(label).toBe('DeepSeek 官方 (2个模型)')

      wrapper.unmount()
    })

    it('4.1.11 配置名称超长时正确截断', () => {
      const wrapper = mount(ModelSelector, {
        global: {
          components: {
            ElSelect,
          },
        },
      })

      // 创建一个超过 30 个字符的配置名称（使用英文字母确保长度）
      const longName = 'This is a very very very long configuration name that should be truncated'
      const longNameConfig: ModelConfig = {
        ...mockModelConfigs[0],
        name: longName,
      }

      const truncated = wrapper.vm.truncateConfigName(longNameConfig.name)

      // 应该被截断并添加省略号
      expect(truncated.length).toBeLessThan(longName.length)
      expect(truncated).toContain('...')
      expect(truncated).not.toBe(longNameConfig.name)
      // 截断后应该是 30 个字符 + '...'
      expect(truncated.length).toBe(33)

      wrapper.unmount()
    })
  })
})
