import { ref, computed } from 'vue'

// Drag&drop переупорядочивание страниц документа (admin/pages.html)
export function useDragReorder(itemsRef, keyFn = (item) => item) {
  let originalOrder = itemsRef.value.map(keyFn)
  const dragSrcIndex = ref(null)
  const dragging = ref(false)

  function captureOriginal() {
    originalOrder = itemsRef.value.map(keyFn)
  }

  function onDragStart(index) {
    dragSrcIndex.value = index
    dragging.value = true
  }

  function onDragOver(index) {
    if (dragSrcIndex.value === null || dragSrcIndex.value === index) return
    const items = itemsRef.value
    const [moved] = items.splice(dragSrcIndex.value, 1)
    items.splice(index, 0, moved)
    dragSrcIndex.value = index
  }

  function onDragEnd() {
    dragSrcIndex.value = null
    setTimeout(() => {
      dragging.value = false
    }, 100)
  }

  const orderChanged = computed(() => {
    const current = itemsRef.value.map(keyFn)
    return current.some((v, i) => v !== originalOrder[i])
  })

  return {
    dragSrcIndex,
    dragging,
    onDragStart,
    onDragOver,
    onDragEnd,
    orderChanged,
    captureOriginal,
  }
}
