import { ref, onMounted, onUnmounted } from 'vue'

// Анимации лендинга (home.html): scroll-lock героя, лента истории (shimmer + draw-on-click),
// вращение блюдца при скролле, IntersectionObserver экрана "проблема", карусель на wheel/стрелках
export function useHomeAnimations() {
  const heroRef = ref(null)
  const interactiveRef = ref(null)
  const historySectionRef = ref(null)
  const ribbonPathRef = ref(null)
  const ribbonGradRef = ref(null)
  const resultsSectionRef = ref(null)
  const saucerRef = ref(null)
  const problemSectionRef = ref(null)
  const carouselSectionRef = ref(null)
  const trackRef = ref(null)

  const problemAnimated = ref(false)
  const carStep = ref(0)

  let rafShimmer = null
  let intersectionObserver = null
  let hovering = false
  let ribbonDrawn = false
  let ribbonTimer = null

  function updateOverflow() {
    const onHero = window.scrollY < 10
    document.documentElement.style.overflow = onHero && !hovering ? 'hidden' : ''
  }
  function onInteractiveEnter() {
    hovering = true
    updateOverflow()
  }
  function onInteractiveLeave() {
    hovering = false
    updateOverflow()
  }

  function easeInOut(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
  }

  function tickShimmer(t0) {
    function tick(now) {
      const phase = ((now - t0) % 16000) / 16000
      const tri = phase < 0.5 ? phase * 2 : 2 - phase * 2
      const offset = easeInOut(tri) * -1440
      if (ribbonGradRef.value) {
        ribbonGradRef.value.setAttribute('gradientTransform', `translate(${offset} 0)`)
      }
      rafShimmer = requestAnimationFrame(tick)
    }
    rafShimmer = requestAnimationFrame(tick)
  }

  function drawRibbonOnce() {
    if (ribbonDrawn || !ribbonPathRef.value) return
    ribbonDrawn = true
    const path = ribbonPathRef.value
    path.style.transition = 'stroke-dashoffset 2.4s cubic-bezier(0.4, 0, 0.2, 1)'
    path.style.strokeDashoffset = '0'
  }

  function updateSaucer() {
    if (!saucerRef.value || !resultsSectionRef.value) return
    const SAUCER_R = 224 // радиус, px (диаметр 448)
    const sectionTop = resultsSectionRef.value.offsetTop
    const vh = window.innerHeight
    const progress = Math.max(0, Math.min(1, (window.scrollY - sectionTop) / vh))
    const travel = progress * (vh + 448) // полностью уходит под экран
    const deg = (travel / SAUCER_R) * (180 / Math.PI)
    saucerRef.value.style.transform = `translateY(${travel}px) rotate(${deg}deg)`
  }

  function colWidth() {
    const item = trackRef.value?.querySelector('.carousel-item')
    return item ? item.offsetWidth + 20 : 500
  }
  function carMaxStep() {
    if (!carouselSectionRef.value) return 0
    return Math.max(0, 7 - Math.floor(carouselSectionRef.value.offsetWidth / colWidth()))
  }
  function moveCar(delta) {
    carStep.value = Math.max(0, Math.min(carMaxStep(), carStep.value + delta))
    if (trackRef.value) {
      trackRef.value.style.transform = `translateX(-${carStep.value * colWidth()}px)`
    }
  }
  function onCarouselWheel(e) {
    const atStart = carStep.value === 0 && e.deltaY < 0
    const atEnd = carStep.value >= carMaxStep() && e.deltaY > 0
    if (atStart || atEnd) return
    e.preventDefault()
    moveCar(e.deltaY > 0 ? 1 : -1)
  }

  function smoothScrollTo(y, duration) {
    const html = document.documentElement
    html.style.scrollSnapType = 'none'
    const start = window.scrollY
    const diff = y - start
    let startTime = null
    function ease(t) {
      return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
    }
    function step(ts) {
      if (!startTime) startTime = ts
      const t = Math.min((ts - startTime) / duration, 1)
      window.scrollTo(0, start + diff * ease(t))
      if (t < 1) requestAnimationFrame(step)
      else html.style.scrollSnapType = ''
    }
    requestAnimationFrame(step)
  }

  function scrollToId(id) {
    const target = document.getElementById(id)
    if (target) {
      smoothScrollTo(target.getBoundingClientRect().top + window.scrollY, 1400)
    }
  }

  onMounted(() => {
    if (heroRef.value) {
      const header = document.querySelector('header')
      if (header) {
        heroRef.value.style.height = window.innerHeight - header.offsetHeight + 'px'
      }
    }

    window.addEventListener('scroll', updateOverflow)
    updateOverflow()

    if (ribbonPathRef.value) {
      const len = ribbonPathRef.value.getTotalLength()
      ribbonPathRef.value.style.strokeDasharray = String(len)
      ribbonPathRef.value.style.strokeDashoffset = String(len)
    }
    // Лента рисуется по клику, но и сама проявляется через 10с после открытия.
    ribbonTimer = setTimeout(drawRibbonOnce, 10000)
    tickShimmer(performance.now())

    window.addEventListener('scroll', updateSaucer, { passive: true })
    updateSaucer()

    if (problemSectionRef.value) {
      intersectionObserver = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && entries[0].intersectionRatio >= 0.5) {
            problemAnimated.value = true
          }
        },
        { threshold: 0.5 }
      )
      intersectionObserver.observe(problemSectionRef.value)
    }

    // Скролл-снап секций включён только пока смонтирован лендинг
    document.documentElement.style.scrollSnapType = 'y mandatory'
  })

  onUnmounted(() => {
    window.removeEventListener('scroll', updateOverflow)
    window.removeEventListener('scroll', updateSaucer)
    if (rafShimmer) cancelAnimationFrame(rafShimmer)
    if (ribbonTimer) clearTimeout(ribbonTimer)
    if (intersectionObserver) intersectionObserver.disconnect()
    document.documentElement.style.overflow = ''
    document.documentElement.style.scrollSnapType = ''
  })

  return {
    heroRef,
    interactiveRef,
    historySectionRef,
    ribbonPathRef,
    ribbonGradRef,
    resultsSectionRef,
    saucerRef,
    problemSectionRef,
    carouselSectionRef,
    trackRef,
    problemAnimated,
    onInteractiveEnter,
    onInteractiveLeave,
    drawRibbonOnce,
    onCarouselWheel,
    moveCar,
    scrollToId,
  }
}
