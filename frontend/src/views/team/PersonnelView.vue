<script setup lang="js">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { Back, InfoFilled, Plus, Minus } from "@element-plus/icons-vue";
import { currentUser, teamList } from '@/store/user.js'

const route = useRoute()
const router = useRouter()

const teamId = computed(() => parseInt(route.query.teamId))
const team = computed(() => teamList.value.find(t => t.id === teamId.value))

const isOwner = computed(() => team.value?.owner === currentUser.username)

// 从路由路径获取父页面名称
const parentPageName = computed(() => {
    const path = route.path
    if (path.includes('/owner/')) return '我拥有的团队'
    if (path.includes('/admin/')) return '我管理的团队'
    if (path.includes('/member/')) return '我参与的团队'
    return '全部团队'
})

const teamSpaceTitle = computed(() => {
    return team.value ? `${team.value.title}的团队空间` : '团队空间'
})

// 获取当前父路由路径
const parentPath = computed(() => {
  const match = route.path.match(/\/team\/(all|owner|admin|member)/)
  return match ? match[1] : 'all'
})

const handleBack = () => {
    router.push({
        path: `/team/${parentPath.value}/space`,
        query: { teamId: teamId.value }
    })
}

const goToParentPage = () => {
    router.push(`/team/${parentPath.value}`)
}

const goToTeamSpace = () => {
    router.push({
        path: `/team/${parentPath.value}/space`,
        query: { teamId: teamId.value }
    })
}

const viewAuthority = ref(0)
const authorityVisible = computed(() => viewAuthority.value !== 0)
const authorityDialogTitle = ref('')
const authorityDetail = (role) => {
    switch (role) {
      case 'owner':
        viewAuthority.value = 3
        authorityDialogTitle.value = '拥有者权限'
        break
      case 'admin':
        viewAuthority.value = 2
        authorityDialogTitle.value = '管理者权限'
        break
      case 'member':
        viewAuthority.value = 1
        authorityDialogTitle.value = '参与者权限'
        break
      default:
        break
    }
}

const closeAuthorityDialog = () => {
  viewAuthority.value = 0
  authorityDialogTitle.value = ''
}

// TODO: 更改成员权限，弹出一个el-dialog窗口，窗口内容我来写
const handleChangeAuthority = (up) => {

}

// TODO: 移除成员，弹出一个el-dialog窗口，窗口内容我来写
const handleRemoveMember = () => {
  
}

