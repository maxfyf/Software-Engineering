<script setup lang="js">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { List, Connection, Setting, Bell } from "@element-plus/icons-vue";
import {
  acceptNotification,
  clearNotificationList,
  currentUser,
  handleLogout,
  initNotificationList,
  initTaskList,
  initTeamList,
  initUserInfo,
  isLoggedIn,
  markAllNotificationsRead,
  notifications,
  readNotification,
  rejectNotification,
  resetNotificationList,
  unreadCount
} from '@/store/user.js'

const route = useRoute()
const router = useRouter()

// 导航栏选中状态
const activeMenu = ref('/task')

// 接受通知消息（用于转让owner或邀请进入团队，needOperation=true，需发送通知给owner告知结果）
const handleAccept = async (item) => {
  if (item.isRead) return
  await acceptNotification(item.id)
  await Promise.all([initTeamList(true), initTaskList(true)])
  ElMessage.success(`已接受：${item.text}`)
}

// 拒绝通知消息（用于转让owner或邀请进入团队，needOperation=true，需发送通知给owner告知结果）
const handleReject = async (item) => {
  if (item.isRead) return
  await rejectNotification(item.id)
  ElMessage.warning(`已拒绝：${item.text}`)
}

// 确认通知消息（用于通知团队成员其被分配了新任务/通知团队成员其被owner移出团队/通知原owner其权限转交成功与否/通知owner成员加入或拒绝加入团队，needOperation=false）
const handleRead = async (item) => {
  if (item.isRead) return
  await readNotification(item.id)
  ElMessage.warning(`已确认：${item.text}`)
}

// 清空消息
const clearNotifications = async () => {
  await clearNotificationList()
  ElMessage.info('通知已清空')
}

// 全部标记为已读
const markAllAsRead = async () => {
  await markAllNotificationsRead()
  ElMessage.info('所有通知已标记为已读')
}

// 监听路由变化，更新导航栏选中状态
watch(() => route.path, (newPath) => {
    if (newPath.startsWith('/task')) {
        activeMenu.value = '/task'
    } else if (newPath.startsWith('/team')) {
      activeMenu.value = '/team'
    } else if (newPath.startsWith('/settings')) {
        activeMenu.value = '/settings'
    } else {
        activeMenu.value = newPath
    }
}, { immediate: true })

// 页面加载时检查登录状态
onMounted(async () => {
    await initUserInfo()
    if (isLoggedIn.value) {
      await initNotificationList()
    }
})

watch(() => currentUser.username, async (username) => {
  if (isLoggedIn.value && username) {
    await initNotificationList()
  } else {
    resetNotificationList()
  }
})

// 退出登录处理
const onHandleLogout = async () => {
  const result = await handleLogout()
  if (result && result.success && result.redirect) {
    await router.push(result.redirect)
  }
}
</script>

