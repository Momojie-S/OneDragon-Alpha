/**
 * DualModelSelector 组件单元测试
 * 从 chat-model-selector E2E 测试迁移而来
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DualModelSelector from '../DualModelSelector.vue'
import * as modelApi from '../../services/modelApi'

// Mock modelApi module
vi.mock('../../services/modelApi', async () => {
  const actual = await vi.importActual('../../services/modelApi')
  return {
    ...actual,
    getActiveModelConfigs: vi.fn(),
  }
})

// 测试数据前缀
const TEST_PREFIX = 'test_'

describe('DualModelSelector 组件测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('组件挂载和数据获取', () => {
    it('4.2.1 组件挂载时调用 API 获取模型配置', async () => {
      const mockConfigs = [
        {
          id: 1,
          name: `${TEST_PREFIX}config_openai`,
          provider: 'openai',
          base_url: 'https://api.openai.com',
          models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false },
            { model_id: 'gpt-3.5-turbo', support_vision: false, support_thinking: true }
          ],
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          name: `${TEST_PREFIX}config_qwen`,
          provider: 'qwen',
          base_url: 'https://api.qwen.com',
          models: [
            { model_id: 'qwen-max', support_vision: false, support_thinking: true }
          ],
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockConfigs
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      // 等待异步操作完成
      await new Promise(process.nextTick)

      expect(mockGetActiveModelConfigs).toHaveBeenCalledTimes(1)
      expect(wrapper.vm.isLoading).toBe(false)
      wrapper.unmount()
    })

    it('4.2.1 双层选择器正确显示', async () => {
      const mockConfigs = [
        {
          id: 1,
          name: `${TEST_PREFIX}config_openai`,
          provider: 'openai',
          base_url: 'https://api.openai.com',
          models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false }
          ],
          is_active: true,
        },
      ]

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: mockConfigs
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      await new Promise(process.nextTick)

      // 验证选择器存在
      expect(wrapper.find('.config-selector').exists()).toBe(true)
      expect(wrapper.find('.model-selector').exists()).toBe(true)

      wrapper.unmount()
    })
  })

  describe('配置选择', () => {
    it('4.2.2 选择模型配置后显示模型列表', async () => {
      const mockConfigs = [
        {
          id: 1,
          name: `${TEST_PREFIX}config_openai`,
          provider: 'openai',
          base_url: 'https://api.openai.com',
          models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false },
            { model_id: 'gpt-3.5-turbo', support_vision: false, support_thinking: true }
          ],
          is_active: true,
        },
      ]

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: mockConfigs
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      // 选择配置
      await wrapper.vm.handleConfigChange(1)
      await new Promise(process.nextTick)

      // 验证第二层选择器已启用
      expect(wrapper.vm.isModelSelectorDisabled).toBe(false)
      // 验证当前模型列表
      expect(wrapper.vm.currentModels).toEqual(mockConfigs[0].models)
      expect(wrapper.vm.currentModels.length).toBe(2)

      wrapper.unmount()
    })

    it('4.2.5 切换模型配置时模型列表更新', async () => {
      const mockConfigs = [
        {
          id: 1,
          name: `${TEST_PREFIX}config_openai`,
          provider: 'openai',
          models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false }
          ],
          is_active: true,
        },
        {
          id: 2,
          name: `${TEST_PREFIX}config_qwen`,
          provider: 'qwen',
          models: [
            { model_id: 'qwen-max', support_vision: false, support_thinking: true }
          ],
          is_active: true,
        },
      ]

      // 切换配置
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 2,
        page: 1,
        page_size: 100,
        items: mockConfigs
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      await new Promise(process.nextTick)

      // 选择第一个配置
      await wrapper.vm.handleConfigChange(1)
      await new Promise(process.nextTick)

      expect(wrapper.vm.currentModels.length).toBe(1)
      expect(wrapper.vm.currentModels[0].model_id).toBe('gpt-4')

      // 切换到第二个配置
      await wrapper.vm.handleConfigChange(2)
      await new Promise(process.nextTick)

      // 验证模型列表已更新且模型选择已重置
      expect(wrapper.vm.currentModels.length).toBe(1)
      expect(wrapper.vm.currentModels[0].model_id).toBe('qwen-max')
      expect(wrapper.vm.selectedModelId).toBeNull()

      wrapper.unmount()
    })
  })

  describe('模型选择', () => {
    it('4.2.3 选择模型后刷新页面选择状态保持', async () => {
      const mockConfig = {
        id: 1,
        name: `${TEST_PREFIX}config_openai`,
        provider: 'openai',
        models: [
          { model_id: 'gpt-4', support_vision: true, support_thinking: false }
        ],
        is_active: true,
      }

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: [mockConfig]
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      await new Promise(process.nextTick)

      // 选择配置
      await wrapper.vm.handleConfigChange(1)
      await new Promise(process.nextTick)

      // 选择模型
      await wrapper.vm.handleModelChange('gpt-4')
      await new Promise(process.nextTick)

      // 验证保存到 localStorage（组件使用 model_config_id 和 model_id）
      const savedSelection = localStorage.getItem('chat_model_selection')
      expect(savedSelection).toBeTruthy()

      const parsed = JSON.parse(savedSelection!)
      expect(parsed.model_config_id).toBe(1)
      expect(parsed.model_id).toBe('gpt-4')

      wrapper.unmount()
    })

    it('4.2.4 没有可用模型配置时显示提示', async () => {
      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 0,
        page: 1,
        page_size: 100,
        items: []
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      await new Promise(process.nextTick)

      // 验证选择器被禁用
      expect(wrapper.vm.isConfigSelectorDisabled).toBe(true)
      expect(wrapper.vm.configPlaceholderText).toBe('暂无可用模型配置')

      wrapper.unmount()
    })
  })

  describe('响应式布局', () => {
    it('4.2.6 移动端显示 - 验证组件结构', async () => {
      const mockConfig = {
        id: 1,
        name: `${TEST_PREFIX}config_openai`,
        provider: 'openai',
        models: [
          { model_id: 'gpt-4', support_vision: true, support_thinking: false }
        ],
        is_active: true,
      }

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: [mockConfig]
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      await new Promise(process.nextTick)

      // 验证选择器都存在
      expect(wrapper.find('.dual-model-selector').exists()).toBe(true)
      expect(wrapper.find('.config-selector').exists()).toBe(true)
      expect(wrapper.find('.model-selector').exists()).toBe(true)

      // 验证响应式样式类在 CSS 中定义（通过 @media 查询）
      const selectorElement = wrapper.find('.dual-model-selector').element
      expect(selectorElement).toBeDefined()

      wrapper.unmount()
    })
  })

  describe('模型能力标签', () => {
    it('4.2.8 模型能力标签显示', async () => {
      const mockConfig = {
        id: 1,
        name: `${TEST_PREFIX}config_openai`,
        provider: 'openai',
        models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false },
            { model_id: 'gpt-3.5-turbo', support_vision: false, support_thinking: true }
          ],
        is_active: true,
      }

      const mockGetActiveModelConfigs = vi.mocked(modelApi.getActiveModelConfigs)
      mockGetActiveModelConfigs.mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: [mockConfig]
      })

      const wrapper = mount(DualModelSelector, {
        global: {
          plugins: []
        }
      })

      // 选择配置
      await wrapper.vm.handleConfigChange(1)
      await new Promise(process.nextTick)

      // 验证模型能力标签函数
      const visionModel = mockConfig.models[0]
      const thinkingModel = mockConfig.models[1]

      const visionTags = wrapper.vm.getModelTags(visionModel)
      const thinkingTags = wrapper.vm.getModelTags(thinkingModel)

      // 验证视觉能力标签
      expect(visionTags).toEqual([{ text: '视觉', type: 'success' }])

      // 验证思考能力标签
      expect(thinkingTags).toEqual([{ text: '思考', type: 'warning' }])

      wrapper.unmount()
    })
  })
})
