<script setup lang="js">
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { List, Setting } from "@element-plus/icons-vue";
import { handleLogout, currentUser } from '@/store/user.js'
import { isLoggedIn } from '@/store/user.js'

const route = useRoute()
const activeMenu = computed(() => {
  if (route.path.startsWith('/task')) {
    return '/task'
  }
  return route.path
})
const activeIndex = ref('/')    //当前网页路径

// 页面加载时检查登录状态
onMounted(() => {
    const savedIsLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
    const savedUsername = localStorage.getItem('username')

    console.log('App 挂载时检查登录状态:', { savedIsLoggedIn, savedUsername })

    if (savedIsLoggedIn && savedUsername) {
        isLoggedIn.value = true
        // 从 localStorage 加载用户名（完整信息应该从后端获取）
        currentUser.username = savedUsername
        console.log('已恢复登录状态，用户名:', savedUsername)
        // TODO: 这里可以从后端重新获取完整的用户信息
    } else {
        isLoggedIn.value = false
        console.log('未登录状态')
    }
})

watch(() => route.path, (newPath) => {
  console.log('路径变化：', newPath)
  activeIndex.value = newPath
}, { immediate: true })
</script>

<template>
  <el-menu
    mode="horizontal"
    :default-active="activeMenu"
    class="navbar"
    :router="true"
  >
    <!-- 网站信息 -->
    <img src="/src/assets/images/logo.jpg" class="logo" alt="Logo">
    <span class="site-name">协作式任务管理系统</span>
    <div v-if="isLoggedIn" class="routes">
      <el-menu-item index="/task" class="route">
        <el-icon>
          <List/>
        </el-icon>
        我的任务
      </el-menu-item>
      <el-menu-item index="/settings" class="route">
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
          width="200px"
          height="200px"
          trigger="hover"
          popper-class="hover-popover"
        >
          <template #reference>
            <span class="username">
              {{ currentUser.username }}
            </span>
          </template>
          <div>
            <h2 class="popover-title">{{ currentUser.username }}</h2>
            <p class="popover-info"><strong>Full Name:</strong> {{ currentUser.firstName }} {{ currentUser.lastName }}</p>
            <p class="popover-info"><strong>Email:</strong> {{ currentUser.email }}</p>
            <div class="popover-button">
              <el-button
                  type="danger"
                  class="logout-button"
                  @click="handleLogout"
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

  <main v-if="isLoggedIn" class="main-without-footer">
    <router-view/>
  </main>

  <main v-else class="main-with-footer">
    <router-view/>
    <footer class="footer">
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
  padding: 0 10px;
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

.main-without-footer {
  position: absolute;
  top: 50px;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #ececec;
  overflow: auto;
}

.main-with-footer {
  position: absolute;
  top: 50px;
  bottom: 30px;
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

</style>
