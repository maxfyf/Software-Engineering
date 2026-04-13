<script setup>
import { computed } from 'vue';
import { finishTask, highlightTaskId, removeTask } from "@/store/user.js";
import { Check, Delete, Edit, View } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

const props = defineProps({
  tasks: {
    type: Array,
    required: true,
    default: () => []
  },

  router: {
    type: Object,
    required: true
  },

  currentPage: {
    type: Number,
    default: 1
  },

  pageSize: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['pageChange', 'viewDetail'])

const total = computed(() => props.tasks.length)
const pageData = computed(() => {
  const start = (props.currentPage - 1) * props.pageSize
  const end = start + props.pageSize
  return props.tasks.slice(start, end)
})

// 切换页面
const handleCurrentChange = (page) => {
  emit('pageChange', page)
}

// 表格行样式回调
const tableRowClassName = ({ row }) => {
  if (row.id === highlightTaskId.value) {
    return 'highlight-row'
  }
  return ''
}

// 查看详情
const viewDetail = (row) => {
  highlightTaskId.value = row.id
  emit('viewDetail', row)
}

// 更改状态
const checkTask = (row) => {
  highlightTaskId.value = row.id
  finishTask(row.id)
  ElMessage.success('任务已完成')
}

// 编辑任务
const editTask = (row) => {
  console.log('编辑任务:', row)
  highlightTaskId.value = row.id
  props.router.push({
    path: '/task/edit',
    query: {
      isNew: 'false',
      taskId: row.id
    }
  })
}

// 删除任务
const deleteTask = (row) => {
  highlightTaskId.value = null
  ElMessageBox.confirm(
      `确定要删除任务"${row.title}"吗？`,
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(() => {
    removeTask(row.id)
    ElMessage.success('任务已删除')
  }).catch(() => {
    console.log('取消删除')
  })
}
</script>

<template>
  <el-row>
    <el-col>
      <el-table :data="pageData" stripe class="task-table" :row-class-name="tableRowClassName" :key="highlightTaskId">
        <el-table-column prop="title" label="任务名称" min-width="50%" align="left" />
        <el-table-column prop="status" label="状态" min-width="20%" align="center" />
        <el-table-column prop="priority" label="优先级" min-width="15%" align="center" />
        <el-table-column fixed="right" label="操作" min-width="15%" align="center">
          <template v-slot:default="scope">
            <el-button link type="text" @click="viewDetail(scope.row)">
              <el-icon>
                <View/>
              </el-icon>
            </el-button>

            <el-button v-if="scope.row.status !== '已完成'" link type="text" @click="checkTask(scope.row)">
              <el-icon>
                <Check/>
              </el-icon>
            </el-button>
            <el-button v-else link type="text" disabled>
              <el-icon>
                <Check/>
              </el-icon>
            </el-button>

            <el-button link type="text" @click="editTask(scope.row)">
              <el-icon>
                <Edit/>
              </el-icon>
            </el-button>

            <el-button link type="text" class="delete-button" @click="deleteTask(scope.row)">
              <el-icon>
                <Delete/>
              </el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-col>
  </el-row>

  <el-pagination
      @current-change="handleCurrentChange"
      :current-page="props.currentPage"
      :page-size="props.pageSize"
      layout="prev, pager, next"
      :total="total"
      class="pagination"
  />
</template>

<style scoped>
.task-table {
  width: 100%;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-pagination .el-pager li) {
  background-color: transparent !important;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background-color: transparent !important;
  color: black !important;
}

:deep(.el-table__row.highlight-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row.highlight-row td) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row--striped.highlight-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row--striped.highlight-row td) {
  background-color: #ecf5ff !important;
}

.delete-button:hover {
  color: #f56c6c !important;
}
</style>