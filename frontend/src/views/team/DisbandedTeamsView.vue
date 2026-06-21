<script setup lang="js">
import { computed, inject, nextTick, onMounted, ref, watch } from "vue";
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
const highlightedTeamId = ref(null)
const searchText = ref("")
const tableRef = ref(null)

const disbandedTeams = computed(() => teamView?.disbandedTeams?.value || [])
const total = computed(() => disbandedTeams.value.length)
const pageData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return disbandedTeams.value.slice(start, end)
})

const searchData = computed(() => disbandedTeams.value.map(team => ({
  data: team.title,
  aux: '',
  id: team.id,
  searchText: team.title
})))

watch(searchText, (value) => {
  if (!value) {
    highlightedTeamId.value = null
    currentPage.value = 1
  }
})

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const scrollToHighlightedRow = async () => {
  await nextTick()
  const row = tableRef.value?.$el?.querySelector('.highlight-row')
  row?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

const handleSelectDisbandedTeam = async (item) => {
  if (!item) return
  const index = disbandedTeams.value.findIndex(team => Number(team.id) === Number(item.id))
  if (index === -1) return

  currentPage.value = Math.floor(index / pageSize.value) + 1
  highlightedTeamId.value = item.id
  await scrollToHighlightedRow()
}

const rowClassName = ({ row }) => {
  return Number(row.id) === Number(highlightedTeamId.value) ? 'highlight-row' : ''
}

const isRestoreNameConflict = (error) => {
  const detail = error?.response?.data?.detail || error?.detail || error?.msg || ''
  return String(detail).includes('同名团队') || String(detail).includes('重命名后再恢复')
}

const openRenameThenRestore = (team) => {
  ElMessage.warning('当前已有同名团队，请先重命名该团队后再恢复')
  teamView.handleRename(team, {
    afterRename: async (renamedTeam) => {
      await teamView.handleRestoreTeam(renamedTeam)
      highlightedTeamId.value = null
      currentPage.value = 1
    }
  })
}

const restoreTeam = async (team) => {
  if (!teamView) {
    ElMessage.error('回收站状态未初始化')
    return
  }

  if (teamView.hasActiveTeamTitle(team.title)) {
    openRenameThenRestore(team)
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
    highlightedTeamId.value = null
    currentPage.value = 1
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    if (isRestoreNameConflict(error)) {
      openRenameThenRestore(team)
      return
    }
    console.error('恢复团队失败:', error)
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
              ref="tableRef"
              :data="pageData"
              :row-class-name="rowClassName"
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

.disbanded-teams-table :deep(.highlight-row) {
  background-color: #ecf5ff !important;
}

.disbanded-teams-table :deep(.highlight-row td) {
  background-color: #ecf5ff !important;
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