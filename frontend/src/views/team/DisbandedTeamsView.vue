<script setup lang="js">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { handleBack } from "@/utils/routeManager.js";

const route = useRoute()
const router = useRouter()

//TODO
const disbandedTeams = []
const total = computed(() => disbandedTeams.length)
const currentPage = ref(1)
const pageSize = ref(10)
const pageData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return disbandedTeams.slice(start, end)
})

const handleCurrentChange = (page) => {
  // TODO
}

const searchData = []    // TODO: 搜索框数组
const handleSelectDisbandedTeam = () => {
  // TODO: 搜索框搜索函数
}

const restoreTeam = (team) => {
  /* TODO: 首先检查是否有别的团队与该解散的团队重名，如有，则需调用TeamViewWrapper中创建的useTeamView对象中的
           handleRename(currentName)函数，要求重命名该团队后再恢复。完成恢复后需要去除disbandedAt属性（解散日期），
           并对所有团队中的其他成员，如果其未读解散该团队时发送的通知，则删除该通知；如果其已读解散该团队是发送的通知，则
           发送一条新的通知告知该团队已恢复
   */
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>

        <div class="search-wrapper">
          <Search :dataset="searchData" :onSelect="handleSelectDisbandedTeam" />
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
                label="创建日期"
                min-width="20%"
                align="center"
            />
            <el-table-column
                prop="disbandedAt"
                label="解散日期"
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