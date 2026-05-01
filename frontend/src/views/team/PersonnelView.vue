<script setup lang="js">
import { computed, ref } from 'vue'
import Draggable from 'vuedraggable'
import { useRoute, useRouter } from 'vue-router'
import HeaderWrapper from "@/components/HeaderWrapper.vue"
import Route from "@/components/Route.vue"
import { currentUser, teamList } from '@/store/user.js'
import { handleBack } from '@/utils/routeManager.js'
import { Delete, Plus, InfoFilled } from "@element-plus/icons-vue"
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/request/api.js'

const route = useRoute()
const router = useRouter()

const teamId = computed(() => parseInt(route.query.teamId))
const team = computed(() => teamList.value.find(t => t.id === teamId.value) || {})

const addVisible = ref(false)

const objects = computed(() => {
  if (!teamList.value) {
    return { owner: '', admin: [], member: [] }
  }

  const currentTeam = teamList.value.find(t => t.id === teamId.value)
  if (!currentTeam) {
    return { owner: '', admin: [], member: [] }
  }

  const adminList = Array.isArray(currentTeam.admin) ? currentTeam.admin : []
  const memberList = Array.isArray(currentTeam.member) ? currentTeam.member : []

  return {
    owner: currentTeam.owner || '',
    admin: adminList.map(name => ({ id: name, name: name })),
    member: memberList.map(name => ({ id: name, name: name }))
  }
})
const isDragging = ref(false)
const draggedMemberName = ref(null)

const isOwner = computed(() => team.value?.owner === currentUser.username)

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

const closeAddDialog = () => {
  addVisible.value = false
}

const closeAuthorityDialog = () => {
  viewAuthority.value = 0
  authorityDialogTitle.value = ''
}

const handleDragStart = (event) => {
  isDragging.value = true
  if (event && event.item) {
    draggedMemberName.value = event.item.textContent.trim()
  }
}

const handleDragEnd = () => {
  isDragging.value = false
  setTimeout(() => {
    draggedMemberName.value = null
  }, 100)
}

const onDragChange = async (event) => {
  if (!event.added) return

  const memberName = event.added.element.name

  let newRole = null
  if (objects.value.admin.some(a => a.name === memberName)) {
    newRole = 'admin'
  } else if (objects.value.member.some(m => m.name === memberName)) {
    newRole = 'member'
  }

  if (!newRole) return

  try {
    await api.setMemberRole(teamId.value, memberName, newRole)
    ElMessage.success('角色更改成功')

    const currentTeam = teamList.value.find(t => t.id === teamId.value)
    if (currentTeam) {
      currentTeam.admin = currentTeam.admin.filter(a => a !== memberName)
      currentTeam.member = currentTeam.member.filter(m => m !== memberName)
      if (newRole === 'admin') {
        currentTeam.admin.push(memberName)
      } else {
        currentTeam.member.push(memberName)
      }
    }
  } catch (error) {
    ElMessage.error('角色更改失败')
    teamList.value = [...teamList.value]
  }
}

const doRemoveMember = async (username) => {
  try {
    await api.removeMember(teamId.value, username)
    const currentTeam = teamList.value.find(t => t.id === teamId.value)
    if (currentTeam) {
      currentTeam.admin = currentTeam.admin.filter(a => a !== username)
      currentTeam.member = currentTeam.member.filter(m => m !== username)
    }
    ElMessage.success('成员已移除')
  } catch (error) {
    ElMessage.error('移除成员失败')
  }
}

const handleRemoveMember = async () => {
  const removableMembers = [
    ...(team.value?.admin || []),
    ...(team.value?.member || [])
  ]

  if (removableMembers.length === 0) {
    ElMessage.warning('没有可移除的成员')
    return
  }

  if (draggedMemberName.value && removableMembers.includes(draggedMemberName.value)) {
    const name = draggedMemberName.value
    try {
      await ElMessageBox.confirm(
        `确定要移除成员"${name}"吗？`,
        '移除成员',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          confirmButtonType: 'danger'
        }
      )
      await doRemoveMember(name)
    } catch (error) {
      // 取消移除
    }
    return
  }

  ElMessageBox.prompt('请输入要移除的成员用户名', '移除成员', {
    confirmButtonText: '移除',
    cancelButtonText: '取消',
    confirmButtonType: 'danger',
    inputValidator: (value) => {
      if (!value) return '请输入用户名'
      if (!removableMembers.includes(value)) return '该用户不在团队中或无法移除'
      return true
    }
  }).then(async ({ value }) => {
    await doRemoveMember(value)
  }).catch(() => {})
}

