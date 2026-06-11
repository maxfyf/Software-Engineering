<script setup lang="js">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentUser, initTaskList, initTeamList, teamList } from '@/store/user.js'
import { handleEnter } from '@/utils/routeManager.js'
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const route = useRoute()
const router = useRouter()

const teamId = computed(() => parseInt(route.query.teamId))
const team = computed(() => teamList.value.find(t => t.id === teamId.value))

const isOwner = computed(() => team.value?.owner === currentUser.username)
const isAdmin = computed(() => team.value?.admin?.includes(currentUser.username))

const canManage = computed(() => isOwner.value || isAdmin.value)

const filterByTeam = (task) => task.team === team.value?.title

const loadTeamSpaceData = async () => {
  await Promise.all([
    initTeamList(),
    initTaskList()
  ])
}

onMounted(loadTeamSpaceData)
watch(teamId, loadTeamSpaceData)

// 查看团队操作日志
const handleViewOperations = () => {
  handleEnter(route, router, {
    path: 'operations',
    params: []
  })
}
</script>

<template>
  <router-view v-if="route.path.includes('/detail') ||
                     route.path.includes('/edit') ||
                     route.path.includes('/personnel') ||
                     route.path.includes('/operations')" />
  <template v-else>
    <TaskViewWrapper
        :filter-fn="filterByTeam"
        :show-new-button="canManage"
        :show-assignee="true"
        :is-team-space="true"
        :is-admin="canManage"
    />

    <div class="footer">
      <el-button
          type="primary"
          class="back"
          @click="handleViewOperations"
      >
        查看操作日志
      </el-button>

      <el-button
          type="primary"
          class="member"
          @click="handleEnter(route, router, {
            path: 'personnel',
            params: []
          })"
      >
        <span v-if="isOwner">编辑</span>
        成员信息
      </el-button>
    </div>
  </template>
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