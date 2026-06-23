<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { ref } from "vue";
import { useRoute, useRouter } from 'vue-router';
import { currentUser, handleCancelAccount, validateEmail, validatePhone } from "@/store/user.js";
import Route from "@/components/Route.vue";
import { Edit } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import api from "@/request/api.js";

const route = useRoute()
const router = useRouter()

const originalFirstName = ref('')
const originalLastName = ref('')
const originalPhone = ref('')
const originalEmail = ref('')

const syncUserInfo = (data = {}) => {
  currentUser.firstName = data.firstName ?? data.first_name ?? currentUser.firstName
  currentUser.lastName = data.lastName ?? data.last_name ?? currentUser.lastName
  currentUser.phone = data.phone ?? data.phone_number ?? currentUser.phone
  currentUser.email = data.email ?? currentUser.email
}

const updateUserInfo = async (payload) => {
  const res = await api.updateUserInfo(payload)
  syncUserInfo(res.data || {})
}

const editingFirstName = ref(false);
const editFirstName = () => {
  originalFirstName.value = currentUser.firstName || ''
  editingFirstName.value = true;
}
const updateFirstName = async () => {
  const nextValue = (currentUser.firstName || '').trim()
  try {
    await updateUserInfo({ first_name: nextValue || null })
    currentUser.firstName = nextValue
    editingFirstName.value = false
    ElMessage.success('名已更新')
  } catch (error) {
    currentUser.firstName = originalFirstName.value
  }
}

const editingLastName = ref(false);
const editLastName = () => {
  originalLastName.value = currentUser.lastName || ''
  editingLastName.value = true;
}
const updateLastName = async () => {
  const nextValue = (currentUser.lastName || '').trim()
  try {
    await updateUserInfo({ last_name: nextValue || null })
    currentUser.lastName = nextValue
    editingLastName.value = false
    ElMessage.success('姓已更新')
  } catch (error) {
    currentUser.lastName = originalLastName.value
  }
}

const editingPhone = ref(false);
const editPhone = () => {
  originalPhone.value = currentUser.phone || ''
  editingPhone.value = true;
}
const updatePhone = async () => {
  const nextValue = (currentUser.phone || '').trim()
  if (!validatePhone(nextValue)) {
    currentUser.phone = originalPhone.value
    editingPhone.value = false
    ElMessage.error('电话号码必须为8位或11位数字')
    return
  }

  try {
    await updateUserInfo({ phone_number: nextValue || null })
    currentUser.phone = nextValue
    editingPhone.value = false
    ElMessage.success('电话号码已更新')
  } catch (error) {
    currentUser.phone = originalPhone.value
  }
}

const editingEmail = ref(false);
const editEmail = () => {
  originalEmail.value = currentUser.email || ''
  editingEmail.value = true;
}
const updateEmail = async () => {
  const nextValue = (currentUser.email || '').trim()
  if (!validateEmail(nextValue)) {
    currentUser.email = originalEmail.value
    editingEmail.value = false
    ElMessage.error('邮箱格式不正确，应为"xxx@xxx.xxx"')
    return
  }

  try {
    await updateUserInfo({ email: nextValue || null })
    currentUser.email = nextValue
    editingEmail.value = false
    ElMessage.success('电子邮箱已更新')
  } catch (error) {
    currentUser.email = originalEmail.value
  }
}

