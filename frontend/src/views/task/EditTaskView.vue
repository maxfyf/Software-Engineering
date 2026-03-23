<script setup lang="js">
import { ref } from "vue";
import { Back } from "@element-plus/icons-vue";
import HeaderWrapper from "@/components/HeaderWrapper.vue";

const isNew = ref(true);
const newTitle = ref(isNew ? '' : 'TODO: 原标题')
const newDescription = ref(isNew ? '' : 'TODO: 原描述')
const newStatus = ref(isNew ? '待办' : 'TODO: 原状态')
const newPriority = ref(isNew ? '中' : 'TODO: 原优先级')

const pastDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}
const newDate=ref(isNew ? '' : 'TODO: 原截止时间')

// TODO: 回退到AllTaskView，若为新建任务，取消该任务；若为编辑任务，取消编辑记录
const handleBack = () => {

}

// TODO: 保存所有更改并回退到'/task/all'页面
const saveChanges = () => {

}
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
            编辑任务“TODO:任务标题（需要随任务标题的改动实时重新渲染）”
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
              :rows="6"
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
  flex: 1;
  margin-left: 35px;
  margin-right: 35px;
  border-radius: 10px;
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.box-card:hover {
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
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