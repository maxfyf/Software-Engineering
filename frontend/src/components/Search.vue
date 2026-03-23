<script setup lang="js">
import { Search } from "@element-plus/icons-vue";
</script>

<script lang="js">
export default {
  name: 'SearchInput',
  props: {
    // 搜索数据集
    data: {
      type: Array,
      default: []
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
    }
  },

  data() {
    return {
      searchText: this.value,
      showDropdown: false,
      fixedDropdownStyle: {
        position: 'fixed',
        width: '0px',
        top: '0px',
        left: '0px',
        maxHeight: `${this.maxHeight}px`
      },
      value: '',
      hasDropdownPosition: false
    };
  },

  computed: {
    // 筛选前缀匹配结果
    filteredOptions() {
      if (!this.searchText) return []

      const keyword = this.searchText
      if (keyword === '') return []

      return this.data.filter(str => {
        if (!str) return false
        return str.startsWith(keyword)
      })
    }
  },

  watch: {
    // 监听value
    value(newVal) {
      if (newVal !== this.searchText) {
        this.searchText = newVal
      }
    },

    // 监听searchText
    searchText(newVal) {
      this.showDropdown = !!newVal
      this.$emit('input', this.searchText)
      this.$emit('search', {
        keyword: this.searchText,
        results: this.filteredOptions
      })

      if (!this.hasDropdownPosition) {
        this.setDropdownPosition()
        this.hasDropdownPosition = true
      }
    }
  },

  methods: {
    // 搜索框获得焦点
    handleFocus() {
      if (this.searchText) {
        this.showDropdown = true
      }
    },

    // 搜索框失去焦点
    handleBlur() {
      setTimeout(() => {
        this.showDropdown = false
      }, 100)
    },

    // 获取输入框位置
    getInputRect() {
      const inputEl = this.$refs.inputRef?.$el?.querySelector('.el-input__inner') ||
          this.$el.querySelector('input')
      if (!inputEl) return null
      return inputEl.getBoundingClientRect()
    },

    // 设置下拉框位置
    setDropdownPosition() {
      this.$nextTick(() => {
        const rect = this.getInputRect()
        if (!rect) return;

        const height = rect.height;
        const marginWidth = 32 - height / 2;

        const top = rect.bottom
        const left = rect.left - marginWidth
        const width = rect.width + 2 * marginWidth

        this.fixedDropdownStyle = {
          ...this.fixedDropdownStyle,
          position: 'fixed',
          width: `${width}px`,
          top: `${top}px`,
          left: `${left}px`,
          bottom: 'auto',
          maxHeight: `${this.maxHeight}px`
        };
      });
    },

    // 选中下拉框中的某一项
    selectOption(str) {
      this.handleBlur();
      this.value = str
      this.searchText = str

      this.$emit('select', str)
      this.$emit('input', str)

      if (this.onSelect) {
        this.onSelect(str)
      }
    },

    // 对前缀匹配的文本中的HTML特殊符号转义
    match(str) {
      if (str === null || str === undefined) return '';

      const htmlEscapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
      };

      return str.replace(/[&<>"'/`=]/g, function(char) {
        return htmlEscapeMap[char];
      });
    }
  }
}
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
          @click="selectOption(item)"
      >
        <span v-html="match(item)"></span>
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
</style>