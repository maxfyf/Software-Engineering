<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const isPersonalTask = (task) => !task.teamId
</script>

<template>
  <TaskViewWrapper
      title="个人任务"
      :filter-fn="isPersonalTask"
      :show-new-button="true"
  />
</template>