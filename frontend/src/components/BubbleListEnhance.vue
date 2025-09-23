<script setup lang="ts">
import { ref, computed, onUnmounted, watch, onMounted, nextTick } from 'vue'
import type {
  BubbleListItemProps,
  BubbleListProps
} from 'vue-element-plus-x/types/BubbleList';
import { BubbleList, Typewriter } from 'vue-element-plus-x';
import * as echarts from 'echarts'

// 定义增强的消息类型
interface EnhancedMessage extends BubbleListItemProps {
  messageType?: 'text' | 'chart'
  chartData?: any
  isMarkdown?: boolean
  typing?: boolean | object
}

// 定义组件属性
interface BubbleListEnhanceProps extends BubbleListProps<EnhancedMessage> {
}

// 定义组件事件
const emit = defineEmits<{
  scrollComplete: []
  complete: [instance: any, index: number]
}>()

const props = withDefaults(defineProps<BubbleListEnhanceProps>(), {
  alwaysShowScrollbar: false
})

const chartContainers = ref<Map<number, HTMLElement>>()
const chartInstances = ref<Map<number, echarts.ECharts>>()
const bubbleListRef = ref<InstanceType<typeof BubbleList>>()
const isMounted = ref(true)
const isResizing = ref(false)
const previousWidth = ref<number>(0)


const getContainerParent = (container: HTMLElement): HTMLElement | null => {
  // 找到上层的 el-bubble-content-wrapper 元素
  let parentWrapper: HTMLElement | null = null
  let parent = container.parentElement
  while (parent && !parentWrapper) {
    if (parent.classList.contains('el-bubble-content-wrapper')) {
      parentWrapper = parent
    }
    parent = parent.parentElement
  }

  return parentWrapper
}

/**
 * 调整容器宽度到父容器宽度的95%
 * @param container 图表容器元素
 * @returns Promise<boolean> 是否成功调整了容器宽度
 */
const adjustContainerWidth = async (container: HTMLElement): Promise<boolean> => {
  // 找到上层的 el-bubble-content-wrapper 元素
  let parentWrapper: HTMLElement | null = getContainerParent(container)

  if (!parentWrapper) {
    console.error('Failed to find parent wrapper element', container)
    return false
  }

  // 无论容器当前宽度如何，都需要调整到95%
  if (parentWrapper.clientWidth > 0) {
    const wrapperWidth = parentWrapper.clientWidth
    const targetWidth = Math.floor(wrapperWidth * 0.95)
    container.style.width = `${targetWidth}px`
  } else {
    console.error('Parent wrapper width is 0')
    return false
  }

  return true
}



/**
 * 初始化 ECharts 图表
 * 调整容器宽度后再初始化echart实例
 * @param index 图表索引
 * @param container 图表容器元素
 * @param chartData ECharts 配置数据
 * @returns 图表实例，初始化失败返回 null
 */
const initChart = async (index: number, container: HTMLElement, chartData: any) => {
  if (!chartContainers.value) {
    chartContainers.value = new Map()
  }
  if (!chartInstances.value) {
    chartInstances.value = new Map()
  }

  chartContainers.value.set(index, container)

  try {
    // 立即设置标记位，防止ResizeObserver触发
    isResizing.value = true

    const widthAdjusted = await adjustContainerWidth(container)
    if (!widthAdjusted) {
      return null
    }

    const chart = echarts.init(container)

    if (!chartData || typeof chartData !== 'object') {
      throw new Error('Invalid chart data format')
    }

    chart.setOption(chartData)
    chartInstances.value.set(index, chart)

    // 等待ResizeObserver处理完所有事件
    await new Promise(resolve => setTimeout(resolve, 200))

    return chart
  } catch (error) {
    console.error(`Failed to initialize chart for index ${index}:`, error)
    throw error
  } finally {
    // 重置标记位
    isResizing.value = false
  }
}

const destroyChart = (index: number) => {
  if (chartInstances.value?.has(index)) {
    const chart = chartInstances.value.get(index)!
    chart.dispose()
    chartInstances.value.delete(index)
    chartContainers.value?.delete(index)
  }
}

onUnmounted(() => {
  isMounted.value = false

  // 清理图表实例
  if (chartInstances.value) {
    chartInstances.value.forEach((chart, index) => {
      try {
        chart.dispose()
      } catch (error) {
        console.error(`Failed to dispose chart ${index}:`, error)
      }
    })
    chartInstances.value.clear()
  }

  if (chartContainers.value) {
    chartContainers.value.clear()
  }

  // 清理定时器
  if (bubbleListResizeTimer) {
    clearTimeout(bubbleListResizeTimer)
    bubbleListResizeTimer = null
  }

  // 清理观察者
  if (bubbleListResizeObserver) {
    bubbleListResizeObserver.disconnect()
    bubbleListResizeObserver = null
  }
})

let bubbleListResizeObserver: ResizeObserver | null = null
let bubbleListResizeTimer: NodeJS.Timeout | null = null

