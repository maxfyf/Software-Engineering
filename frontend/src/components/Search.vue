<script setup lang="js">
import { Search } from "@element-plus/icons-vue";
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  // 搜索数据集
  dataset: {
    type: Array,
    required: true
  },
  // 是否显示辅助信息
  showAux: {
    type: Boolean,
    default: false
  },
  // 下拉框最大高度
  maxHeight: {
    type: Number,
    default: 200
  },
  // 回调函数
  onSelect: {
    type: Function,
    default: null
  },
  // v-model 支持
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['input', 'search', 'select', 'update:modelValue'])

// 响应式数据
const searchText = ref(props.modelValue)
const showDropdown = ref(false)
const hasDropdownPosition = ref(false)
const blurTimeout = ref(null)
const selectingOption = ref(false)

const fixedDropdownStyle = ref({
  position: 'fixed',
  width: '0px',
  top: '0px',
  left: '0px',
  maxHeight: `${props.maxHeight}px`
})

// 计算属性：筛选前缀匹配结果
const filteredOptions = computed(() => {
  if (!searchText.value) return []
  const keyword = searchText.value
  if (keyword === '') return []

  return props.dataset.filter(d => {
    if (!d) return false
    const searchText = d.searchText ?? d.data
    return searchText.includes(keyword) || d.data.includes(keyword) || d.aux?.includes(keyword)
  })
})

// 监听 modelValue 变化（外部修改）
watch(() => props.modelValue, (newVal) => {
  if (newVal !== searchText.value) {
    searchText.value = newVal
  }
})

// 监听 searchText 变化
watch(searchText, (newVal) => {
  if (selectingOption.value) {
    showDropdown.value = false
    return
  }
  showDropdown.value = !!newVal
  emit('update:modelValue', newVal)
  emit('input', newVal) // 兼容旧版 input 事件
  emit('search', {
    keyword: newVal,
    results: filteredOptions.value
  })

  if (!hasDropdownPosition.value) {
    setDropdownPosition()
    hasDropdownPosition.value = true
  }
})

// 获取输入框 DOM 元素
const getInputRect = () => {
  const inputEl = document.querySelector('.el-input__inner') || document.querySelector('input')
  if (!inputEl) return null
  return inputEl.getBoundingClientRect()
}

// 设置下拉框位置
const setDropdownPosition = () => {
  nextTick(() => {
    const rect = getInputRect()
    if (!rect) return

    const height = rect.height
    const marginWidth = 32 - height / 2

    const top = rect.bottom
    const left = rect.left - marginWidth
    const width = rect.width + 2 * marginWidth

    fixedDropdownStyle.value = {
      ...fixedDropdownStyle.value,
      position: 'fixed',
      width: `${width}px`,
      top: `${top}px`,
      left: `${left}px`,
      bottom: 'auto',
      maxHeight: `${props.maxHeight}px`
    }
  })
}

// 搜索框获得焦点
const handleFocus = () => {
  if (searchText.value) {
    showDropdown.value = true
  }
  if (blurTimeout.value) {
    clearTimeout(blurTimeout.value)
    blurTimeout.value = null
  }
}

// 搜索框失去焦点
const handleBlur = () => {
  blurTimeout.value = setTimeout(() => {
    showDropdown.value = false
    blurTimeout.value = null
  }, 150)
}

// 选中下拉项
const selectOption = (item) => {
  if (blurTimeout.value) {
    clearTimeout(blurTimeout.value)
    blurTimeout.value = null
  }

  selectingOption.value = true
  searchText.value = item?.data
  showDropdown.value = false

  emit('select', item)
  emit('update:modelValue', item?.data)
  emit('input', item?.data)

  if (props.onSelect) {
    props.onSelect(item)
  }

  nextTick(() => {
    selectingOption.value = false
  })
}

// HTML特殊字符转义
const match = (str) => {
  if (str === null || str === undefined) return ''

  const htmlEscapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  }

  return str.replace(/[&<>"'/`=]/g, char => htmlEscapeMap[char])
}

// 组件挂载后初始化位置
onMounted(() => {
  if (searchText.value) {
    setDropdownPosition()
    hasDropdownPosition.value = true
  }
})
</script>

<!-- 搜索输入框 -->
<template>
  <div class="search-wrapper">
    <!-- 搜索框 -->
    <el-input
        ref="inputRef"
        v-model="searchText"
        placeholder="搜索"
        clearable
        @focus="handleFocus"
        @blur="handleBlur"
    >
      <template #prefix>
        <el-icon>
          <Search />
        </el-icon>
      </template>
    </el-input>

    <!-- 下拉匹配结果框 -->
    <div
        v-show="showDropdown && searchText"
        class="search-dropdown"
        :style="fixedDropdownStyle"
    >
      <div
          v-if="filteredOptions.length === 0"
          class="no-match"
      >
          未找到匹配结果
      </div>
      <div
          v-else
          v-for="(item, idx) in filteredOptions"
          :key="idx"
          class="dropdown-item"
          @mousedown.prevent="selectOption(item)"
      >
        <span v-html="match(item?.data)"/>
        <span v-if="showAux" class="aux">
          &nbsp;&nbsp;&nbsp;
          <span v-html="match(item?.aux)"/>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-wrapper {
  display: inline-block;
  width: 100%;
  height: 100%;
}

.search-wrapper :deep(.el-input__wrapper) {
  background-color: #f5f5f5;
  border-radius: 999px;
  border: 1px solid #dfdfdf;
}

.search-wrapper :deep(.el-input__wrapper):focus {
  border-color: #409eff;
  background-color: white;
}

.search-dropdown {
  background-color: white;
  border: 1px solid #e7e7e7;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
  margin-top: 1px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  z-index: 100;
}

:deep(.search-dropdown) {
  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
    background: transparent;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--el-color-info-light-8);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background-color: var(--el-color-info);
  }
}

:deep(.search-dropdown) {
  scrollbar-width: thin;
  scrollbar-color: var(--el-color-info-light-8) transparent;
}

.no-match {
  padding: 8px 16px;
  font-size: 14px;
  color: #606060;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-item {
  padding: 8px 16px;
  font-size: 14px;
  color: #606060;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-item:hover:not(.no-result) {
  background-color: #f5f7fa;
}

.aux {
  color: lightgrey;
  font-style: italic;
}
</style>