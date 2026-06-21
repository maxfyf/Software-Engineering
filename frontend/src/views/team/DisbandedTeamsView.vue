<script setup lang="js">
import { computed, inject, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { handleBack } from "@/utils/routeManager.js";

const route = useRoute()
const router = useRouter()
const teamView = inject('teamView', null)

const currentPage = ref(1)
const pageSize = ref(10)
const selectedTeam = ref(null)
const searchText = ref("")

const disbandedTeams = computed(() => teamView?.disbandedTeams?.value || [])
const filteredTeams = computed(() => {
  if (!selectedTeam.value) return disbandedTeams.value
  return disbandedTeams.value.filter(team => Number(team.id) === Number(selectedTeam.value.id))
})
const total = computed(() => filteredTeams.value.length)
const pageData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredTeams.value.slice(start, end)
})

const searchData = computed(() => disbandedTeams.value.map(team => ({
  data: team.title,
  aux: team.disbandedAt ? `解散时间：${team.disbandedAt}` : '',
  id: team.id
})))


watch(searchText, (value) => {
  if (!value) {
    selectedTeam.value = null
    currentPage.value = 1
  }
})
const handleCurrentChange = (page) => {
  currentPage.value = page
}

const handleSelectDisbandedTeam = (item) => {
  selectedTeam.value = item || null
  currentPage.value = 1
}

const restoreTeam = async (team) => {
  if (!teamView) {
    ElMessage.error('回收站状态未初始化')
    return
  }

  if (teamView.hasActiveTeamTitle(team.title)) {
    ElMessage.warning('当前已有同名团队，请先重命名该团队后再恢复')
    teamView.handleRename(team)
    return
  }

  try {
    await ElMessageBox.confirm(
        `确定要恢复团队"${team.title}"吗？`,
        '',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: undefined
        }
    )
    await teamView.handleRestoreTeam(team)
    selectedTeam.value = null
    currentPage.value = 1
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('恢复团队失败:', error)
    }
  }
}

onMounted(async () => {
  await teamView?.loadDisbandedTeams(true)
})
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>

        <div class="search-wrapper">
          <Search v-model="searchText" :dataset="searchData" :onSelect="handleSelectDisbandedTeam" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-row>
        <el-col>
          <el-table
              :data="pageData"
              empty-text="暂无解散的团队"
              stripe
              class="disbanded-teams-table"
          >
            <el-table-column
                prop="title"
                label="团队名"
                min-width="40%"
                align="left"
            />
            <el-table-column
                prop="createdAt"
                label="创建时间"
                min-width="20%"
                align="center"
            />
            <el-table-column
                prop="disbandedAt"
                label="解散时间"
                min-width="20%"
                align="center"
            />
            <el-table-column
                fixed="right"
                label="操作"
                min-width="20%"
                align="center"
            >
              <template v-slot:default="scope">
                <el-button
                    link
                    type="text"
                    @click="restoreTeam(scope.row)"
                >
                  <span>恢复</span>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>

      <el-pagination
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="total"
          class="pagination"
      />

      <div class="footer">
        <el-button type="primary" class="back-button" @click="handleBack(route, router, 1)">
          返回
        </el-button>
      </div>
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.route-wrapper {
  display: flex;
  left: 20px;
  align-items: center;
}

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}

.main-content-wrapper {
  padding: 20px 30px;
  height: calc(100% - 40px);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.disbanded-teams-table {
  width: 100%;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-pagination .el-pager li) {
  background-color: transparent !important;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background-color: transparent !important;
  color: black !important;
}

.footer {
  width: 100%;
  height: 35px;
  margin-top: auto;
  margin-bottom: 0;
  display: flex;
  justify-content: center;
}

.back-button {
  width: 80px;
  height: 100%;
  font-size: 20px;
}
</style>