<script setup lang="js">
import { ref, computed, onMounted} from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import SelectableList from "@/components/SelectableList.vue";
import { ElMessage, ElMessageBox } from 'element-plus';
import { taskList, addTask, getTaskById, updateTask, teamList, getPredecessors, updatePredecessors }
  from '@/store/user.js';
import { handleBack } from "@/utils/routeManager.js"
import { Edit } from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();

const taskId = ref(null)
const isNew = ref(true);
const originalTask = ref(null)  
const isLeaving = ref(false)

const newTitle = ref('')
const newAssignee = ref('')
const newDescription = ref('')
const newStatus = ref('待办')
const newPredecessor = ref([])
const newPriority = ref('中')
const newDate = ref('')

const pastDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

// 判断当前任务是否为团队任务
const isTeamTask = computed(() => {
  return route.fullPath.indexOf('/space') !== -1
})

// 当前任务所属团队
const currentTeam = computed(() => {
  const teamId = isNew.value
    ? parseInt(route.query.teamId)
    : teamList.value.find(t => t.title === originalTask.value?.team)?.id
  return teamList.value.find(t => t.id === teamId) || null
})

// 团队成员列表（响应式）
const teamMembers = computed(() => {
  if (!currentTeam.value) return []
  return [currentTeam.value.owner, ...currentTeam.value.admin, ...currentTeam.value.member]
})

// 当前作用域内的任务列表（用于唯一性验证）
// 个人任务只检查个人任务，团队任务只检查同一团队内的任务
const scopeTaskList = computed(() => {
  if (isTeamTask.value) {
    // 团队任务：只检查同一团队内的任务
    return taskList.value.filter(t => t.team === currentTeam.value?.title)
  } else {
    // 个人任务：只检查个人任务（team 为 null）
    return taskList.value.filter(t => !t.team)
  }
})

// 前置任务列表的空白文本
const emptyText = computed(() => {
  if(currentTeam.value) {
    return currentTeam.value.title + "中暂无其它团队任务"
  }
  else {
    return "暂无其它个人任务"
  }
})

const candidateTaskList = computed(() => {
  return scopeTaskList.value.filter(t => t.id !== taskId.value).map(task => task.title)
})

const findTaskByDependencyItem = (item) => {
  if (typeof item === 'number') {
    return taskList.value.find(t => t.id === item)
  }
  const numericId = Number(item)
  if (!Number.isNaN(numericId)) {
    const taskById = taskList.value.find(t => t.id === numericId)
    if (taskById) return taskById
  }
  return scopeTaskList.value.find(t => t.title === item)
}

// 寻找未完成的前置任务
const findUnfinishedPredecessor = (predecessors) => {
  for (const predItem of predecessors) {
    const predTask = findTaskByDependencyItem(predItem)
    if(predTask.status !== '已完成') return predTask
  }
  return null
}

const findFinishedSuccessor = (targetId) => {
  const successors = taskList.value.filter(t =>
      (t.predecessor || []).some(predItem => findTaskByDependencyItem(predItem)?.id === targetId)
  )
  for(let task of successors) {
    if(task.status === '已完成') return task
  }
  return null
}

const showPredecessor = ref(false)
const tempPredecessor = ref([])
const showPredecessorDialog = () => {
  // 打开窗口时，将当前已有的前置任务复制到 tempPredecessor
  tempPredecessor.value = newPredecessor.value.slice()
  showPredecessor.value = true
}
const closePredecessorDialog = () => {
  showPredecessor.value = false
}
const updateNewPredecessor = () => {
  // 检查非法状态：已完成的任务不能添加未完成的前置任务
  if (newStatus.value === '已完成') {
    const blocker = findUnfinishedPredecessor(tempPredecessor.value)
    if (blocker) {
      ElMessage.error(`任务「${newTitle.value}」已完成，无法添加未完成的前置任务「${blocker.title}」`)
      return
    }
  }

  // 检查环路
  const cycleTask = findCycleCausingPredecessor(tempPredecessor.value)
  if (cycleTask) {
    ElMessage.error(`新增前置任务「${cycleTask.title}」将导致依赖关系出现环路，请重新选择`)
    return
  }

  // 更新 newPredecessor
  newPredecessor.value = tempPredecessor.value.slice()
  closePredecessorDialog()
}

