<script setup>
import { ref, onMounted } from 'vue'
import http from '../api/http'
import { useHomeAnimations } from '../composables/useHomeAnimations'
import teapotIcon from '../assets/img/teapot-icon.png'
import cupSaucer from '../assets/img/cup-saucer.png'

const stats = ref({ factory_count: 0, doc_count: 0, page_count: 0 })

async function loadStats() {
  try {
    const { data } = await http.get('/api/ceramic/site/stats')
    stats.value = data
  } catch (error) {
    // Значения по умолчанию остаются нулевыми
  }
}
onMounted(loadStats)

const {
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
} = useHomeAnimations()

const searchSteps = [
  ['01', 'Выберите завод', 'Перейдите в раздел «Объекты» — там список всех заводов с описаниями, датами и географией.'],
  ['02', 'Найдите документ', 'Воспользуйтесь поиском по материалам: по типу документа, дате или ключевому слову.'],
  ['03', 'Запросите копию', 'Высококачественные сканы предоставляются по запросу для некоммерческого использования.'],
]

const teamMembers = [
  ['Имя Фамилия', 'Куратор'],
  ['Имя Фамилия', 'Куратор'],
  ['Имя Фамилия', 'Куратор'],
  ['Имя Фамилия', 'ИТ-разработчик'],
  ['Имя Фамилия', 'Искусствовед'],
  ['Имя Фамилия', 'Архитектор-реставратор'],
  ['Имя Фамилия', 'Урбанист'],
  ['Имя Фамилия', 'Урбанист'],
  ['Имя Фамилия', 'Урбанист'],
]
</script>

