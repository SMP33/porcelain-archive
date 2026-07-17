import { ref, computed } from 'vue'

// Бургер-меню шапки: открытие/закрытие + анимация полосок в крестик
export function useMobileMenu() {
  const isOpen = ref(false)

  function toggle() {
    isOpen.value = !isOpen.value
  }
  function close() {
    isOpen.value = false
  }

  const bar1Style = computed(() =>
    isOpen.value ? { transform: 'translateY(8px) rotate(45deg)' } : {}
  )
  const bar2Style = computed(() => ({ opacity: isOpen.value ? '0' : '1' }))
  const bar3Style = computed(() =>
    isOpen.value ? { transform: 'translateY(-8px) rotate(-45deg)' } : {}
  )

  return { isOpen, toggle, close, bar1Style, bar2Style, bar3Style }
}
