import { describe, it, expect, vi } from 'vitest'

import { mount } from '@vue/test-utils'
import App from '../App.vue'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/' }),
  useRouter: () => ({ push: vi.fn() }),
}))

describe('App', () => {
  it('mounts renders properly', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          'router-view': true,
        },
      },
    })
    // 验证应用正常渲染
    expect(wrapper.exists()).toBe(true)
  })
})
