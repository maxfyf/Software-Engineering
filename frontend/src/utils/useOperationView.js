import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPersonalOperations, getTeamOperations } from '@/store/user.js'

const getObjectId = (operation) => {
  const object = operation?.object
  if (object && typeof object === 'object') {
    return object.taskId ?? object.task_id ?? object.objectId ?? object.object_id ?? object.id ?? null
  }
  if (typeof object === 'number') return object
  return operation?.taskId ?? operation?.task_id ?? operation?.objectId ?? operation?.object_id ?? null
}

const getObjectLabel = (operation) => {
  const object = operation?.object
  if (object && typeof object === 'object') {
    return object.title ?? object.name ?? object.label ?? String(getObjectId(operation) ?? '')
  }
  return object === undefined || object === null ? '' : String(object)
}

const getObjectAux = (operation) => {
  const id = getObjectId(operation)
  const scope = operation?.scope
  const scopeText = scope === undefined || scope === null ? '' : String(scope)
  return id ? `taskId: ${id}` : scopeText
}

export function useOperationView() {
  const route = useRoute()
  const operations = ref([])
  const selectedObject = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(10)

  const teamId = computed(() => route.query.teamId)

  const loadOperations = async () => {
    try {
      if (teamId.value) {
        operations.value = await getTeamOperations(teamId.value)
      } else {
        operations.value = await getPersonalOperations()
      }
      currentPage.value = 1
    } catch (error) {
      operations.value = []
      ElMessage.error('操作记录加载失败')
    }
  }

  const dataset = computed(() => {
    const seen = new Set()
    const result = []
    operations.value.forEach((item) => {
      const id = getObjectId(item)
      const label = getObjectLabel(item)
      if (!label && !id) return

      const key = id ? `id:${id}` : `label:${label}`
      if (seen.has(key)) return
      seen.add(key)
      result.push({
        data: label || String(id),
        aux: id ? `taskId: ${id}` : getObjectAux(item),
        taskId: id,
        object: item.object
      })
    })
    return result
  })

  const filteredOperations = computed(() => {
    if (!selectedObject.value) return operations.value

    const selectedId = selectedObject.value.taskId
    const selectedLabel = selectedObject.value.data
    return operations.value.filter((item) => {
      const itemId = getObjectId(item)
      if (selectedId) return Number(itemId) === Number(selectedId)
      return getObjectLabel(item) === selectedLabel
    })
  })

  const operationTypes = computed(() => {
    return [...new Set(operations.value.map(item => item.type).filter(Boolean))]
  })

  const handleSelectObject = (item) => {
    selectedObject.value = item || null
    currentPage.value = 1
  }

  const handleSearchObject = ({ keyword }) => {
    if (!keyword) {
      selectedObject.value = null
      currentPage.value = 1
    }
  }

  const handlePageChange = (page) => {
    currentPage.value = page
  }

  onMounted(loadOperations)
  watch(() => route.query.teamId, loadOperations)

  return {
    dataset,
    operations: filteredOperations,
    operationTypes,
    currentPage,
    pageSize,
    handleSelectObject,
    handleSearchObject,
    handlePageChange
  }
}