const newUsername = ref('')
const newAuthority = ref('member')
const handleAdd = () => {
  addVisible.value = true
}

const handleAddMember = async () => {
  if (!newUsername.value || !newUsername.value.trim()) {
    ElMessage.error('请输入用户名')
    return
  }

  const username = newUsername.value.trim()
  const role = newAuthority.value

  try {
    await api.addMember(teamId.value, username, role)

    const currentTeam = teamList.value.find(t => t.id === teamId.value)
    if (currentTeam) {
      if (role === 'admin' && !currentTeam.admin.includes(username)) {
        currentTeam.admin.push(username)
      } else if (role === 'member' && !currentTeam.member.includes(username)) {
        currentTeam.member.push(username)
      }
    }

    ElMessage.success('成员添加成功')
    addVisible.value = false
    newUsername.value = ''
    newAuthority.value = 'member'
  } catch (error) {
    ElMessage.error('添加成员失败')
  }
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <Route :route="route" :router="router"/>
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

        <div v-if="isOwner" class="button-header">
          <div v-if="isDragging" class="delete-button" @dragover.prevent @drop="handleRemoveMember" @click="handleRemoveMember">
            <el-icon><Delete /></el-icon>
          </div>

          <el-button type="primary" class="new-button" @click="handleAdd">
            <el-icon><Plus/></el-icon>
            <span>
              &nbsp;添加成员
            </span>
          </el-button>
        </div>

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
          </div>
          <div v-if="isOwner">
            <Draggable
                v-model="objects.admin"
                group="personnel"
                item-key="id"
                class="draggable-list"
                @start="handleDragStart"
                @end="handleDragEnd"
                @change="onDragChange"
                :force-fallback="true"
            >
              <template #item="{ element }">
                <div class="draggable-item">
                  {{ element.name }}
                </div>
              </template>
            </Draggable>
          </div>
          <div v-else class="value">
            {{ team?.admin?.length > 0 ? team.admin.join('、') : '暂无' }}
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
          </div>
          <div v-if="isOwner">
            <Draggable
                v-model="objects.member"
                group="personnel"
                item-key="id"
                class="draggable-list"
                @start="handleDragStart"
                @end="handleDragEnd"
                @change="onDragChange"
                :force-fallback="true"
            >
              <template #item="{ element }">
                <div class="draggable-item">
                  {{ element.name }}
                </div>
              </template>
            </Draggable>
          </div>
          <div v-else class="value">
            {{ team?.member?.length > 0 ? team.member.join('、') : '暂无' }}
          </div>
        </div>

        <template #footer>
          <div class="footer">
            <el-button
                type="primary"
                class="back-button"
                @click="handleBack(route, router, 1)"
            >
              返回
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>

  <!-- 添加用户弹窗 -->
  <el-dialog
      v-model="addVisible"
      width="500px"
      center
      :beforeClose="closeAddDialog"
  >
    <template #header>
      <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;添加用户</span>
    </template>
    <div class="dialog-body">
      <el-input
          v-model="newUsername"
          type="text"
          placeholder="用户名"
      />

      <el-select v-model="newAuthority">
        <el-option label="管理者" value="admin"/>
        <el-option label="参与者" value="member"/>
      </el-select>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button
            type="default"
            class="cancel"
            @click="closeAddDialog"
        >
          取消
        </el-button>

        <el-button
            type="primary"
            class="check"
            @click="handleAddMember"
        >
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>

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
</template>

<style scoped>
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

.button-header {
  width: 100%;
  display: flex;
  margin-bottom: 25px;
}

.delete-button {
  font-size: 20px;
  margin-left: 40px;
  margin-right: auto;
}

.delete-button:hover {
  color: #f56c6c !important;
}

.new-button {
  width: 100px;
  margin-left: auto;
  margin-right: 20px;
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

.draggable-list {
  height: 80px;
  overflow-y: auto;
  background-color: #f8f9fa;
  border: 1px solid #eef;
  border-radius: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px;
}

.draggable-list:hover {
  border: 1px solid #409eff;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.15);
}

.draggable-item {
  display: inline-block;
  width: auto;
  height: 30px;
  background-color: white;
  color: black;
  font-size: 15px;
  border-radius: 5px;
  text-align: center;
  cursor: move;
  box-sizing: border-box;
  padding: 0 5px;
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.1);
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.draggable-item:hover {
  background-color: #ecf5ff;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
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

.dialog-item {
  font-size: 18px;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

.back-button {
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>