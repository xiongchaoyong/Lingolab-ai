import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // ---- state ----
  const sidebarCollapsed = ref(false)
  const isLoading = ref(false)

  // ---- actions ----
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(val) {
    isLoading.value = val
  }

  return {
    sidebarCollapsed,
    isLoading,
    toggleSidebar,
    setLoading,
  }
})