// TODO: 添加成员，弹出一个el-dialog窗口，窗口内容我来写
const handleAddMember = () => {
    
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <el-button
            link
            type="text"
            size="large"
            @click="handleBack"
        >
          <el-icon :size="25">
            <Back/>
          </el-icon>
        </el-button>
        <span class="route">
          <span class="clickable" @click="goToParentPage">{{ parentPageName }}</span>
          <span>&nbsp;>&nbsp;</span>
          <span class="clickable" @click="goToTeamSpace">{{ teamSpaceTitle }}</span>
          <span>&nbsp;>&nbsp;</span>
          <span class="present-directory">
            成员信息
          </span>
        </span>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <template #header>
          <div>
            <span v-if="isOwner" class="header">编辑</span>
            <span class="header">成员信息</span>
          </div>
        </template>

        <div class="main-content">
          <div class="key-container">
            <div class="key">
              拥有者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail('owner')"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            {{ team ? team.owner : '' }}
          </div>
          <br>

          <div class="key-container">
            <div class="key">
              管理者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail('admin')"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
                @click="handleChangeAuthority(false)"
            >
              <el-icon>
                <Minus/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"  
                @click="handleChangeAuthority(true)"
            >
              <el-icon>
                <Plus/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            {{ team && team.admin.length > 0 ? team.admin.join('、') : '暂无' }}
          </div>
          <br>

          <div class="key-container">
            <div class="key">
              参与者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail('member')"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
                @click="handleChangeAuthority(true)"
            >
              <el-icon>
                <Minus/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
                @click="handleChangeAuthority(false)"
            >
              <el-icon>
                <Plus/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            {{ team && team.member.length > 0 ? team.member.join('、') : '暂无' }}
          </div>
        </div>

        <template #footer>
          <div v-if="isOwner" class="footer">
            <el-button
                type="danger"
                class="remove-button"
                @click="handleRemoveMember"
            >
              移除成员
            </el-button>

            <el-button
                type="primary"
                class="add-button"
                @click="handleAddMember"
            >
              添加成员
            </el-button>
          </div>
          <div v-else class="footer">
            <el-button
                type="primary"
                class="back-button"
                @click="handleBack"
            >
              返回
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>

  <!-- 权限详情弹窗 -->
  <el-dialog
      v-model="authorityVisible"
      width="500px"
      center
      :beforeClose="closeAuthorityDialog"
  >
    <template #header>
      <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ authorityDialogTitle }}</span>
    </template>
    <ul class="dialog-item">
      <li>浏览团队中的所有任务</li>
      <li>操作分配给自己的任务，但只能修改任务状态</li>
      <li v-if="viewAuthority >= 2">创建/修改/删除任务</li>
      <li v-if="viewAuthority >= 2">将任务分配给团队成员</li>
      <li v-if="viewAuthority >= 3">将其他用户添加到团队</li>
      <li v-if="viewAuthority >= 3">将参与者设置为管理者</li>
      <li v-if="viewAuthority >= 3">将管理者设置为参与者</li>
    </ul>
  </el-dialog>

  <!-- 移除成员弹窗 -->
  <el-dialog
      v-model="removeMemberDialogVisible"
      title="移除成员"
      width="400px"
  >
    <el-form label-width="100px">
      <el-form-item label="选择成员">
        <el-select v-model="memberToRemove" placeholder="请选择要移除的成员">
          <el-option
              v-for="member in [...(team?.admin || []), ...(team?.member || [])]"
              :key="member"
              :label="member"
              :value="member"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeRemoveDialog">取消</el-button>
      <el-button type="danger" @click="confirmRemoveMember">移除</el-button>
    </template>
  </el-dialog>

  <!-- 添加成员弹窗 -->
  <el-dialog
      v-model="addMemberDialogVisible"
      title="添加成员"
      width="400px"
  >
    <el-form label-width="100px">
      <el-form-item label="用户名">
        <el-input v-model="newMemberName" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="角色">
        <el-radio-group v-model="newMemberRole">
          <el-radio label="admin">管理者</el-radio>
          <el-radio label="member">参与者</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeAddDialog">取消</el-button>
      <el-button type="primary" @click="confirmAddMember">添加</el-button>
    </template>
  </el-dialog>

</template>

<style scoped>
.inner-header {
  left: 0;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  flex-direction: row;
  gap: 15px;
  align-items: center;
}

.route {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: #333333;
}

.present-directory {
  font-weight: bold;
}

.main-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.box-card {
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
}

.header {
  font-size: 25px;
  font-weight: bold;
}

:deep(.el-card__header) {
  border-bottom: none;
  display: flex;
  justify-content: center;
}

.main-content {
  margin-left: 25px;
  margin-right: 25px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.key-container {
  width: 100%;
  display: flex;
  flex-direction: row;
}

.key {
  font-weight: bold;
  font-size: 20px;
}

.info {
  margin-left: 5px;
  margin-right: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 0;
}

.authority-button {
  padding: 5px;
  width: 40px;
  height: 40px;
}

.value {
  font-size: 18px;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

.remove-button {
  margin-left: 20%;
  margin-right: auto;
  width: 120px;
  height: 100%;
  font-size: 20px;
}

.add-button {
  margin-left: auto;
  margin-right: 20%;
  width: 120px;
  height: 100%;
  font-size: 20px;
}

.back-button {
  width: 100px;
  height: 100%;
  font-size: 20px;
}
.clickable {
  cursor: pointer;
  color: #409eff;
}

.clickable:hover {
  text-decoration: underline;
}

.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-item {
  font-size: 18px;
}
</style>