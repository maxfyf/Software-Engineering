import { ref } from 'vue'

export const minWidth = 200    //最小宽度：200px
export const maxWidthPercent = 0.5    //最大宽度占比：50%

export const getContainerWidth = () => {
    const layoutEl = document.querySelector('.sidebar-layout')
    return layoutEl ? layoutEl.clientWidth : window.innerWidth
}

let maxWidth = getContainerWidth() * maxWidthPercent
export const sidebarWidth = ref((3 * minWidth + maxWidth) / 4)