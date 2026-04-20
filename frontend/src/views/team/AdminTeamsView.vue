<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";

const isAdmin = (team) => team.admin.includes(currentUser.username)
</script>

<template>
  <TeamViewWrapper
      title="我管理的团队"
      :filter-fn="isAdmin"
      :show-new-button="false"
  />
</template>

<style scoped>

</style>