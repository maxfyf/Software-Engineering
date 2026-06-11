<script setup lang="js">
import { computed } from "vue";

const props = defineProps({
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
    return object.title ?? object.name ?? object.label ?? object.id ?? ''
  }
  return object ?? ''
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
            min-width="15%"
            align="center"
        />
        <el-table-column
            prop="description"
            label="描述"
            min-width="55%"
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