<template>
  <div>

    <!-- ===== ЭКРАН 1: ГЕРОЙ ===== -->
    <div id="home-hero" ref="heroRef" class="tw:relative tw:overflow-hidden tw:text-white tw:flex tw:flex-col" style="background-color: #6b1a1a;">
      <div ref="interactiveRef" class="tp-interactive tw:relative tw:z-10 tw:flex-1 tw:flex tw:items-center tw:justify-center tw:select-none"
           @mouseenter="onInteractiveEnter" @mouseleave="onInteractiveLeave">

        <div class="tp-left">
          <h3 class="tw:font-serif tw:text-base tw:font-bold tw:mb-3 tw:text-white">Что в архиве</h3>
          <p class="tw:text-sm tw:text-white/70 tw:leading-relaxed">
            Оцифрованные документы российских керамических и фарфоровых заводов —
            технические условия, приказы, патенты, переписка и каталоги изделий,
            спасённые от уничтожения с закрывшихся предприятий.
          </p>
        </div>

        <div class="tp-right">
          <h3 class="tw:font-serif tw:text-base tw:font-bold tw:mb-3 tw:text-white">Для чего</h3>
          <p class="tw:text-sm tw:text-white/70 tw:leading-relaxed">
            Сохранить документальное наследие фарфоровой промышленности и дать ему вторую жизнь, сделав
            его доступным для исследователей, историков и всех, кому важна
            эта страница отечественной истории.
          </p>
        </div>

        <a href="#home-history" class="tp-arrow" @click.prevent="scrollToId('home-history')">
          <svg width="18" height="100" viewBox="0 0 18 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="9" y1="0" x2="9" y2="88" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
            <polyline points="1,78 9,90 17,78" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </a>

        <div class="tp-glow"></div>
        <div class="tp-eyes" style="left: calc(50% + 4rem); top: calc(50% - 7rem);">👀</div>
        <div class="tp-icon">
          <img :src="teapotIcon" alt="Чайник" class="tw:w-36 tw:h-36 tw:md:w-48 tw:md:h-48 tw:object-contain">
        </div>
      </div>
    </div>

    <!-- ===== ЭКРАН 2: ИСТОРИЯ ===== -->
    <section id="home-history" ref="historySectionRef" class="tw:min-h-screen tw:flex tw:flex-col" style="background-color: #fdf6ed;" @click="drawRibbonOnce">

      <svg id="history-ribbon" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="ribbon-gold" ref="ribbonGradRef" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="2880" y2="0">
            <stop offset="0%"    stop-color="#5c3d00"/>
            <stop offset="5%"    stop-color="#b8820a"/>
            <stop offset="11%"   stop-color="#e8c040"/>
            <stop offset="17.5%" stop-color="#fff5a0"/>
            <stop offset="23%"   stop-color="#d4a020"/>
            <stop offset="27.5%" stop-color="#f0c838"/>
            <stop offset="33%"   stop-color="#fffacc"/>
            <stop offset="38.5%" stop-color="#c89018"/>
            <stop offset="43.5%" stop-color="#e8c040"/>
            <stop offset="50%"   stop-color="#7a5200"/>
            <stop offset="50%"   stop-color="#5c3d00"/>
            <stop offset="55%"   stop-color="#b8820a"/>
            <stop offset="61%"   stop-color="#e8c040"/>
            <stop offset="67.5%" stop-color="#fff5a0"/>
            <stop offset="73%"   stop-color="#d4a020"/>
            <stop offset="77.5%" stop-color="#f0c838"/>
            <stop offset="83%"   stop-color="#fffacc"/>
            <stop offset="88.5%" stop-color="#c89018"/>
            <stop offset="93.5%" stop-color="#e8c040"/>
            <stop offset="100%"  stop-color="#7a5200"/>
          </linearGradient>
        </defs>
        <path id="history-ribbon-path" ref="ribbonPathRef"
              d="M -40,900 C 100,550 280,120 490,220 C 590,310 610,340 650,310 C 720,270 780,110 880,160 C 1020,220 1220,480 1490,640"/>
      </svg>

      <div class="tw:flex-1 tw:max-w-5xl tw:mx-auto tw:px-10 tw:pt-24 tw:pb-16 tw:w-full tw:flex tw:flex-col tw:justify-center">

        <div class="tw:relative">
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:absolute tw:-top-6" style="color: #b8820a;">История</p>
          <h2 class="tw:font-serif tw:text-4xl tw:font-bold tw:mb-12 tw:leading-tight" style="color: #2c1a00;">
            Советский фарфор:<br>взлёт и забвение
          </h2>
        </div>

        <div class="tw:grid tw:grid-cols-2 tw:gap-16">
          <div class="tw:space-y-5 tw:text-base tw:leading-relaxed tw:text-ink-900">
            <p>
              В середине XX века Советский Союз обладал одной из крупнейших
              фарфоровых промышленностей в мира. Десятки заводов от Ленинграда
              до Владивостока выпускали изделия, экспортировавшиеся на пять континентов.
            </p>
            <p>
              Государственные предприятия сочетали промышленный масштаб с высоким
              художественным уровнем. Краснодарская «Чайка», открытая в 1960-м,
              стала одним из крупнейших производителей керамической посуды в стране —
              её сервизы до сих пор хранят как семейные реликвии.
            </p>
            <p>
              Каждый завод нёс свою эстетику — ЛФЗ с его строгой элегантностью,
              Дулёво с народными мотивами, Вербилки с традицией, восходящей
              к XVIII веку.
            </p>
          </div>
          <div class="tw:space-y-5 tw:text-base tw:leading-relaxed tw:text-ink-900">
            <p>
              После распада СССР большинство заводов оказались в условиях,
              к которым не были готовы. Государственные субсидии исчезли,
              рынки сбыта рухнули, производственные цепочки разорвались.
            </p>
            <p>
              Одни предприятия были проданы или перепрофилированы. Другие
              просто закрыли двери — тихо, без объявлений, оставив за собой
              цеха, оборудование и горы документов, судьба которых никого
              не интересовала. «Чайка» закрылась после 60 лет работы,
              но место и архивы остались.
            </p>
            <p>
              Производственная культура, складывавшаяся десятилетиями, начала
              исчезать вместе с людьми, которые её несли.
            </p>
          </div>
        </div>

      </div>
    </section>

    <!-- ===== ЭКРАН 3: ПРОБЛЕМА ===== -->
    <section id="home-problem" ref="problemSectionRef" :class="{ animated: problemAnimated }"
             class="tw:min-h-screen tw:relative tw:flex tw:items-center tw:justify-center tw:overflow-hidden" style="background-color: #0f172a;">

      <div class="prob-obj prob-obj-left">
        <img :src="cupSaucer" alt="" class="tw:object-contain tw:drop-shadow-2xl" style="width: min(340px, 32vw); max-height: 55vh;">
      </div>

      <div class="prob-obj prob-obj-right">
        <img :src="cupSaucer" alt="" class="tw:object-contain tw:drop-shadow-2xl" style="width: min(340px, 32vw); max-height: 55vh; transform: scaleX(-1);">
      </div>

      <div class="prob-text">
        <p class="tw:font-serif tw:font-bold tw:text-white tw:leading-snug tw:mb-6" style="font-size: clamp(1.6rem, 3vw, 2.4rem);">
          <span class="prob-blink-1">Заводы</span> <span class="prob-italic">закрываются</span>.<br>
          <span class="prob-blink-2">Документы</span> <span class="prob-italic">теряются</span>.<br>
          <span class="prob-blink-3">История</span> <span class="prob-italic">уходит</span>.
        </p>
        <p class="tw:text-white/45 tw:text-sm tw:leading-relaxed tw:mx-auto" style="max-width: 26rem;">
          С 1991 года прекратили работу более 200 фарфоровых
          и керамических предприятий России. Вместе с ними исчезают
          уникальные архивы — свидетели промышленной и культурной эпохи.
        </p>
      </div>

      <a href="#home-work" class="prob-arrow" @click.prevent="scrollToId('home-work')">
        <svg width="18" height="100" viewBox="0 0 18 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="9" y1="0" x2="9" y2="88" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          <polyline points="1,78 9,90 17,78" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>

    </section>

    <!-- ===== ЭКРАН 4: ПРОДЕЛАННАЯ РАБОТА ===== -->
    <section id="home-work" class="tw:min-h-screen tw:bg-white tw:flex tw:flex-col">
      <div class="tw:flex-1 tw:max-w-5xl tw:mx-auto tw:px-10 tw:pt-20 tw:pb-16 tw:w-full tw:flex tw:flex-col">

        <div class="tw:relative">
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:absolute tw:-top-6 tw:text-gray-400">Проделанная работа</p>
          <h2 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-12">
            Серия экспедиций на фарфорные заводы
          </h2>
        </div>

        <div class="tw:grid tw:gap-16 tw:flex-1" style="grid-template-columns: 2fr 3.9fr;">

          <div class="tw:flex tw:flex-col">
            <div class="tw:space-y-8 tw:mb-6">
              <div>
                <div class="tw:text-5xl tw:font-bold tw:font-serif tw:text-ink-900 tw:mb-1">{{ stats.doc_count }}+</div>
                <div class="tw:text-sm tw:text-gray-400">оцифрованных документов</div>
              </div>
              <div>
                <div class="tw:text-5xl tw:font-bold tw:font-serif tw:text-ink-900 tw:mb-1">{{ stats.page_count }}+</div>
                <div class="tw:text-sm tw:text-gray-400">страниц архивных материалов</div>
              </div>
            </div>
            <p class="tw:text-base tw:text-ink-900 tw:leading-relaxed tw:mt-2 tw:max-w-[360px]">
              Экспедиции проходят непосредственно в хранилища предприятий, где собраны
              десятки килограммов бумажных свидетельств хода производственного
              процесса: детали поставок, объёмы производств, переписки, распоряжения
              и другое.
            </p>
            <p class="tw:text-base tw:text-ink-900 tw:leading-relaxed tw:mt-4 tw:max-w-[360px]">
              Каждый документ из архива сканируется и описывается вручную
              волонтёрами проекта под руководством кураторов и искусствоведов.
            </p>
          </div>

          <div class="work-grid tw:grid tw:gap-2 tw:self-start tw:relative" style="grid-template-columns: calc(3*(100% - 8px)/7) 1fr calc(3*(100% - 8px)/7);">
            <div class="photo-placeholder tw:rounded-xl tw:bg-gray-100 tw:flex tw:items-center tw:justify-center" style="grid-column:1; grid-row:1/3;">
              <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">фото</span>
            </div>
            <div class="photo-placeholder tw:rounded-xl tw:bg-gray-100 tw:aspect-[4/3] tw:flex tw:items-center tw:justify-center" style="grid-column:2/4; grid-row:1;">
              <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">фото</span>
            </div>
            <div style="grid-column:2; grid-row:2; aspect-ratio:1/1;"></div>
            <div class="photo-placeholder tw:rounded-xl tw:bg-gray-100 tw:flex tw:items-center tw:justify-center" style="grid-column:3; grid-row:2/4;">
              <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">фото</span>
            </div>
            <div class="photo-placeholder tw:rounded-xl tw:bg-gray-100 tw:aspect-[4/3] tw:flex tw:items-center tw:justify-center" style="grid-column:1/3; grid-row:3;">
              <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">фото</span>
            </div>
            <div class="work-camera"><span class="cam-normal">📷</span><span class="cam-flash">📸</span></div>
          </div>

        </div>
      </div>
    </section>

    <!-- ===== ЭКРАН 5: КАРУСЕЛЬ ===== -->
    <section id="home-carousel" ref="carouselSectionRef" class="tw:min-h-screen tw:flex tw:flex-col tw:justify-center tw:gap-8"
             style="background-color: #111111;" @wheel="onCarouselWheel">

      <div class="tw:px-16 tw:flex tw:items-end tw:justify-between">
        <div>
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:mb-2 tw:text-white/30">Рабочий процесс</p>
          <h2 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-white">Из экспедиций</h2>
        </div>
        <div class="tw:flex tw:gap-3">
          <button class="tw:opacity-40 tw:hover:opacity-100 tw:transition-opacity" @click="moveCar(-1)">
            <svg width="100" height="18" viewBox="0 0 100 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="100" y1="9" x2="12" y2="9" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              <polyline points="22,1 10,9 22,17" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="tw:opacity-40 tw:hover:opacity-100 tw:transition-opacity" @click="moveCar(1)">
            <svg width="100" height="18" viewBox="0 0 100 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="0" y1="9" x2="88" y2="9" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              <polyline points="78,1 90,9 78,17" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="tw:overflow-hidden">
        <div class="carousel-track" ref="trackRef">
          <div v-for="i in 14" :key="i" class="carousel-item">фото {{ i }}</div>
        </div>
      </div>

    </section>

    <!-- ===== ЭКРАН 6: РЕЗУЛЬТАТЫ И ПОИСК ===== -->
    <section id="home-results" ref="resultsSectionRef" class="tw:min-h-screen tw:bg-white tw:flex tw:flex-col">
      <div id="results-saucer" ref="saucerRef"></div>
      <div class="tw:flex-1 tw:max-w-5xl tw:mx-auto tw:px-10 tw:pt-20 tw:pb-16 tw:w-full tw:flex tw:flex-col">

        <div class="tw:relative">
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:absolute tw:-top-6 tw:text-gray-400">Архив открыт</p>
          <h2 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-12">Как искать материалы?</h2>
        </div>

        <div class="tw:grid tw:grid-cols-2 tw:gap-16">

          <div class="tw:flex tw:flex-col">
            <div class="tw:space-y-10 tw:mb-10">
              <div v-for="step in searchSteps" :key="step[0]" class="tw:flex tw:gap-5">
                <span class="tw:text-2xl tw:font-bold tw:font-serif tw:shrink-0 tw:w-10 tw:pt-0.5" style="color: #6b1a1a;">{{ step[0] }}</span>
                <div>
                  <h4 class="tw:text-sm tw:font-semibold tw:text-ink-900 tw:mb-1">{{ step[1] }}</h4>
                  <p class="tw:text-sm tw:text-gray-500 tw:leading-relaxed">{{ step[2] }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="tw:flex tw:flex-col tw:space-y-10">
            <router-link to="/ceramic/objects"
               class="tw:block tw:border tw:border-gray-200 tw:rounded-lg tw:px-4 tw:py-3 tw:w-2/3 tw:hover:border-gray-300 tw:transition-colors tw:group">
              <div class="tw:text-sm tw:font-semibold tw:text-ink-900 tw:mb-0.5 tw:group-hover:text-clay-500 tw:transition-colors">
                Каталог объектов →
              </div>
              <p class="tw:text-xs tw:text-gray-400">{{ stats.factory_count }} заводов и предприятий</p>
            </router-link>
            <router-link to="/ceramic/search"
               class="tw:block tw:border tw:border-gray-200 tw:rounded-lg tw:px-4 tw:py-3 tw:w-2/3 tw:hover:border-gray-300 tw:transition-colors tw:group">
              <div class="tw:text-sm tw:font-semibold tw:text-ink-900 tw:mb-0.5 tw:group-hover:text-clay-500 tw:transition-colors">
                Поиск по материалам →
              </div>
              <p class="tw:text-xs tw:text-gray-400">{{ stats.doc_count }} документов в базе</p>
            </router-link>
            <router-link to="/ceramic/feedback"
               class="tw:block tw:border tw:border-gray-200 tw:rounded-lg tw:px-4 tw:py-3 tw:w-2/3 tw:hover:border-gray-300 tw:transition-colors tw:group">
              <div class="tw:text-sm tw:font-semibold tw:text-ink-900 tw:mb-0.5 tw:group-hover:text-clay-500 tw:transition-colors">
                Связаться с нами →
              </div>
              <p class="tw:text-xs tw:text-gray-400">Помочь улучшить архив</p>
            </router-link>
          </div>

        </div>

        <div class="tw:pr-40 tw:mt-10 tw:space-y-4">
          <p class="tw:text-base tw:text-ink-900 tw:leading-relaxed">
            Мы оцифровали и описали архив завода, разработали концепцию редевелопмента территории и создали информационное сопровождение проекта.
          </p>
          <p class="tw:text-base tw:text-ink-900 tw:leading-relaxed">
            Нашей задачей было не только сохранить память о легендарном производстве и предоставить исследователям ранее закрытый массив документации за десятки лет работы, но и вдохновить тысячи людей историей «Чайки», превратив её в современное общественное пространство.
          </p>
        </div>

      </div>
    </section>

    <!-- ===== ЭКРАН 7: КОМАНДА ===== -->
    <section id="home-team" class="tw:min-h-screen tw:flex tw:flex-col" style="background-color: #1a3d2b;">
      <div class="tw:flex-1 tw:max-w-5xl tw:mx-auto tw:px-10 tw:pt-20 tw:pb-4 tw:w-full tw:flex tw:flex-col">

        <div class="tw:relative">
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:absolute tw:-top-6" style="color: rgba(255,255,255,0.4);">Активисты</p>
          <h2 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-white tw:mb-8 tw:pb-4" style="border-bottom: 1px solid rgba(255,255,255,0.15);">
            Команда проекта
          </h2>
        </div>

        <div class="tw:grid tw:grid-cols-3 tw:gap-5">
          <div v-for="(member, i) in teamMembers" :key="i" class="tw:flex tw:flex-col tw:gap-3">
            <div class="tw:w-16 tw:h-16 tw:rounded-full tw:flex tw:items-center tw:justify-center" style="background: rgba(255,255,255,0.1);">
              <svg class="tw:w-8 tw:h-8" fill="rgba(255,255,255,0.3)" viewBox="0 0 24 24">
                <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
              </svg>
            </div>
            <div>
              <div class="tw:font-semibold tw:text-sm tw:text-white">{{ member[0] }}</div>
              <div class="tw:text-xs tw:font-medium tw:mt-0.5" style="color: #7ecba1;">{{ member[1] }}</div>
            </div>
          </div>
        </div>

        <div class="tw:mt-6 tw:pt-4" style="border-top: 1px solid rgba(255,255,255,0.1);">
          <p class="tw:text-xs tw:font-semibold tw:tracking-widest tw:uppercase tw:mb-3" style="color: rgba(255,255,255,0.4);">Волонтёры оцифровки</p>
          <p class="tw:text-sm tw:leading-relaxed" style="color: rgba(255,255,255,0.45);">
            Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия,
            Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия,
            Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия, Имя Фамилия
          </p>
        </div>

      </div>
    </section>

  </div>
</template>

<style scoped>
/* ============================
   SCROLL SNAP
   ============================ */
#home-hero     { height: calc(100vh - 64px); scroll-snap-align: end; }
#home-history,
#home-problem,
#home-work,
#home-carousel,
#home-results,
#home-team     { scroll-snap-align: start; min-height: 100vh; }

/* ============================
   TEAPOT (Screen 1)
   ============================ */
.tp-interactive { cursor: default; }
.tp-icon {
  transform-origin: center center;
  transition: transform 1.4s cubic-bezier(0.22, 1, 0.36, 1);
  position: relative; z-index: 10;
}
.tp-interactive:hover .tp-icon { transform: scale(3); }

.tp-glow {
  position: absolute; width: 280px; height: 280px; border-radius: 50%;
  background: radial-gradient(circle,
    rgba(210,50,50,0.80) 0%, rgba(180,30,30,0.45) 28%,
    rgba(140,20,20,0.18) 55%, transparent 72%);
  opacity: 0; transform: scale(0.5);
  transition: opacity 1.4s ease, transform 1.4s ease;
  pointer-events: none; z-index: 1;
}
.tp-interactive:hover .tp-glow { opacity: 1; transform: scale(4); }

.tp-left, .tp-right {
  opacity: 0; transition: opacity 0.5s ease 0.5s;
  pointer-events: none; position: absolute; top: 50%;
  transform: translateY(-50%); width: 22%; z-index: 20;
}
.tp-left  { left: 5%; }
.tp-right { right: 5%; }
.tp-interactive:hover .tp-left,
.tp-interactive:hover .tp-right { opacity: 1; pointer-events: auto; }

@keyframes camera-rock {
  0%, 80%, 100% { transform: translate(-50%,-50%) rotate(0deg); }
  83%           { transform: translate(-50%,-50%) rotate(-10deg); }
  86%           { transform: translate(-50%,-50%) rotate(10deg); }
  89%           { transform: translate(-50%,-50%) rotate(-10deg); }
  92%           { transform: translate(-50%,-50%) rotate(10deg); }
  96%           { transform: translate(-50%,-50%) rotate(0deg); }
}
.work-camera {
  position: absolute; top: 50%; left: 50%;
  font-size: 1.6rem; line-height: 1; display: inline-block;
  animation: camera-rock 4s infinite;
  pointer-events: auto; z-index: 2; cursor: default;
}
.photo-placeholder { opacity: 0; transition: opacity 1.2s ease; }
.work-grid:has(.work-camera:hover) .photo-placeholder { opacity: 1; }
.cam-flash { display: none; }
.work-camera:hover { animation: none; transform: translate(-50%,-50%) rotate(0deg); }
.work-camera:hover .cam-normal { display: none; }
.work-camera:hover .cam-flash { display: inline; }

@keyframes tp-blink {
  0%, 80%, 100% { transform: scaleY(1); }
  83%           { transform: scaleY(0.08); }
  86%           { transform: scaleY(1); }
  89%           { transform: scaleY(0.08); }
  92%           { transform: scaleY(1); }
}
.tp-eyes {
  position: absolute; font-size: 1.6rem; line-height: 1;
  display: inline-block; animation: tp-blink 5s infinite;
  transform-origin: center 60%; opacity: 1;
  transition: opacity 0.3s ease; pointer-events: none; z-index: 15;
}
.tp-interactive:hover .tp-eyes { opacity: 0; }

.tp-arrow {
  position: absolute; bottom: 2.5rem; left: 50%;
  transform: translateX(-50%); opacity: 0;
  transition: opacity 0.25s ease; pointer-events: none; z-index: 20;
  cursor: pointer;
}
.tp-interactive:hover .tp-arrow { opacity: 1; pointer-events: auto; }

/* ============================
   PROBLEM (Screen 3) — animation
   ============================ */
.prob-obj {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  transition: transform 1.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.prob-obj-right { transition-delay: 0.1s; }

#home-problem.animated .prob-obj-left  {
  transform: translate(calc(-50% - 32vw), -50%);
}
#home-problem.animated .prob-obj-right {
  transform: translate(calc(-50% + 32vw), -50%);
}