const onHandleCancelAccount = async () => {
  const result = await handleCancelAccount()
  if (result && result.success && result.redirect) {
    await router.push(result.redirect)
  }
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <div class="item">
          <span class="key">用户名：</span>
          {{ currentUser.username || '未设置' }}
        </div>

        <div class="item">
          <span class="key">名：</span>
          <div v-if="editingFirstName" class="value">
            <el-input
                class="short-input"
                v-model="currentUser.firstName"
                type="text"
            />
            <el-button
                type="primary"
                @click="updateFirstName"
            >
              确认
            </el-button>
          </div>
          <div v-else class="value">
            {{ currentUser.firstName || '未设置' }}
            <el-popover
                placement="bottom"
                :offset="0"
                trigger="hover"
                popper-style="min-width: 0; width: auto;"
            >
              <template #reference>
                <el-icon class="edit" @click="editFirstName">
                  <Edit/>
                </el-icon>
              </template>
              <span v-if="currentUser.firstName">
                编辑名
              </span>
              <span v-else>
                设置名
              </span>
            </el-popover>
          </div>
        </div>

        <div class="item">
          <span class="key">姓：</span>
          <div v-if="editingLastName" class="value">
            <el-input
                class="short-input"
                v-model="currentUser.lastName"
                type="text"
            />
            <el-button
                type="primary"
                @click="updateLastName"
            >
              确认
            </el-button>
          </div>
          <div v-else class="value">
            {{ currentUser.lastName || '未设置' }}
            <el-popover
                placement="bottom"
                :offset="0"
                trigger="hover"
                popper-style="min-width: 0; width: auto;"
            >
              <template #reference>
                <el-icon class="edit" @click="editLastName">
                  <Edit/>
                </el-icon>
              </template>
              <span v-if="currentUser.lastName">
                编辑姓
              </span>
              <span v-else>
                设置姓
              </span>
            </el-popover>
          </div>
        </div>

        <div class="item">
          <span class="key">电话号码：</span>
          <div v-if="editingPhone" class="value">
            <el-input
                class="long-input"
                v-model="currentUser.phone"
                type="text"
            />
            <el-button
                type="primary"
                @click="updatePhone"
            >
              确认
            </el-button>
          </div>
          <div v-else class="value">
            {{ currentUser.phone || '未设置' }}
            <el-popover
                placement="bottom"
                :offset="0"
                trigger="hover"
                popper-style="min-width: 0; width: auto;"
            >
              <template #reference>
                <el-icon class="edit" @click="editPhone">
                  <Edit/>
                </el-icon>
              </template>
              <span v-if="currentUser.phone">
                编辑电话号码
              </span>
                <span v-else>
                设置电话号码
              </span>
            </el-popover>
          </div>
        </div>

        <div class="item">
          <span class="key">电子邮箱：</span>
          <div v-if="editingEmail" class="value">
            <el-input
                class="long-input"
                v-model="currentUser.email"
                type="text"
            />
            <el-button
                type="primary"
                @click="updateEmail"
            >
              确认
            </el-button>
          </div>
          <div v-else class="value">
            {{ currentUser.email || '未设置' }}
            <el-popover
                placement="bottom"
                :offset="0"
                trigger="hover"
                popper-style="min-width: 0; width: auto;"
            >
              <template #reference>
                <el-icon class="edit" @click="editEmail">
                  <Edit/>
                </el-icon>
              </template>
              <span v-if="currentUser.email">
                编辑电子邮箱
              </span>
              <span v-else>
                设置电子邮箱
              </span>
            </el-popover>
          </div>
        </div>

        <template #footer>
          <div class="footer">
            <el-button
                class="cancel-button"
                type="danger"
                @click="onHandleCancelAccount"
            >
              注销账号
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.route-wrapper {
  display: flex;
  left: 20px;
  align-items: center;
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

.item {
  width: 100%;
  display: flex;
  align-items: center;
  margin-top: 20px;
  font-size: 20px;
}

.key {
  font-weight: bold;
}

.value {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 15px;
}

.edit:hover {
  cursor: pointer;
  color: #409eff;
}

.short-input :deep(.el-input__inner) {
  height: 30px;
  font-size: medium;
  width: 150px;
}

.long-input :deep(.el-input__inner) {
  height: 30px;
  font-size: medium;
  width: 300px;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  justify-content: center;
}

.cancel-button {
  width: 150px;
  height: 100%;
  font-size: 20px;
}
</style>