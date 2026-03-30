<script setup lang="js">
import { ref, computed, onMounted} from "vue";
import { Back } from "@element-plus/icons-vue";
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { taskList, highlightTaskId, addTask, getTaskById } from '@/store/user.js';

const route = useRoute();
const router = useRouter();

const taskId = ref(null)
const isNew = ref(true);
const originalTask = ref(null)  
const isLeaving = ref(false)

const newTitle = ref('')
const newDescription = ref('')
const newStatus = ref('待办')
const newPriority = ref('中')
const newDate = ref('')

const pastDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

const taskTitle = computed(() => isNew.value ? '' : newTitle.value)

// 检查是否有修改
const hasChanges = () => {
  if (isNew.value) {
    // 新建模式：任何输入都算有修改
    return newTitle.value || newDescription.value || newDate.value
  }
  
  // 编辑模式：和原始任务比较
  if (!originalTask.value) return false
  
  return newTitle.value !== originalTask.value.title ||
         newDescription.value !== (originalTask.value.description || '') ||
         newStatus.value !== originalTask.value.status ||
         newPriority.value !== originalTask.value.priority ||
         newDate.value !== (originalTask.value.deadline || '')
}

// 页面加载时，根据路由参数初始化数据
onMounted(() => {
  const isNewParam = route.query.isNew
  const taskIdParam = route.query.taskId
  
  if (isNewParam === 'false' && taskIdParam) {
    // 编辑模式
    isNew.value = false
    taskId.value = parseInt(taskIdParam)
    // TODO: 从后端加载任务详情
    // 模拟加载已有任务数据
    loadTaskData(taskId.value)
  } else {
    // 新建模式
    isNew.value = true
    // 重置表单为空
    resetForm()
  }
})

// 加载任务数据（编辑模式）
const loadTaskData = (id) => {
  console.log('加载任务数据, ID:', id)
  const task = getTaskById(id)
  if (task) {
    originalTask.value = task
    
    // 设置表单值
    newTitle.value = task.title
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
  newDescription.value = ''
  newStatus.value = '待办'
  newPriority.value = '中'
  newDate.value = ''
}

// 回退到AllTaskView，若为新建任务，取消该任务；若为编辑任务，取消编辑记录
const handleBack = () => {
  const info = isNew.value ? '您新建的任务尚未保存，确定要离开吗？' : '您有未保存的更改，确定要离开吗？'
  
  if (hasChanges()) {
    ElMessageBox.confirm(
      info,
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
    ).then(() => {
      isLeaving.value = true
      router.push('/task/all')
    }).catch(() => {
      // 取消，留在当前页面
    })
  } else {
    isLeaving.value = true
    router.push('/task/all')
  }
}

// 保存所有更改并回退到'/task/all'页面
const saveChanges = () => {
  // 表单验证
  if (!newTitle.value) {
    ElMessage.warning('请输入任务标题')
    return
  }
  
  const taskData = {
    title: newTitle.value,
    description: newDescription.value,
    status: newStatus.value,
    priority: newPriority.value,
    deadline: newDate.value
  }
  
  if (isNew.value) {
    // 新建任务
    // TODO: 调用后端创建任务 API
    addTask(taskData)  // 调用 addTask
    ElMessage.success('任务创建成功')
  } else {
    // 更新任务
    // TODO: 调用后端更新任务 API
    const index = taskList.value.findIndex(t => t.id === taskId.value)
    if (index !== -1) {
      taskList.value[index] = {
        ...taskList.value[index],
        ...taskData,
        updatedAt: new Date().toISOString()
      }
    }
    ElMessage.success('任务更新成功')
  }
  
  // 返回任务列表
  resetForm()
  isLeaving.value = true  // 标记正在离开，跳过守卫
  router.push('/task/all')
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
        <el-button
            link
            type="text"
            size="large"
            @click="handleBack"
        >
          <el-icon :size="25">
            <Back/>
          </el-icon>
        </el-button>
        <span class="route">
          <span>全部任务</span>
          <span>&nbsp;>&nbsp;</span>
          <span v-if="isNew" class="present-directory">
            新建任务
          </span>
          <span v-else class="present-directory">
            编辑任务“{{ taskTitle }}”
          </span>
        </span>
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
              :rows="1"
          />
        </div>

        <div class="item">
          <span class="key">描述：</span>
          <el-input
              class="description"
              v-model="newDescription"
              type="textarea"
              :rows="10"
          />
        </div>

        <div class="item">
          <span class="key">状态：</span>
          <el-select class="status" v-model="newStatus">
            <el-option label="待办" value="待办"></el-option>
            <el-option label="进行中" value="进行中"></el-option>
            <el-option label="已完成" value="已完成"></el-option>
          </el-select>
        </div>

        <div class="item">
          <span class="key">优先级：</span>
          <el-select class="priority" v-model="newPriority">
            <el-option label="低" value="低"></el-option>
            <el-option label="中" value="中"></el-option>
            <el-option label="高" value="高"></el-option>
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
              clearable
          />
        </div>

        <template #footer>
          <div class="footer">
            <el-button
                type="danger"
                class="cancel"
                @click="handleBack"
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
.inner-header {
  left: 0;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  flex-direction: row;
  gap: 15px;
  align-items: center;
}

.route {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: #333333;
}

.present-directory {
  font-weight: bold;
}

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
  margin-left: 200px;
  margin-right: auto;
  width: 100px;
  height: 100%;
  font-size: 20px;
}

.save {
  margin-left: auto;
  margin-right: 200px;
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>
