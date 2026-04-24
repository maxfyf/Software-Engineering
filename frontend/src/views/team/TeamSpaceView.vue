<script setup lang="js">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentUser, teamList } from '@/store/user.js'
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";

const route = useRoute()
const router = useRouter()

const teamId = computed(() => parseInt(route.query.teamId))
const team = computed(() => teamList.value.find(t => t.id === teamId.value))

const teamTitle = computed(() => team.value ? `${team.value.title}的团队空间` : '团队空间')

const isOwner = computed(() => team.value?.owner === currentUser.username)
const isAdmin = computed(() => team.value?.admin?.includes(currentUser.username))

const canManage = computed(() => isOwner.value || isAdmin.value)

const filterByTeam = (task) => task.team === team.value?.title

const extraQuery = computed(() => ({ teamId: teamId.value }))

const parentPath = computed(() => {
  const match = route.path.match(/\/team\/(all|owner|admin|member)/)
  return match ? match[1] : 'all'
})

const handleBack = () => {
  router.push(`/team/${parentPath.value}`)
}

const viewMembers = () => {
  router.push({
      path: `/team/${parentPath.value}/space/personnel`,
      query: { teamId: teamId.value }
  })
}
</script>

<template>
  <router-view v-if="route.path.includes('/edit') || route.path.includes('/personnel')" />
  <template v-else>
    <TaskViewWrapper
        :title="teamTitle"
        :filter-fn="filterByTeam"
        :show-new-button="canManage"
        :show-assignee="true"
        :is-admin="canManage"
        :extra-query="extraQuery"
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