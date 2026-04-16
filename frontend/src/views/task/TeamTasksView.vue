<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const isTeamTask = (task) => task.team
</script>

<template>
  <TaskViewWrapper
      title="团队任务"
      :filter-fn="isTeamTask"
  />
</template>

<style scoped>

</style>