import { ref, computed, onMounted, onUnmounted } from 'vue'

// Лайтбокс страниц документа: zoom/pan/swipe/клавиатура/prefetch соседних страниц
const LB_MIN_SCALE = 1
const LB_MAX_SCALE = 5

export function useLightbox(pagesRef) {
  const isOpen = ref(false)
  const currentIndex = ref(0)
  const scale = ref(1)
  const panX = ref(0)
  const panY = ref(0)
  const loading = ref(false)
  const imgEl = ref(null)

  let isPanning = false
  let panStartX = 0
  let panStartY = 0
  let panOriginX = 0
  let panOriginY = 0
  let pinchStartDist = 0
  let pinchStartScale = 1
  let swipeStartX = null

  const pages = computed(() => pagesRef.value || [])
  const total = computed(() => pages.value.length)
  const current = computed(() => pages.value[currentIndex.value] || null)

  const transformStyle = computed(() => ({
    transform: `translate(${panX.value}px, ${panY.value}px) scale(${scale.value})`,
    cursor: scale.value > 1 ? 'grab' : 'default',
  }))
  const zoomPercent = computed(() => Math.round(scale.value * 100))
  const canZoomIn = computed(() => scale.value < LB_MAX_SCALE)
  const canZoomOut = computed(() => scale.value > LB_MIN_SCALE)
  const canPrev = computed(() => currentIndex.value > 0)
  const canNext = computed(() => currentIndex.value < total.value - 1)

  function preload(i) {
    if (i >= 0 && i < total.value) {
      const im = new Image()
      im.src = pages.value[i].image_url
    }
  }

  function resetZoom() {
    scale.value = 1
    panX.value = 0
    panY.value = 0
  }

  // Не даёт растянутому изображению уйти за пределы видимой области
  function clampPan() {
    const img = imgEl.value
    if (!img) return
    const maxX = (img.clientWidth * (scale.value - 1)) / 2
    const maxY = (img.clientHeight * (scale.value - 1)) / 2
    panX.value = Math.max(-maxX, Math.min(maxX, panX.value))
    panY.value = Math.max(-maxY, Math.min(maxY, panY.value))
  }

  function zoomBy(delta) {
    scale.value = Math.min(LB_MAX_SCALE, Math.max(LB_MIN_SCALE, scale.value + delta))
    if (scale.value === 1) {
      panX.value = 0
      panY.value = 0
    }
    clampPan()
  }

  function open(pageNumber) {
    const idx = pages.value.findIndex((p) => p.page_number === pageNumber)
    currentIndex.value = idx >= 0 ? idx : 0
    resetZoom()
    isOpen.value = true
    loading.value = true
    preload(currentIndex.value - 1)
    preload(currentIndex.value + 1)
    document.body.style.overflow = 'hidden'
  }

  function close() {
    isOpen.value = false
    document.body.style.overflow = ''
    resetZoom()
  }

  function shiftPage(delta) {
    const next = currentIndex.value + delta
    if (next >= 0 && next < total.value) {
      currentIndex.value = next
      resetZoom()
      loading.value = true
      preload(next - 1)
      preload(next + 1)
    }
  }

  function onImageLoad() {
    loading.value = false
  }

  function onWheel(e) {
    e.preventDefault()
    zoomBy(e.deltaY < 0 ? 0.2 : -0.2)
  }

  function onDblclick() {
    if (scale.value !== 1) {
      resetZoom()
    } else {
      scale.value = 2.5
      clampPan()
    }
  }

  function onMousedown(e) {
    if (scale.value <= 1) return
    isPanning = true
    panStartX = e.clientX
    panStartY = e.clientY
    panOriginX = panX.value
    panOriginY = panY.value
    e.preventDefault()
  }

  function onMousemove(e) {
    if (!isPanning) return
    panX.value = panOriginX + (e.clientX - panStartX)
    panY.value = panOriginY + (e.clientY - panStartY)
    clampPan()
  }

  function onMouseup() {
    isPanning = false
  }

  function touchDist(t) {
    return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY)
  }

  function onTouchstart(e) {
    if (e.touches.length === 2) {
      pinchStartDist = touchDist(e.touches)
      pinchStartScale = scale.value
      swipeStartX = null
    } else if (e.touches.length === 1) {
      if (scale.value > 1) {
        isPanning = true
        panStartX = e.touches[0].clientX
        panStartY = e.touches[0].clientY
        panOriginX = panX.value
        panOriginY = panY.value
      } else {
        swipeStartX = e.touches[0].clientX
      }
    }
  }

  function onTouchmove(e) {
    if (e.touches.length === 2 && pinchStartDist > 0) {
      e.preventDefault()
      const ratio = touchDist(e.touches) / pinchStartDist
      scale.value = Math.min(LB_MAX_SCALE, Math.max(LB_MIN_SCALE, pinchStartScale * ratio))
      if (scale.value === 1) {
        panX.value = 0
        panY.value = 0
      }
      clampPan()
    } else if (e.touches.length === 1 && isPanning) {
      e.preventDefault()
      panX.value = panOriginX + (e.touches[0].clientX - panStartX)
      panY.value = panOriginY + (e.touches[0].clientY - panStartY)
      clampPan()
    }
  }

  function onTouchend(e) {
    if (e.touches.length < 2) pinchStartDist = 0
    if (e.touches.length === 0) {
      if (isPanning) {
        isPanning = false
      } else if (scale.value === 1 && swipeStartX !== null && e.changedTouches.length) {
        const dx = e.changedTouches[0].clientX - swipeStartX
        if (Math.abs(dx) > 50) shiftPage(dx < 0 ? 1 : -1)
      }
      swipeStartX = null
    }
  }

  function onKeydown(e) {
    if (!isOpen.value) return
    if (e.key === 'Escape') close()
    if (e.key === 'ArrowLeft') shiftPage(-1)
    if (e.key === 'ArrowRight') shiftPage(1)
    if (e.key === '+' || e.key === '=') zoomBy(0.5)
    if (e.key === '-') zoomBy(-0.5)
  }

  onMounted(() => {
    document.addEventListener('keydown', onKeydown)
    document.addEventListener('mousemove', onMousemove)
    document.addEventListener('mouseup', onMouseup)
  })
  onUnmounted(() => {
    document.removeEventListener('keydown', onKeydown)
    document.removeEventListener('mousemove', onMousemove)
    document.removeEventListener('mouseup', onMouseup)
    document.body.style.overflow = ''
  })

  return {
    isOpen,
    current,
    currentIndex,
    total,
    loading,
    imgEl,
    transformStyle,
    zoomPercent,
    canZoomIn,
    canZoomOut,
    canPrev,
    canNext,
    open,
    close,
    shiftPage,
    zoomBy,
    resetZoom,
    onImageLoad,
    onWheel,
    onDblclick,
    onMousedown,
    onTouchstart,
    onTouchmove,
    onTouchend,
  }
}