// 检查新增前置任务是否会形成环路
const findCycleCausingPredecessor = (selectedPredecessors) => {
  if (isNew.value || !taskId.value) return null

  // 获取当前任务ID
  const currentId = taskId.value

  // 对于每个选中的前置任务，追溯其前置任务链
  for (const predTitle of selectedPredecessors) {
    const predTask = scopeTaskList.value.find(t => t.title === predTitle)
    if (!predTask) continue

    // 直接自引用检查
    if (predTask.id === currentId) return predTask

    // 递归追溯前置任务链
    const visited = new Set()
    if (tracePredecessorChain(predTask.id, currentId, visited)) {
      return predTask
    }
  }
  return null
}

// 递归追溯任务的前置任务链，检查是否包含目标任务
const tracePredecessorChain = (taskId, targetId, visited) => {
  if (visited.has(taskId)) return false
  visited.add(taskId)

  const task = taskList.value.find(t => t.id === taskId)
  if (!task || !task.predecessor) return false

  for (const predItem of task.predecessor) {
    // predecessor 可能是标题或ID
    let predTask
    if (typeof predItem === 'number') {
      predTask = taskList.value.find(t => t.id === predItem)
    } else {
      predTask = taskList.value.find(t => t.title === predItem || t.id === predItem)
    }
    if (!predTask) continue

    if (predTask.id === targetId) return true
    if (tracePredecessorChain(predTask.id, targetId, visited)) return true
  }
  return false
}

// 检查是否有修改
const hasChanges = () => {
  if (isNew.value) {
    // 新建模式：任何输入都算有修改
    return newTitle.value || newDescription.value || newDate.value || newPredecessor.value.length > 0
  }

  // 编辑模式：和原始任务比较
  if (!originalTask.value) return false

  const originalAssignee = Array.isArray(originalTask.value.assignee)
      ? (originalTask.value.assignee[0] || '')
      : (originalTask.value.assignee || '')

  // 比较前置任务列表
  const originalPredecessorStr = (originalTask.value.predecessor || []).map(String).sort().join(',')
  const newPredecessorIds = newPredecessor.value.map(title => {
    const task = scopeTaskList.value.find(t => t.title === title)
    return task?.id
  }).filter(id => id !== undefined)
  const newPredecessorStr = newPredecessorIds.map(String).sort().join(',')

  return newTitle.value !== originalTask.value.title ||
         (isTeamTask.value && newAssignee.value !== originalAssignee) ||
         newDescription.value !== (originalTask.value.description || '') ||
         newStatus.value !== originalTask.value.status ||
         newPriority.value !== originalTask.value.priority ||
         newDate.value !== (originalTask.value.deadline || '') ||
         originalPredecessorStr !== newPredecessorStr
}

// 页面加载时，根据路由参数初始化数据
onMounted(async () => {
  const isNewParam = route.query.isNew
  const taskIdParam = route.query.taskId
  
  if (isNewParam === 'false' && taskIdParam) {
    // 编辑模式
    isNew.value = false
    taskId.value = parseInt(taskIdParam)
    // 从后端加载任务详情
    await loadTaskData(taskId.value)
  } else {
    // 新建模式
    isNew.value = true
    // 重置表单为空
    resetForm()
  }
})

// 加载任务数据（编辑模式）
const loadTaskData = async (id) => {
  const task = await getTaskById(id)
  if (task) {
    originalTask.value = task

    // 设置表单值
    newTitle.value = task.title
    if (isTeamTask.value) {
      const a = task.assignee
      newAssignee.value = Array.isArray(a) ? (a[0] || '') : (a || '')
    }
    newDescription.value = task.description || ''
    newStatus.value = task.status
    newPriority.value = task.priority
    newDate.value = task.deadline || ''

    // 编辑页必须从依赖接口读取最新关系，避免 task.predecessor 为空数组时跳过真实数据。
    try {
      const predecessors = await getPredecessors(id)
      const predTitles = predecessors.map(pred => pred.title)
      const predIds = predecessors.map(pred => pred.id)
      newPredecessor.value = predTitles
      originalTask.value = {
        ...task,
        predecessor: predIds
      }
    } catch (error) {
      console.error('获取前置任务失败:', error)
      newPredecessor.value = []
    }
  }
}

