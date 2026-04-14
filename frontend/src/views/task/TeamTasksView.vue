<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const isTeamTask = (task) => task.teamId
</script>

<template>
  <TaskViewWrapper
      title="团队任务"
      :filter-fn="isTeamTask"
  />
</template>