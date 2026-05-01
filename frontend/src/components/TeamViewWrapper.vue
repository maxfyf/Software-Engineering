<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import TeamList from "@/components/TeamList.vue";
import { useTeamView } from "@/utils/useTeamView.js";
import { Plus } from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";

const props = defineProps({
  filterFn: {
    type: Function,
    default: null
  },
  showNewButton: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const router = useRouter()

const {
  teams,
  dataset,
  createDialogVisible,
  newTeamTitle,
  handleSelect,
  handleNew,
  handleCreateTeam,
  handleCancelCreate,
  handleEnterTeamSpace
} = useTeamView(props.filterFn)
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router"/>
        </div>
        <div class="search-wrapper">
          <Search :data="dataset" :onSelect="handleSelect" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div v-if="showNewButton" class="header">
        <el-button type="primary" class="new-button" @click="handleNew">
          <el-icon><Plus/></el-icon>
          &nbsp;新建团队
        </el-button>
      </div>

      <TeamList
          :teams="teams"
          @enter-team-space="handleEnterTeamSpace"
      />
    </div>

    <!-- 新建团队弹窗 -->
    <el-dialog
        v-model="createDialogVisible"
        width="500px"
        center
        :beforeClose="handleCancelCreate"
    >
      <template #header>
        <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;新建团队</span>
      </template>
      <el-input
          v-model="newTeamTitle"
          type="text"
          placeholder="团队名"
      />
      <template #footer>
        <div class="dialog-footer">
          <el-button
              type="default"
              class="cancel"
              @click="handleCancelCreate"
          >
            取消
          </el-button>
          <el-button
              type="primary"
              class="check"
              @click="handleCreateTeam"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
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
  margin-top: 20px;
  margin-left: 20px;
  margin-right: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.header {
  width: 100%;
  display: flex;
}

.new-button {
  width: 100px;
  margin-left: auto;
  margin-right: 15px;
}

.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-footer {
  width: 100%;
  height: 30px;
  display: flex;
  flex-direction: row;
}

.cancel {
  margin-left: 20%;
  margin-right: auto;
  width: 70px;
  height: 100%;
  font-size: 18px;
}

.check {
  margin-left: auto;
  margin-right: 20%;
  width: 70px;
  height: 100%;
  font-size: 18px;
}
</style>