<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';

const route = useRoute();
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/edit')"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>