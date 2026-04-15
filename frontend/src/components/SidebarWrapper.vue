<script setup lang="js">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { minWidth, maxWidthPercent, getContainerWidth, sidebarWidth } from '@/store/layout.js'

const isResizing = ref(false)
let maxWidth = getContainerWidth() * maxWidthPercent

const updateMaxWidth = () => {
  const containerWidth = getContainerWidth()
  maxWidth = containerWidth * maxWidthPercent
  if (sidebarWidth.value > maxWidth) {
    sidebarWidth.value = maxWidth
  }
}

const startResize = (e) => {
  e.preventDefault()
  isResizing.value = true

  const startX = e.clientX
  const startWidth = sidebarWidth.value

  const onMouseMove = (moveEvent) => {
    moveEvent.preventDefault()
    const deltaX = moveEvent.clientX - startX
    let newWidth = startWidth + deltaX

    if (newWidth < minWidth) {
      newWidth = minWidth
    }
    if (newWidth > maxWidth) {
      newWidth = maxWidth
    }

    sidebarWidth.value = newWidth
  }

  const onMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const handleWindowResize = () => {
  updateMaxWidth()
}

onMounted(() => {
  updateMaxWidth()
  window.addEventListener('resize', handleWindowResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize)
})
</script>

<!-- 含可拖动侧边栏的界面 -->
<template>
  <div class="page-with-sidebar">
    <!-- 侧边栏 -->
    <aside
        class="sidebar"
        :style="{ width: sidebarWidth + 'px' }"
        :class="{ 'resizing-active': isResizing }"
    >
      <!-- 侧边栏内容 -->
      <div class="sidebar-content">
        <slot name="sidebar"/>
      </div>

      <!-- 拖拽手柄 -->
      <div
          class="resize-handle"
          @mousedown="startResize"
          :class="{ 'resizing-active': isResizing }"
      />
    </aside>

    <!-- 内容区 -->
    <main class="content">
      <slot/>
    </main>
  </div>
</template>

<style scoped>
.page-with-sidebar {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: row;
}

.sidebar {
  height: 100%;
  background-color: rgba(255,255,255,0.75);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: row;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.resize-handle {
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  cursor: ew-resize;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resize-handle:hover {
  width: 3px;
  background-color: #409eff;
}

.resize-handle:active {
  width: 3px;
  background-color: #409eff;
}

.content {
  flex: 1;
  overflow-x: hidden;
  position: relative;
}
</style>