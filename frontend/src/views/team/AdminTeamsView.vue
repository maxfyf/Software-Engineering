<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";
import { useRoute } from 'vue-router';

const route = useRoute();
const isAdmin = (team) => team.admin.includes(currentUser.username)
</script>

<template>
  <TeamViewWrapper
      v-if="!route.path.includes('/space')"
      title="我管理的团队"
      :filter-fn="isAdmin"
      :show-new-button="false"
  />
  <router-view v-else />
</template>

<style scoped>

</style>