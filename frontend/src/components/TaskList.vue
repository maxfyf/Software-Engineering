<script setup lang="js">
import { computed, ref, h } from 'vue';
import { useRoute, useRouter } from 'vue-router'
import {
  finishTask,
  startTask as startTaskAction,
  highlightTaskId,
  removeTask,
  currentUser,
  teamList,
  taskList
} from "@/store/user.js";
import { handleEnter } from "@/utils/routeManager.js"
import { View, CaretRight, Check, Edit, Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox, ElCheckbox } from "element-plus";

const props = defineProps({
  tasks: {
    type: Array,
    required: true,
    default: () => []
  },

  showAssignee: {
    type: Boolean,
    default: false
  },

  isAdmin: {
    type: Boolean,
    default: false
  },

  isTeamSpace: {
    type: Boolean,
    default: false
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

const route = useRoute();
const router = useRouter();

const emit = defineEmits(['pageChange'])

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

// 查看任务详情
const viewTaskDetail = (row) => {
  console.log('查看任务详情:', row)
  highlightTaskId.value = row.id

  const newPage = {
    path: 'detail',
    params: [
      {
        key: 'showAssignee',
        value: props.showAssignee
      },
      {
        key: 'taskId',
        value: row.id
      }
    ]
  }
  handleEnter(route, router, newPage)
}

// 开始任务
const startTask = async (row) => {
  highlightTaskId.value = row.id
  const ok = await startTaskAction(row.id)
  if (ok) {
    ElMessage.success('任务已开始')
  }
}

// 完成任务
const checkTask = async (row) => {
  // 检查是否存在未完成的前置任务
  const predecessorList = row.predecessor || []
  if (predecessorList.length > 0) {
    const hasUnfinished = predecessorList.some(predItem => {
      // predecessor 可能是标题或ID
      let predTask
      if (typeof predItem === 'number') {
        predTask = taskList.value.find(t => t.id === predItem)
      } else {
        predTask = taskList.value.find(t => t.title === predItem || t.id === predItem)
      }
      return predTask && predTask.status !== '已完成'
    })
    if (hasUnfinished) {
      ElMessage.error('存在未完成的前置任务，无法完成此任务')
      return
    }
  }
  highlightTaskId.value = row.id
  const ok = await finishTask(row.id)
  if (ok) {
    ElMessage.success('任务已完成')
  }
}

// 编辑任务
const editTask = (row) => {
  console.log('编辑任务:', row)
  highlightTaskId.value = row.id

  const newPage = {
    path: 'edit',
    params: [
      {
        key: 'isNew',
        value: false
      },
      {
        key: 'taskId',
        value: row.id
      }
    ]
  }
  handleEnter(route, router, newPage)
}

// 判断当前用户是否为任务负责人
const isCurrentAssignee = (task) => {
  const assignee = task.assignee
  if (Array.isArray(assignee)) {
    return assignee.includes(currentUser.username)
  }
  return assignee === currentUser.username
}

// 判断当前用户是否为任务所属团队的管理员（与团队空间逻辑一致）
const isTaskTeamAdmin = (task) => {
  if (!task.team) return false
  const team = teamList.value.find(t => t.title === task.team)
  if (!team) return false
  return team.owner === currentUser.username || team.admin?.includes(currentUser.username)
}

// 删除任务
const cascade = ref(false)    // 级联标记
const deleteTask = (row) => {
  ElMessageBox.confirm(
      h('div', [
        h('p', `确定要删除任务"${row.title}"吗？`),
        h(ElCheckbox, {
          modelValue: cascade.value,
          'onUpdate:modelValue': (val) => {
            cascade.value = val
          },
          style: {
            position: 'absolute',
            bottom: '13px',
            left: '20px',
            zIndex: 1
          }
        }, () => '级联删除')
      ]),
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(() => {
    highlightTaskId.value = null
    // 传递 cascade 参数给后端
    removeTask(row.id, cascade.value)
    ElMessage.success('任务已删除')
  }).catch(() => {
    console.log('取消删除')
  })
}
</script>

<template>
  <el-row>
    <el-col>
      <el-table
          :data="pageData"
          empty-text="暂无任务"
          stripe
          class="task-table"
          :row-class-name="tableRowClassName"
          :key="highlightTaskId"
      >
        <el-table-column
            prop="title"
            label="任务名称"
            :min-width="showAssignee ? '38%' : '40%'"
            align="left"
        />
        <el-table-column
            v-if="showAssignee"
            prop="assignee"
            label="负责人"
            min-width="25%"
            align="center"
        />
        <el-table-column
            prop="status"
            label="状态"
            :min-width="showAssignee ? '7%' : '20%'"
            align="center"
        />
        <el-table-column
            prop="priority"
            label="优先级"
            :min-width="showAssignee ? '10%' : '20%'"
            align="center"
        />
        <el-table-column
            fixed="right"
            label="操作"
            min-width="20%"
            align="center"
        >
          <template v-slot:default="scope">
            <el-button
                link
                type="text"
                @click="viewTaskDetail(scope.row)"
            >
              <el-icon>
                <View/>
              </el-icon>
            </el-button>

            <!-- 个人任务、负责人、团队管理者/拥有者可见 -->
            <!-- 任务模块中，团队任务只有负责人能修改状态 -->
            <el-button
                link
                type="text"
                v-if="((scope.row.team === null && scope.row.owner === currentUser.username) ||
                  (scope.row.team !== null && (isTeamSpace ? (isCurrentAssignee(scope.row) || isTaskTeamAdmin(scope.row)) : isCurrentAssignee(scope.row))) &&
                  scope.row.status === '待办')"
                @click="startTask(scope.row)"
            >
              <el-icon>
                <CaretRight/>
              </el-icon>
            </el-button>
            <el-button
                link
                type="text"
                v-else-if="((scope.row.team === null && scope.row.owner === currentUser.username) ||
                  (scope.row.team !== null && (isTeamSpace ? (isCurrentAssignee(scope.row) || isTaskTeamAdmin(scope.row)) : isCurrentAssignee(scope.row))) &&
                  scope.row.status === '进行中')"
                @click="checkTask(scope.row)"
            >
              <el-icon>
                <Check/>
              </el-icon>
            </el-button>

            <!-- 编辑按钮：任务模块中团队任务不显示；团队空间中按权限显示 -->
            <el-button
                link
                type="text"
                v-if="(scope.row.team === null && scope.row.owner === currentUser.username) ||
                  (scope.row.team !== null && isTeamSpace && (scope.row.owner === currentUser.username || isTaskTeamAdmin(scope.row)))"
                @click="editTask(scope.row)"
            >
              <el-icon>
                <Edit/>
              </el-icon>
            </el-button>

            <!-- 删除按钮：任务模块中团队任务不显示；团队空间中按权限显示 -->
            <el-button
                link
                type="text"
                class="delete-button"
                v-if="(scope.row.team === null && scope.row.owner === currentUser.username) ||
                  (scope.row.team !== null && isTeamSpace && (scope.row.owner === currentUser.username || isTaskTeamAdmin(scope.row)))"
                @click="deleteTask(scope.row)"
            >
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