// 重置表单
const resetForm = () => {
  originalTask.value = null
  newTitle.value = ''
  if (isTeamTask.value) {
    newAssignee.value = currentTeam.value?.owner || ''
  }
  newDescription.value = ''
  newStatus.value = '待办'
  newPriority.value = '中'
  newDate.value = ''
  newPredecessor.value = []
}

// 保存所有更改并回退到来源页面
const saveChanges = async () => {
  // 表单验证
  if (!newTitle.value) {
    ElMessage.error('任务标题不能为空')
    return
  }

  // 检查已完成任务是否存在未完成的前置任务
  if (newStatus.value === '已完成') {
    const blocker = findUnfinishedPredecessor(newPredecessor.value)
    if (blocker) {
      if (!isNew.value && originalTask.value?.status === '已完成') {
        ElMessage.error(`任务「${newTitle.value}」已完成，无法添加未完成的前置任务「${blocker.title}」`)
      } else {
        ElMessage.error(`前置任务「${blocker.title}」未完成，无法完成当前任务`)
      }
      return
    }
  }

  if (!isNew.value && originalTask.value?.status === '已完成' && newStatus.value !== '已完成') {
    const blocker = findFinishedSuccessor(taskId.value)
    if (blocker) {
      ElMessage.error(`后继任务「${blocker.title}」已完成，无法将当前任务改为未完成状态`)
      return
    }
  }

  const taskData = {
    title: newTitle.value,
    ...(isTeamTask.value && {
      assignee: newAssignee.value,
      team: currentTeam.value?.title || null }),
    description: newDescription.value,
    status: newStatus.value,
    priority: newPriority.value,
    deadline: newDate.value || null 
  }

  // 将前置任务标题转换为ID数组
  const predecessorIds = newPredecessor.value.map(title => {
    const task = scopeTaskList.value.find(t => t.title === title)
    return task?.id
  }).filter(id => id !== undefined)

  if (isNew.value) {
    // 新建任务
    const idx = scopeTaskList.value.findIndex(t => t.title === newTitle.value)
    if (idx !== -1) {
      ElMessage.error(isTeamTask.value ? '该团队中已存在同名任务' : '个人任务中已存在同名任务')
      return
    }
    // 创建任务时包含前置任务信息
    const newTask = await addTask({
      ...taskData,
      predecessor: predecessorIds
    })
    // 如果有前置任务，调用后端API设置依赖关系
    if (predecessorIds.length > 0 && newTask.id) {
      await updatePredecessors(newTask.id, predecessorIds)
    }
    newTask.predecessor = newPredecessor.value.slice()
    ElMessage.success('任务创建成功')
  } else {
    // 更新任务
    const idx = scopeTaskList.value.findIndex(t => t.title === newTitle.value && t.id !== taskId.value)
    if (idx !== -1) {
      ElMessage.error(isTeamTask.value ? '该团队中已存在同名任务' : '个人任务中已存在同名任务')
      return
    }
    await updateTask(taskId.value, taskData)
    // 更新前置任务依赖关系
    await updatePredecessors(taskId.value, predecessorIds)
    ElMessage.success('任务更新成功')
  }

  // 返回来源页面
  resetForm()
  isLeaving.value = true  // 标记正在离开，跳过守卫
  handleBack(route, router, 1)
}