<template>
  <el-menu
    mode="horizontal"
    :default-active="activeMenu"
    :key="activeMenu"
    class="navbar"
    :router="true"
  >
    <!-- 网站信息 -->
    <img src="/src/assets/images/logo.png" class="logo" alt="Logo">
    <span class="site-name">协作式任务管理系统</span>
    <div v-if="isLoggedIn" class="routes">
      <el-menu-item
          index="/task"
          class="route"
          :class="{ 'active-border': activeMenu === '/task' }"
      >
        <el-icon>
          <List/>
        </el-icon>
        我的任务
      </el-menu-item>

      <el-menu-item
          index="/team"
          class="route"
          :class="{ 'active-border': activeMenu === '/team' }"
      >
        <el-icon>
          <Connection/>
        </el-icon>
        我的团队
      </el-menu-item>

      <el-menu-item
          index="/settings"
          class="route"
          :class="{ 'active-border': activeMenu === '/settings' }"
      >
        <el-icon>
          <Setting/>
        </el-icon>
        设置
      </el-menu-item>
    </div>

    <!-- 账户信息 -->
    <div class="account">
      <div v-if="isLoggedIn">
        <el-popover
            placement="bottom"
            :width="250"
            :offset="0"
            trigger="click"
            :append-to-body="true"
            popper-class="second-layer-popover"
        >
          <template #reference>
            <el-badge
                :value="unreadCount > 99 ? '99+' : (unreadCount > 0 ? unreadCount : '')"
                class="notifications"
            >
              <el-icon>
                <Bell/>
              </el-icon>
            </el-badge>
          </template>

          <div class="notification-popover">
            <div class="notification-header">
              <span class="notification-title">通知</span>
              <div class="notification-buttons">
                <el-button link type="primary" @click="clearNotifications" v-if="notifications.length > 0">
                  清空
                </el-button>
                <el-button link type="primary" @click="markAllAsRead" v-if="unreadCount > 0">
                  全部已读
                </el-button>
              </div>
            </div>
            <div class="notification-list" v-if="notifications.length">
              <div
                  v-for="item in notifications"
                  :key="item.id"
                  class="notification-item"
                  :class="{ unread: !item.isRead }"
              >
                <div class="notification-text">{{ item.text }}</div>
                <div class="notification-actions" v-if="!item.isRead">
                  <div v-if="item.needOperation">
                    <el-button size="small" link type="primary" @click="handleAccept(item)">
                      接受
                    </el-button>
                    <el-button size="small" link type="danger" @click="handleReject(item)">
                      拒绝
                    </el-button>
                  </div>
                  <div v-else>
                    <el-button size="small" link type="primary" @click="handleRead(item)">
                      确认
                    </el-button>
                  </div>
                </div>
                <div class="notification-actions" v-else>
                  <el-tag size="small" type="info">
                    <span v-if="item.needOperation">已处理</span>
                    <span v-else>已确认</span>
                  </el-tag>
                </div>
              </div>
            </div>
            <div class="empty-placeholder" v-else>
              暂无通知
            </div>
          </div>
        </el-popover>

        <el-popover
          placement="bottom"
          :width="350"
          :height="250"
          :offset="0"
          trigger="hover"
          :append-to-body="true"
          popper-class="top-layer-popover"
        >
          <template #reference>
            <span class="username">
              {{ currentUser.username }}
            </span>
          </template>
          <div>
            <h2 class="popover-title">
              {{ currentUser.username }}
            </h2>
            <p class="popover-info" v-if="currentUser.lastName && currentUser.firstName">
              <span class="key">全名：</span>
              {{ currentUser.lastName }}{{ currentUser.firstName }}
            </p>
            <p class="popover-info" v-if="currentUser.phone">
              <span class="key">电话号码：</span>
              {{ currentUser.phone }}
            </p>
            <p class="popover-info" v-if="currentUser.email">
              <span class="key">电子邮箱：</span>
              {{ currentUser.email }}
            </p>
            <div class="popover-button">
              <el-button
                  type="danger"
                  class="logout-button"
                  @click="onHandleLogout"
              >
                退出登录
              </el-button>
            </div>
          </div>
        </el-popover>
      </div>
      <span v-else class="info">
        未登录
      </span>
    </div>
  </el-menu>

  <main class="main">
    <router-view/>
    <footer v-if="isLoggedIn === false" class="footer">
      <p class="copyright">&copy; 2026 封逸凡、徐熙竣、丁泓森、赵冠杰、陈熙睿团队版权所有</p>
    </footer>
  </main>
</template>

<style scoped>
.navbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  background: white;
  height: 50px;
  display: flex;
  align-items: center;
}

.logo {
  margin-left: 20px;
  width: 40px;
  height: auto;
}

.site-name {
  margin-left: 15px;
  margin-right: 15px;
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  font-weight: 800;
  font-size: 30px;
  background: linear-gradient(135deg, #4ab7ff, #1e6ef0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 20px rgba(0, 160, 255, 0.3);
}

.routes {
  display: flex;
  margin-left: 10px;
}

.route {
  font-size: large;
  cursor: pointer;
}

.route:hover {
  text-shadow: 2px 2px 3px rgba(0,0,0,0.5);
}

.notifications {
  color: black;
  font-size: large;
  margin-right: 20px;
}

.notifications:hover {
  cursor: pointer;
  text-shadow: 2px 2px 3px rgba(0,0,0,0.5);
  color: #409eff;
}

.notification-popover {
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.notification-header {
  display: flex;
  align-items: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.notification-title {
  font-size: 20px;
  font-weight: bold;
}

.notification-buttons {
  display: flex;
  flex-direction: row;
  margin-left: auto;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  max-height: 200px;
}

:deep(.notification-list) {
  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--el-color-info-light-8);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background-color: var(--el-color-info);
  }
}

.notification-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.notification-item.unread {
  background-color: #f0f9ff;
}

.notification-text {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-word;
}

.notification-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.empty-placeholder {
  text-align: center;
  padding: 32px 16px;
  color: #909399;
  font-size: 14px;
}

.account {
  position: absolute;
  right: 0;
  display: flex;
  align-items: center;
}

.username {
  font-size: large;
  margin-right: 30px;
  color: #409eff;
  cursor: pointer;
}

.username:hover {
  font-size: large;
  color: #409eff;
  text-shadow: 0 0 5px #fff, 0 0 10px #0080ff, 0 0 15px #0080ff;
}

.top-layer-popover {
  z-index: 200;
}

.top-layer-popover .popover-content {
  position: relative;
  z-index: 200;
}

.popover-title {
  font-weight: bold;
  text-align: center;
}

.popover-info {
  padding: 3px 10px;
}

.key {
  font-weight: bold;
}

.popover-button {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.logout-button {
  width: 100px;
  height: 30px;
  font-size: 15px;
}

.info {
  font-size: large;
  margin-right: 30px;
  color: black;
}

.main {
  position: absolute;
  top: 50px;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #ececec;
  overflow: auto;
}

.footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30px;
  background-color: #d8d8d8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copyright {
  color: black;
  font-size: medium;
}

.active-border {
  border-bottom: 2px solid #409eff !important;
}
</style>