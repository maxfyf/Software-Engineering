<script setup lang="js">
import { ref, watch } from 'vue'
import { ElCheckbox, ElEmpty } from 'element-plus'

const props = defineProps({
  candidates: {
    type: Array,
    default: () => [],
    required: true
  },
  modelValue: {
    type: Array,
    default: () => [],
    required: true
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])
const selectedIndices = ref([...props.modelValue])

// 监听外部 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  selectedIndices.value = [...newVal]
}, { deep: true })

// 监听内部选中状态变化，向外发送事件
watch(selectedIndices, (newVal) => {
  emit('update:modelValue', newVal)
  emit('change', newVal)
}, { deep: true })

// 判断某项是否选中
const isSelected = (index) => {
  return selectedIndices.value.includes(index)
}

// 切换某项的选中状态
const toggleItem = (index) => {
  const currentIndex = selectedIndices.value.indexOf(index)
  if (currentIndex === -1) {
    selectedIndices.value.push(index)
  } else {
    selectedIndices.value.splice(currentIndex, 1)
  }
}
</script>

<template>
  <div class="selectable-list">
    <div
        v-for="(item, index) in candidates"
        :key="index"
        class="list-item"
        :class="{ 'is-selected': isSelected(index) }"
        @click="toggleItem(index)"
    >
      <el-checkbox
          :model-value="isSelected(index)"
          @click.stop
          @change="toggleItem(index)"
      >
        {{ item }}
      </el-checkbox>
    </div>
    <div v-if="candidates.length === 0" class="empty-state">
      <el-empty :description="emptyText" :image-size="80" />
    </div>
  </div>
</template>

<style scoped>
.selectable-list {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  border-radius: 5px;
}

.list-item {
  padding: 8px 12px;
  cursor: pointer;
}

.list-item:hover {
  background-color: #c6e2ff;
}

.list-item.is-selected {
  background-color: #ecf5ff;
}

.list-item.is-selected:hover {
  background-color: #c6e2ff;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
}

:deep(.el-checkbox) {
  width: 100%;
  display: flex;
  align-items: center;
}

:deep(.el-checkbox__label) {
  flex: 1;
  word-break: break-word;
}
</style>