.prob-text {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0; transition: opacity 0.9s ease 1.2s;
  text-align: center; width: 38vw; z-index: 10;
  pointer-events: none;
}
#home-problem.animated .prob-text { opacity: 1; }

.prob-italic {
  font-style: italic;
}
@keyframes prob-blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}
#home-problem.animated .prob-blink-1 { animation: prob-blink 8s ease-in-out infinite 0s; }
#home-problem.animated .prob-blink-2 { animation: prob-blink 8s ease-in-out infinite 3.1s; }
#home-problem.animated .prob-blink-3 { animation: prob-blink 8s ease-in-out infinite 5.7s; }

.prob-arrow {
  position: absolute; bottom: 2.5rem; left: 50%;
  transform: translateX(-50%);
  opacity: 0; transition: opacity 0.5s ease 2.8s;
  pointer-events: none; z-index: 20;
  cursor: pointer;
}
#home-problem.animated .prob-arrow { opacity: 1; pointer-events: auto; }

/* ============================
   CAROUSEL (Screen 5)
   ============================ */
#home-carousel { overflow: hidden; }
.carousel-track {
  display: grid;
  grid-template-rows: repeat(2, calc((100vh - 200px) / 2));
  grid-template-columns: repeat(7, calc((100vh - 200px) / 2 * 4 / 3));
  gap: 1.25rem;
  padding: 0 4rem;
  will-change: transform;
  transition: transform 1.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.carousel-item {
  border-radius: 0.75rem; overflow: hidden;
  background: rgba(255,255,255,0.05);
  display: flex; align-items: center; justify-content: center;
  font-family: serif; font-size: 0.75rem;
  color: rgba(255,255,255,0.15); letter-spacing: 0.1em;
  border: 1px solid rgba(255,255,255,0.07);
}

/* ============================
   HISTORY RIBBON (Screen 2)
   ============================ */
#home-history { position: relative; overflow: hidden; }
#history-ribbon {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
#home-history > div { position: relative; z-index: 1; }
#history-ribbon path {
  fill: none;
  stroke: url(#ribbon-gold);
  stroke-width: 6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ============================
   SAUCER (Screen 6)
   ============================ */
#home-results { position: relative; overflow: hidden; }
#results-saucer {
  position: absolute;
  right: -140px;
  top: 20px;
  width: 448px;
  height: 448px;
  border-radius: 50%;
  background: #f5ede6;
  border: 3px solid #c8a898;
  transform-origin: center center;
  will-change: transform;
}
#results-saucer::after {
  content: '';
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #6b1a1a;
}

/* ============================
   TEAM (Screen 7) — gold stripe
   ============================ */
#home-team { position: relative; }
#home-team::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 6px;
  background: linear-gradient(to right,
    #5c3d00, #b8820a 10%, #e8c040 22%, #fff5a0 35%,
    #d4a020 46%, #f0c838 55%, #fffacc 66%, #c89018 77%,
    #e8c040 87%, #7a5200 100%);
  background-size: 300% 100%;
  animation: gold-shimmer 4s ease-in-out infinite alternate;
}
@keyframes gold-shimmer {
  0%   { background-position: 0% center; }
  100% { background-position: 100% center; }
}
</style>
