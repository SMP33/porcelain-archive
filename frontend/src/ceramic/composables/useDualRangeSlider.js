import { ref, computed, unref } from 'vue'

// Двойной range-слайдер для фильтра по годам (search.html)
export function useDualRangeSlider(min, max, initialFrom, initialTo) {
  const valueFrom = ref(unref(initialFrom))
  const valueTo = ref(unref(initialTo))

  function onFromInput() {
    if (valueFrom.value > valueTo.value) valueFrom.value = valueTo.value
  }
  function onToInput() {
    if (valueTo.value < valueFrom.value) valueTo.value = valueFrom.value
  }

  const trackStyle = computed(() => {
    const minV = unref(min)
    const maxV = unref(max)
    const span = maxV - minV || 1
    const pf = ((valueFrom.value - minV) / span) * 100
    const pt = ((valueTo.value - minV) / span) * 100
    return { left: pf + '%', width: pt - pf + '%' }
  })

  function reset(from, to) {
    valueFrom.value = from
    valueTo.value = to
  }

  return { valueFrom, valueTo, onFromInput, onToInput, trackStyle, reset }
}
