<script setup lang="js">
import { ref, computed, onMounted} from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import { ElMessage, ElMessageBox } from 'element-plus';
import { taskList, addTask, getTaskById, updateTask, teamList } from '@/store/user.js';
import { handleBack } from "@/utils/routeManager.js"

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

// 检查是否有修改
const hasChanges = () => {
  if (isNew.value) {
    // 新建模式：任何输入都算有修改
    return newTitle.value || newDescription.value || newDate.value
  }
  
  // 编辑模式：和原始任务比较
  if (!originalTask.value) return false

  const originalAssignee = Array.isArray(originalTask.value.assignee)
      ? (originalTask.value.assignee[0] || '')
      : (originalTask.value.assignee || '')
  
  return newTitle.value !== originalTask.value.title ||
         (isTeamTask.value && newAssignee.value !== originalAssignee) ||
         newDescription.value !== (originalTask.value.description || '') ||
         newStatus.value !== originalTask.value.status ||
         newPriority.value !== originalTask.value.priority ||
         newDate.value !== (originalTask.value.deadline || '')
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
}

// 保存所有更改并回退到来源页面
const saveChanges = async () => {
  // 表单验证
  if (!newTitle.value) {
    ElMessage.error('任务标题不能为空')
    return
  }
  
  const taskData = {
    title: newTitle.value,
    ...(isTeamTask.value && { 
      assignee: newAssignee.value,
      team: currentTeam.value?.title || null }),
    description: newDescription.value,
    status: newStatus.value,
    priority: newPriority.value,
    deadline: newDate.value
  }
  
  if (isNew.value) {
    // 新建任务
    let idx = taskList.value.findIndex(t => t.title === newTitle.value)
    if(idx !== -1) {
      ElMessage.error('该任务已存在')
      return
    }
    await addTask(taskData) 
    ElMessage.success('任务创建成功')
  } else {
    // 更新任务
    let idx = taskList.value.findIndex(t => t.title === newTitle.value
        && t.id !== taskId.value)
    if(idx !== -1) {
      ElMessage.error('任务标题重复')
      return
    }
    await updateTask(taskId.value, taskData)
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
              :rows="isTeamTask ? 8 : 10"
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
