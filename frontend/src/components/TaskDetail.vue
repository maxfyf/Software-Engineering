<script setup>

const props = defineProps({
  currentTask: {
    type: Object,
    default: null
  },

  viewDialogVisible: {
    type: Boolean,
    default: false
  }
})

const closeViewDialog = () => {
  props.viewDialogVisible = false
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未设置'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}
</script>

<template>
  <el-dialog
      v-model="props.viewDialogVisible"
      width="500px"
      center
      :before-close="closeViewDialog"
  >
    <template #header>
      <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;任务详情</span>
    </template>
    <div class="dialog-content-wrapper">
      <p class="dialog-content">
        <span class="key">任务标题：</span>
        {{ props.currentTask.title }}
      </p>
      <p class="dialog-content" v-if="props.currentTask.description !== ''">
        <span class="key">描述：</span>
        {{ props.currentTask.description }}
      </p>
      <p class="dialog-content">
        <span class="key">状态：</span>
        {{ props.currentTask.status }}
      </p>
      <p class="dialog-content">
        <span class="key">优先级：</span>
        {{ props.currentTask.priority }}
      </p>
      <p class="dialog-content" v-if="props.currentTask.deadline !== null">
        <span class="key">截止时间：</span>
        {{ props.currentTask.deadline }}
      </p>
      <p class="dialog-content">
        <span class="key">创建时间：</span>
        {{ formatDate(props.currentTask.createdAt) }}
      </p>
      <p class="dialog-content">
        <span class="key">更新时间：</span>
        {{ formatDate(props.currentTask.updatedAt) }}
      </p>
    </div>
  </el-dialog>
</template>

<style scoped>
.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-content-wrapper {
  overflow-y: auto;
  max-height: 400px;
}

.dialog-content {
  padding: 0 20px;
  font-size: 18px;
}

.key {
  font-weight: bold;
}
</style>