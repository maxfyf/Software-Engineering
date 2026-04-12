<script setup lang="js">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { List, Setting } from "@element-plus/icons-vue";
import { handleLogout, currentUser, isLoggedIn, initUserInfo } from '@/store/user.js'

const route = useRoute()
const router = useRouter()

// 导航栏选中状态
const activeMenu = ref('/task')


// 监听路由变化，更新导航栏选中状态
watch(() => route.path, (newPath) => {
    if (newPath.startsWith('/task')) {
        activeMenu.value = '/task'
    } else if (newPath.startsWith('/settings')) {
        activeMenu.value = '/settings'
    } else {
        activeMenu.value = newPath
    }
}, { immediate: true })

// 页面加载时检查登录状态
onMounted(async () => {
    await initUserInfo()
})

// 退出登录处理
const onHandleLogout = async () => {
  const result = await handleLogout()
  if (result && result.success && result.redirect) {
    router.push(result.redirect)
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
      <span v-if="isLoggedIn">
        <el-popover
          placement="bottom"
          width="350px"
          height="250px"
          trigger="hover"
          popper-class="hover-popover"
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
            <p class="popover-info" v-if="currentUser.lastName !== '' && currentUser.firstName !== ''">
              <span class="key">全名：</span>
              {{ currentUser.lastName }}{{ currentUser.firstName }}
            </p>
            <p class="popover-info" v-if="currentUser.phone !== ''">
              <span class="key">电话号码：</span>
              {{ currentUser.phone }}
            </p>
            <p class="popover-info" v-if="currentUser.email !== ''">
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
      </span>
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
