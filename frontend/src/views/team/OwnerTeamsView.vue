<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";
import { useRoute } from 'vue-router';

const route = useRoute();
const isOwner = (team) => team.owner === currentUser.username
</script>

<template>
  <TeamViewWrapper
      v-if="!route.path.includes('/space')"
      title="我拥有的团队"
      :filter-fn="isOwner"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>