// 路由守卫：离开页面前检查
onBeforeRouteLeave((to, from, next) => {
  if (isLeaving.value) {
    next()
    return
  }
  
  if (hasChanges()) {
    ElMessageBox.confirm(
      isNew.value ? '您新建的任务尚未保存，确定要离开吗？' : '您有未保存的更改，确定要离开吗？',
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
    ).then(() => {
      next()
    }).catch(() => {
      next(false)
    })
  } else {
    next()
  }
})
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <Route :route="route" :router="router"/>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <div class="item">
          <span class="key">标题：</span>
          <el-input
              class="title"
              v-model="newTitle"
              type="textarea"
              maxlength="20"
              show-word-limit
              :rows="1"
          />
        </div>

        <!--团队任务显示负责人选择-->
        <div v-if="isTeamTask" class="item">
          <span class="key">负责人：</span>
          <el-select class="assignee" v-model="newAssignee">
            <el-option
                v-for="item in teamMembers"
                :key="item"
                :label="item"
                :value="item"
            />
          </el-select>
        </div>

        <div class="item">
          <span class="key">描述：</span>
          <el-input
              class="description"
              v-model="newDescription"
              type="textarea"
              :rows="isTeamTask ? 6 : 8"
          />
        </div>

        <div class="item">
          <span class="key">状态：</span>
          <el-select class="status" v-model="newStatus">
            <el-option label="待办" value="待办"/>
            <el-option label="进行中" value="进行中"/>
            <el-option label="已完成" value="已完成"/>
          </el-select>
        </div>

        <div class="item">
          <span class="key">前置任务：{{newPredecessor.length}}个</span>
          <el-button
              link
              type="text"
              class="edit-button"
              @click="showPredecessorDialog"
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
                编辑前置任务
              </div>
            </el-popover>
          </el-button>
        </div>

        <div class="item">
          <span class="key">优先级：</span>
          <el-select class="priority" v-model="newPriority">
            <el-option label="低" value="低"/>
            <el-option label="中" value="中"/>
            <el-option label="高" value="高"/>
          </el-select>
        </div>

        <div class="item">
          <span class="key">截止时间：</span>
          <el-date-picker
              v-model="newDate"
              type="date"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="pastDate"
              :editable="false"
              clearable
          />
        </div>

        <template #footer>
          <div class="footer">
            <el-button
                type="danger"
                class="cancel"
                @click="handleBack(route, router, 1)"
            >
              取消
            </el-button>

            <el-button
                v-if="isNew"
                type="primary"
                class="save"
                @click="saveChanges"
            >
              确认
            </el-button>
            <el-button
                v-else
                type="primary"
                class="save"
                @click="saveChanges"
            >
              保存
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>

  <el-dialog
      v-model="showPredecessor"
      width="600px"
      center
      :beforeClose="closePredecessorDialog"
  >
    <template #header>
      <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;编辑前置任务</span>
    </template>
    <div class="dialog-body">
      <SelectableList
          v-model="tempPredecessor"
          :candidates="candidateTaskList"
          :emptyText="emptyText"
      />
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button
            type="default"
            class="cancel-button"
            @click="closePredecessorDialog"
        >
          取消
        </el-button>

        <el-button
            type="primary"
            class="check-button"
            @click="updateNewPredecessor"
        >
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.main-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.box-card {
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
}

.item {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  margin-top: 20px;
}

.key {
  flex-shrink: 0;
  font-size: 19px;
  text-align: center;
}

.title {
  flex-grow: 1;
  font-size: 15px;
}

.title :deep(.el-textarea__inner) {
  resize: none;
}

:deep(.title .el-input__count) {
  font-size: 16px;
  margin-bottom: 5px;
}

.assignee {
  width: 350px;
  font-size: 15px;
}

.description {
  flex-grow: 1;
  font-size: 15px;
  overflow-y: auto;
}

.description :deep(.el-textarea__inner) {
  resize: none;
}

.status {
  width: 100px;
  font-size: 15px;
}

.edit-button {
  margin-left: 15px;
  font-size: 24px;
}

.priority {
  width: 70px;
  font-size: 15px;
}

:deep(.el-card__footer) {
  border-top: none;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  flex-direction: row;
}

.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-body {
  max-height: 400px;
  display: flex;
  flex-direction: column;
  margin: 0 15px 0 15px;
}

.dialog-footer {
  width: 100%;
  height: 30px;
  display: flex;
  flex-direction: row;
}

.cancel-button {
  margin-left: 20%;
  margin-right: auto;
  width: 70px;
  height: 100%;
  font-size: 18px;
}

.check-button {
  margin-left: auto;
  margin-right: 20%;
  width: 70px;
  height: 100%;
  font-size: 18px;
}

.cancel {
  margin-left: 20%;
  margin-right: auto;
  width: 100px;
  height: 100%;
  font-size: 20px;
}

.save {
  margin-left: auto;
  margin-right: 20%;
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>