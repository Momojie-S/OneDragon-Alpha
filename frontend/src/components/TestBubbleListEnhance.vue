<template>
  <div class="test-container">
    <h1>BubbleListEnhance 测试页面</h1>
    <div class="controls">
      <button @click="addTextMessage">添加文本消息</button>
      <button @click="addChartMessage">添加图表消息</button>
      <button @click="clearMessages">清空消息</button>
    </div>

    <div class="messages-container">
      <BubbleListEnhance
        :list="messages"
        :loading="false"
        :max-height="'600px'"
        :auto-scroll="true"
        class="test-bubble-list"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BubbleListEnhance from './BubbleListEnhance.vue'

// 定义消息类型
type TestMessage = {
  role: 'user' | 'assistant'
  content: string
  placement: 'start' | 'end'
  variant: 'outlined' | 'filled'
  messageType?: 'text' | 'chart'
  chartData?: any
  isMarkdown?: boolean
  typing?: boolean | object
}

const messages = ref<TestMessage[]>([])

// 示例图表数据
const sampleChartData = {
  title: {
    text: '销售趋势',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    data: [150, 230, 224, 218, 135, 147],
    type: 'line',
    smooth: true
  }]
}

// 添加文本消息
const addTextMessage = () => {
  const isUser = messages.value.length % 2 === 0
  messages.value.push({
    role: isUser ? 'user' : 'assistant',
    content: `这是第 ${messages.value.length + 1} 条${isUser ? '用户' : '助手'}消息，包含一些文本内容。`,
    placement: isUser ? 'end' : 'start',
    variant: 'outlined',
    messageType: 'text',
    isMarkdown: !isUser,
    typing: !isUser ? { step: 50, interval: 10 } : false,
    maxWidth: "100%"
  })
}

// 添加图表消息
const addChartMessage = () => {
  messages.value.push({
    role: 'assistant',
    content: '数据分析结果',
    placement: 'start',
    variant: 'outlined',
    messageType: 'chart',
    chartData: sampleChartData,
    maxWidth: "100%"
  })
}

// 清空消息
const clearMessages = () => {
  messages.value = []
}
</script>

<style scoped>
.test-container {
  width: 100%;
  margin: 0 auto;
  padding: 20px;
}

.controls {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.controls button {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.controls button:hover {
  background-color: #66b1ff;
}

.messages-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
}

.test-bubble-list {
  height: 600px;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}
</style>