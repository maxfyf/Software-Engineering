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

const total = computed(() => props.operations.length)
const pageData = computed(() => {
  const start = (props.currentPage - 1) * props.pageSize
  const end = start + props.pageSize
  return props.operations.slice(start, end)
})
// 切换页面
const handleCurrentChange = () => {
  // TODO
}
</script>

<template>
  <el-row>
    <el-col>
      <el-table
          :data="pageData"
          empty-text="暂无操作记录"
          stripe
          class="task-table"
          :row-class-name="todo"
          :key="todo"
      >
        <el-table-column
            prop="object"
            label="操作对象"
            min-width="25%"
            align="left"
        />
        <el-table-column
            prop="operator"
            label="操作人"
            min-width="25%"
            align="center"
        />
        <el-table-column
            prop="description"
            label="描述"
            min-width="50%"
            align="left"
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

</style>