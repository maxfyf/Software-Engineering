<script setup lang="js">
import { computed } from "vue";
import { getUserProfile, userProfileMap } from "@/store/user.js";

const props = defineProps({
  route: {
    type: Object,
    required: true,
    default: null
  },

  operations: {
    type: Array,
    required: true,
    default: () => []
  },

  currentPage: {
    type: Number,
    default: 1
  },

  pageSize: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['page-change'])

const total = computed(() => props.operations.length)
const pageData = computed(() => {
  const start = (props.currentPage - 1) * props.pageSize
  const end = start + props.pageSize
  return props.operations.slice(start, end)
})

const isTeamSpace = computed(() => {
  return props.route.fullPath.includes('/space')
})

// 表格行样式回调
const tableRowClassName = () => {
  return ''
}

const tableKey = computed(() => {
  return pageData.value.map(item => item.id).join('-')
})

// 切换页面
const handleCurrentChange = (page) => {
  emit('page-change', page)
}

const getObjectText = (object) => {
  if (object && typeof object === 'object') {
    const title = object.title ?? object.name ?? object.label ?? object.id ?? ''
    return object.deleted ? `${title}（已删除）` : title
  }
  return object ?? ''
}

const formatOperator = (operation) => {
  const operator = operation.operator
  // TODO: 仿照TaskList，根据操作者是否还在团队中添加‘已离队’
}

const hideOperatorDetail = (operation) => {
  const operator = operation.operator
  //TODO: 返回命题“该operator不在团队中”的布尔值
}

const loadOperatorProfile = async (operation) => {
  const username = operation.operator

  try {
    await getUserProfile(username)
  } catch (error) {
    console.error('获取操作者信息失败:', error)
  }
}

const getOperatorProfile = (operation) => {
  const username = operation.operator
  return username ? userProfileMap[username] : null
}
</script>

<template>
  <el-row>
    <el-col>
      <el-table
          :data="pageData"
          empty-text="暂无操作记录"
          stripe
          class="operation-table"
          :row-class-name="tableRowClassName"
          :key="tableKey"
      >
        <el-table-column
            label="操作对象"
            min-width="15%"
            align="left"
        >
          <template #default="{ row }">
            {{ getObjectText(row.object) }}
          </template>
        </el-table-column>
        <el-table-column
            prop="operator"
            label="操作人"
            v-if="isTeamSpace"
            min-width="15%"
            align="center"
        >
          <template v-slot:default="scope">
            <span v-if="hideOperatorDetail(scope.row)">
              {{ formatOperator(scope.row) }}
            </span>
            <el-popover
                v-else
                placement="bottom"
                :fallback-placements="['bottom', 'top']"
                :width="350"
                :height="250"
                :offset="0"
                trigger="hover"
                :append-to-body="true"
                popper-class="user-detail-popover"
                @show="loadOperatorProfile(scope.row)"
            >
              <template #reference>
                <span class="assignee">
                  {{ formatOperator(scope.row) }}
                </span>
              </template><div>
              <h2 class="popover-title">
                {{ formatOperator(scope.row) }}
              </h2>
              <p class="popover-info" v-if="getOperatorProfile(scope.row)?.lastName && getOperatorProfile(scope.row)?.firstName">
                <span class="key">全名：</span>
                {{ getOperatorProfile(scope.row).lastName }}{{ getOperatorProfile(scope.row).firstName }}
              </p>
              <p class="popover-info" v-if="getOperatorProfile(scope.row)?.phone">
                <span class="key">电话号码：</span>
                {{ getOperatorProfile(scope.row).phone }}
              </p>
              <p class="popover-info" v-if="getOperatorProfile(scope.row)?.email">
                <span class="key">电子邮箱：</span>
                {{ getOperatorProfile(scope.row).email }}
              </p>
            </div>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column
            prop="description"
            label="描述"
            :min-width="isTeamSpace ? '55%' : '70%'"
            align="center"
        />
        <el-table-column
            prop="operatedAt"
            label="操作时间"
            min-width="15%"
            align="center"
        />
      </el-table>
    </el-col>
  </el-row>

  <el-pagination
      @current-change="handleCurrentChange"
      :current-page="props.currentPage"
      :page-size="props.pageSize"
      layout="prev, pager, next"
      :total="total"
      class="pagination"
  />
</template>

<style scoped>
.operation-table {
  width: 100%;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>