const setupResizeObserver = () => {
  if (!bubbleListRef.value?.$el) {
    console.warn('Bubble list element not available')
    return
  }

  const bubbleListElement = bubbleListRef.value.$el

  if (bubbleListResizeObserver) {
    bubbleListResizeObserver.disconnect()
  }

  bubbleListResizeObserver = new ResizeObserver((entries) => {
    if (!isMounted.value || isResizing.value) return

    const { width, height } = entries[0].contentRect

    // 只有宽度改变时才触发图表调整
    if (width !== previousWidth.value) {
      if (bubbleListResizeTimer) {
        clearTimeout(bubbleListResizeTimer)
      }

      bubbleListResizeTimer = setTimeout(() => {
        console.log(`Bubble list width changed: ${previousWidth.value} -> ${width}`)
        if (isMounted.value && chartInstances.value?.size > 0) {
          resizeAllCharts(width).catch(error => { console.error('Failed to resize charts:', error) })
        }
      }, 1000)
    }
  })

  bubbleListResizeObserver.observe(bubbleListElement)
}

onMounted(() => {
  isMounted.value = true
  nextTick(() => {
    setupResizeObserver()
  })
})



/**
 * 调整所有图表容器的宽度并重新调整图表大小
 * @param newWidth 新的宽度值，用于更新previousWidth
 */
const resizeAllCharts = async (newWidth?: number) => {
  if (!isMounted.value || !chartInstances.value || chartInstances.value.size === 0) {
    return
  }

  try {
    // 立即设置标记位，防止ResizeObserver触发
    isResizing.value = true

    // 遍历所有图表实例
    for (const [index, chart] of chartInstances.value) {
      try {
        // 获取对应的容器
        const container = chartContainers.value?.get(index)
        if (!container) {
          continue
        }

        // 调用之前定义的adjustContainerWidth函数调整容器宽度
        const widthAdjusted = await adjustContainerWidth(container)
        if (!widthAdjusted) {
          continue
        }

        // 调用图表的resize方法
        chart.resize()

      } catch (error) {
        console.error(`Failed to resize chart ${index}:`, error)
      }
    }

    // 更新previousWidth为新的宽度
    if (newWidth !== undefined) {
      previousWidth.value = newWidth
    }

    // 等待ResizeObserver处理完所有事件
    await new Promise(resolve => setTimeout(resolve, 200))

  } catch (error) {
    console.error('Failed to resize all charts:', error)
  } finally {
    // 重置标记位
    isResizing.value = false
  }
}



watch(
  () => props.list,
  (newList) => {
    nextTick(() => {
      const contentList = bubbleListRef.value?.$el.querySelectorAll('.el-bubble-content') || []

      for (let i = 0; i < newList.length; i++) {
        const item = newList[i]
        const index = i

        if (item.messageType === 'chart' && item.chartData && !chartInstances.value?.has(index)) {
          if (index >= contentList.length) {
            console.error('Index out of range:', index)
            continue
          }

          const containers = contentList[index].querySelectorAll('.content-chart') || []
          if (containers.length === 0) {
            console.error('No chart container found for index:', index)
            continue
          }

          initChart(index, containers[0] as HTMLElement, item.chartData)
            .catch(error => {
              console.error(`Failed to initialize chart for index ${index}:`, error)
            })
        }
      }
    })
  },
  { deep: true, immediate: true }
)
</script>

<template>
  <BubbleList
    ref="bubbleListRef"
    :list="list"
    :max-height="maxHeight"
    :show-back-button="showBackButton"
    :back-button-threshold="backButtonThreshold"
    :btn-color="btnColor"
    :always-show-scrollbar="alwaysShowScrollbar"
    :trigger-indices="triggerIndices"
    @scroll-complete="emit('scrollComplete')"
    @complete="emit('complete', $event)"
  >
    <template #avatar="{ item }">
      <div class="avatar-wrapper">
        <img
          :src="item.role === 'assistant' ? 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png' : 'https://avatars.githubusercontent.com/u/76239030?v=4'"
          :alt="item.role === 'assistant' ? 'AI' : 'User'"
          class="avatar-image"
        >
      </div>
    </template>

    <template #header="{ item }">
      <div class="header-wrapper">
        <div class="header-name">
          {{ item.role === 'assistant' ? 'OneDragon-Alpha' : 'You' }}
        </div>
      </div>
    </template>

    <template #content="{ item, index }">
      <div class="content-wrapper">
        <div v-if="item.messageType === 'text' || !item.messageType" class="content-text">
          <Typewriter
            :content="item.content"
            :is-markdown="item.isMarkdown"
            :typing="item.typing"
          />
        </div>

        <div
          v-else-if="item.messageType === 'chart'"
          class="content-chart"
        ></div>
      </div>
    </template>

    <template #footer="{ item }">
    </template>

    <template #loading="{ item }">
    </template>
  </BubbleList>
</template>

<style scoped lang="less">

.avatar-wrapper {
  .avatar-image {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
  }
}

.header-wrapper {
  .header-name {
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }
}

.content-wrapper {
  .content-text {
    line-height: 1.5;
  }

  .content-chart {
    margin: 8px 0;
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    width: 100%;
    min-height: 400px;
  }
}

.footer-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;

  .footer-actions {
    display: flex;
    gap: 8px;
  }

  .footer-time {
    font-size: 12px;
    color: #999;
  }
}

.loading-container {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 14px;
}
</style>
