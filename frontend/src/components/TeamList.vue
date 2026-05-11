<script setup lang="js">
import { currentUser, highlightTeamId, removeTeam} from "@/store/user.js";
import { ElMessage, ElMessageBox } from "element-plus";
import TwoColumnsWrapper from "@/components/TwoColumnsWrapper.vue";
import { MoreFilled, Right } from "@element-plus/icons-vue";
import { computed, ref, watch } from "vue";

const props = defineProps({
  teams: {
    type: Array,
    required: true,
    default: () => []
  }
})

const emit = defineEmits(['enterTeamSpace'])

// 判定用户角色
const role = (item) => {
  const username = currentUser.username;
  if (username === item.owner)
    return '拥有者'
  else if (item.admin.includes(username))
    return '管理者'
  else if (item.member.includes(username))
    return '参与者'
  else {
    ElMessage.error('非法访问团队')
    return null
  }
}

const handleCommand = (command) => {
  switch (command.action) {
    case 'quit':
      quitTeam(command.item)
      break;
    case 'disband':
      deleteTeam(command.item)
      break;
    default:
      break;
  }
}

const currentTeam = ref(undefined)
const visible = computed(() => {
  return currentTeam.value === undefined
})
const newOwner = ref('');
const dialogResolve = ref(null)
const closeDialog = () => {
  currentTeam.value = undefined
  dialogResolve.value = true
}

// 退出团队
const quitTeam = (item) => {
  if (item.admin.length === 0 && item.member.length === 0) {
    ElMessage.error('您是团队中的唯一成员，无法退出团队')
    return
  }
  ElMessageBox.confirm(
      `确定要退出团队"${item.title}"吗？`,
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(async () => {
    if (item.owner === currentUser.username) {
      currentTeam.value = item
      await new Promise(() => {
        const stopWatch = watch(
            () => dialogResolve.value,
            (newValue) => {
              if (newValue === true) {
                stopWatch()
                dialogResolve.value = null
              }
            }
        )
      })
      // TODO: 将该团队的owner改成newOwner
    }
    highlightTeamId.value = null
    // TODO: 将该用户从团队中移除
    ElMessage.success('已退出团队')
  })
}

// 解散团队
const deleteTeam = (item) => {
  ElMessageBox.confirm(
      `确定要解散团队"${item.title}"吗？`,
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(() => {
    highlightTeamId.value = null
    removeTeam(item.id)
    ElMessage.success('团队已解散')
  }).catch(() => {
    console.log('取消删除')
  })
}

// 进入团队空间
const enterTeamSpace = (item) => {
  console.log('进入团队空间:', item.id)
  highlightTeamId.value = item.id
  emit('enterTeamSpace', item.id)
}
</script>

<template>
  <TwoColumnsWrapper :items="props.teams" empty-text="暂无团队">
    <template #item="{ item }">
      <el-card :class="item.id === highlightTeamId ? 'highlight-card' : 'card' ">
        <div class="card-content">
          <div class="title-line">
            <span class="title">{{item.title}}</span>
            <el-dropdown class="more" trigger="click" @command="handleCommand">
              <el-icon>
                <MoreFilled/>
              </el-icon>

              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                      :command="{ action: 'quit', item: item }"
                  >
                    退出团队
                  </el-dropdown-item>
                  <el-dropdown-item
                      :command="{ action: 'disband', item: item }"
                      v-if="item.owner === currentUser.username"
                  >
                    解散团队
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="info-line">
            <div class="info-wrapper">
            <span class="info">
              创建者：{{item.owner}}
            </span>
              <span class="info">
              成员：{{1 + item.admin.length + item.member.length}}人
            </span>
              <span class="info">
              我的角色：{{role(item)}}
            </span>
            </div>
            <el-button
                link
                type="text"
                class="enter-button"
                @click="enterTeamSpace(item)"
            >
              <el-icon>
                <Right/>
              </el-icon>
            </el-button>
          </div>
        </div>
      </el-card>
    </template>
  </TwoColumnsWrapper>

  <el-dialog
    v-model="visible"
    width="500px"
    center
    :show-close="false"
  >
    <template #header>
      <span class="dialog-title">为{{currentTeam.value.title}}选择新的拥有者</span>
    </template>

    <el-select v-model="newOwner">
      <el-option
          v-for="item in currentTeam.value.admin"
          :key="item"
          :label="item"
          :value="item"
      />
      <el-option
          v-for="item in currentTeam.value.member"
          :key="item"
          :label="item"
          :value="item"
      />
    </el-select>

    <template #footer>
      <div class="dialog-footer">
        <el-button
            class="check"
            type="primary"
            @click="closeDialog"
        >
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.card {
  background-color: white;
  height: 100% !important;
  display: flex;
  flex-direction: column;
}

.highlight-card {
  background-color: #ecf5ff;
  border-color: #ecf5ff;
  height: 100% !important;
  display: flex;
  flex-direction: column;
}

.card-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content:space-between;
  gap: 20px;
}

.title-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.title {
  font-size: 25px;
  font-weight: bold;
}

.more {
  font-size: 20px;
  margin-left: auto;
  margin-right: 0;
}

.more:hover {
  cursor: pointer;
  color: #409eff;
}

.info-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.info-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 0 30px;
  margin-right: 20px;
}

.info {
  display: inline-block;
  width: auto;
}

.enter-button {
  font-size: 30px;
  margin-left: auto;
  margin-right: 0;
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
  justify-content: center;
}

.check {
  width: 70px;
  height: 100%;
  font-size: 18px;
}
</style>