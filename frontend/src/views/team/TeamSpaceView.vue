<script setup lang="js">
//TODO
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const handleBack = () => {

}

//TODO
const viewMembers = () => {

}
</script>

<template>
  <!--TODO: show-new-button=is-admin=用户不为member-->
  <TaskViewWrapper
      title="TODO（团队名）的团队空间"
      :show-new-button="true"
      :show-assignee="true"
      :is-admin="true"
  />

  <div class="footer">
    <el-button
        type="primary"
        class="back"
        @click="handleBack"
    >
      返回团队列表
    </el-button>

    <el-button
        type="primary"
        class="member"
        @click="viewMembers"
    >
      <!--TODO: 用户为owner-->
      <span v-if="true">编辑</span>
      成员信息
    </el-button>
  </div>
</template>

<style scoped>
.footer {
  width: 100%;
  height: 35px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: row;
}

.back {
  margin-left: 15%;
  margin-right: auto;
  width: 200px;
  height: 100%;
  font-size: 20px;
}

.member {
  margin-left: auto;
  margin-right: 15%;
  width: 200px;
  height: 100%;
  font-size: 20px;
}
</style>