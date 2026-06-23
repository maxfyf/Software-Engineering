<script setup lang="js">
import { computed, ref, h, defineComponent } from 'vue';
import { useRoute, useRouter } from 'vue-router'
import {
  finishTask,
  startTask as startTaskAction,
  highlightTaskId,
  removeTask,
  currentUser,
  getUserProfile,
  userProfileMap,
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

// 寻找未完成的前置任务
const findUnfinishedPredecessor = (task) => {
  const predecessors = task.predecessor || []
  for (const predItem of predecessors) {
    const predTask = taskList.value.find(t => Number(t.id) === Number(predItem))
    if (!predTask) continue
    if(predTask.status !== '已完成') return predTask
  }
  return null
}

// 完成任务
const checkTask = async (row) => {
  // 检查是否存在未完成的前置任务
  const blocker = findUnfinishedPredecessor(row)
  if (blocker) {
    ElMessage.error(`前置任务「${blocker.title}」未完成，无法完成当前任务`)
    return
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

// 判断是否展示进展任务按钮
const showUpdateTask = (item) => {
  if(item.owner === currentUser.username) return true
  if(item.team === null) return true
  if(props.isTeamSpace) {
    return isCurrentAssignee(item) || isTaskTeamAdmin(item)
  }
  else {
    return isCurrentAssignee(item)
  }
}

// 判断当前用户是否为任务所属团队的管理员（与团队空间逻辑一致）
const isTaskTeamAdmin = (task) => {
  if (!task.team) return false
  const team = teamList.value.find(t => t.title === task.team)
  if (!team) return false
  return team.owner === currentUser.username || team.admin?.includes(currentUser.username)
}

const isCurrentTeamMember = (task, username) => {
  if (!task.team || !username) return true
  const team = teamList.value.find(t => t.title === task.team)
  if (!team) return true
  return team.owner === username || team.admin?.includes(username) || team.member?.includes(username)
}

const formatAssignee = (task) => {
  const assignees = Array.isArray(task.assignee) ? task.assignee : (task.assignee ? [task.assignee] : [])
  if (assignees.length === 0) return '未分配'
  return assignees.map(username => {
    if (props.isTeamSpace && task.status === '已完成' && !isCurrentTeamMember(task, username)) {
      return `${username}（已离队）`
    }
    return username
  }).join(', ')
}

const hideAssigneeDetail = (task) => {
  const assignees = Array.isArray(task.assignee) ? task.assignee : (task.assignee ? [task.assignee] : [])
  if (assignees.length === 0) return true
  return props.isTeamSpace && task.status === '已完成' && !isCurrentTeamMember(task, assignees[0])
}

const getPrimaryAssignee = (task) => {
  const assignees = Array.isArray(task.assignee) ? task.assignee : (task.assignee ? [task.assignee] : [])
  return assignees[0] || ''
}

const loadAssigneeProfile = async (task) => {
  const username = getPrimaryAssignee(task)
  if (!username || userProfileMap[username]) return

  try {
    await getUserProfile(username)
  } catch (error) {
    console.error('获取负责人信息失败:', error)
  }
}

const getAssigneeProfile = (task) => {
  const username = getPrimaryAssignee(task)
  return username ? userProfileMap[username] : null
}

const DeleteConfirmContent = defineComponent({
  props: {
    title: {
      type: String,
      required: true
    }
  },
  emits: ['change'],
  setup(props, { emit }) {
    const checked = ref(false)
    const updateChecked = (val) => {
      checked.value = val
      emit('change', val)
    }

    return () => h('div', [
      h('p', `确定要删除任务"${props.title}"吗？`),
      h(ElCheckbox, {
        modelValue: checked.value,
        'onUpdate:modelValue': updateChecked,
        style: {
          position: 'absolute',
          bottom: '13px',
          left: '20px',
          zIndex: 1
        }
      }, () => '级联删除')
    ])
  }
})

// 删除任务
const deleteTask = (row) => {
  let cascade = false
  ElMessageBox.confirm(
      h(DeleteConfirmContent, {
        title: row.title,
        onChange: (val) => {
          cascade = val
        }
      }),
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(async () => {
    highlightTaskId.value = null
    // 传递 cascade 参数给后端
    await removeTask(row.id, cascade)
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
            label="负责人"
            min-width="25%"
            align="center"
        >
          <template v-slot:default="scope">
            <span v-if="hideAssigneeDetail(scope.row)">
              {{ formatAssignee(scope.row) }}
            </span>
            <el-popover
                v-else
                placement="bottom"
                :fallback-placements="['bottom', 'top']"
                :width="350"
                :height="250"
                :offset="0"
                trigger="hover"
                :append-to-body="true"
                popper-class="user-detail-popover"
                @show="loadAssigneeProfile(scope.row)"
            >
              <template #reference>
                <span class="assignee">
                  {{ formatAssignee(scope.row) }}
                </span>
              </template><div>
              <h2 class="popover-title">
                {{ formatAssignee(scope.row) }}
              </h2>
              <p class="popover-info" v-if="getAssigneeProfile(scope.row)?.lastName && getAssigneeProfile(scope.row)?.firstName">
                <span class="key">全名：</span>
                {{ getAssigneeProfile(scope.row).lastName }}{{ getAssigneeProfile(scope.row).firstName }}
              </p>
              <p class="popover-info" v-if="getAssigneeProfile(scope.row)?.phone">
                <span class="key">电话号码：</span>
                {{ getAssigneeProfile(scope.row).phone }}
              </p>
              <p class="popover-info" v-if="getAssigneeProfile(scope.row)?.email">
                <span class="key">电子邮箱：</span>
                {{ getAssigneeProfile(scope.row).email }}
              </p>
            </div>
            </el-popover>
          </template>
        </el-table-column>
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
              <el-popover
                  placement="bottom"
                  :offset="0"
                  trigger="hover"
                  popper-style="min-width: 0; width: auto;"
              >
                <template #reference>
                  <el-icon>
                    <View/>
                  </el-icon>
                </template>
                <div>
                  查看详情
                </div>
              </el-popover>
            </el-button>

            <!-- 个人任务、负责人、团队管理者/拥有者可见 -->
            <!-- 任务模块中，团队任务只有负责人能修改状态 -->
            <el-button
                link
                type="text"
                v-if="showUpdateTask(scope.row) && scope.row.status === '待办'"
                @click="startTask(scope.row)"
            >
              <el-popover
                  placement="bottom"
                  :offset="0"
                  trigger="hover"
                  popper-style="min-width: 0; width: auto;"
              >
                <template #reference>
                  <el-icon>
                    <CaretRight/>
                  </el-icon>
                </template>
                <div>
                  开始任务
                </div>
              </el-popover>
            </el-button>
            <el-button
                link
                type="text"
                v-else-if="showUpdateTask(scope.row) && scope.row.status === '进行中'"
                @click="checkTask(scope.row)"
            >
              <el-popover
                  placement="bottom"
                  :offset="0"
                  trigger="hover"
                  popper-style="min-width: 0; width: auto;"
              >
                <template #reference>
                  <el-icon>
                    <Check/>
                  </el-icon>
                </template>
                <div>
                  完成任务
                </div>
              </el-popover>
            </el-button>

            <!-- 编辑按钮：任务模块中团队任务不显示；团队空间中按权限显示 -->
            <el-button
                link
                type="text"
                v-if="(scope.row.team === null && scope.row.owner === currentUser.username) ||
                  (scope.row.team !== null && isTeamSpace && (scope.row.owner === currentUser.username || isTaskTeamAdmin(scope.row)))"
                @click="editTask(scope.row)"
            >
              <el-popover
                  placement="bottom"
                  :offset="0"
                  trigger="hover"
                  popper-style="min-width: 0; width: auto;"
              >
                <template #reference>
                  <el-icon>
                    <Edit/>
                  </el-icon>
                </template>
                <div>
                  编辑任务
                </div>
              </el-popover>
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
              <el-popover
                  placement="bottom"
                  :offset="0"
                  trigger="hover"
                  popper-style="min-width: 0; width: auto;"
              >
                <template #reference>
                  <el-icon>
                    <Delete/>
                  </el-icon>
                </template>
                <div>
                  删除任务
                </div>
              </el-popover>
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

.user-detail-popover {
  z-index: 100;
}

.user-detail-popover .popover-content {
  position: relative;
  z-index: 100;
}

.assignee:hover {
  color: #409eff;
  cursor: pointer;
}

.popover-title {
  font-weight: bold;
  text-align: center;
}

.popover-info {
  padding: 3px 10px;
}

.key {
  font-weight: bold;
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