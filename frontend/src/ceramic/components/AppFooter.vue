<script setup>
import { useRoute } from 'vue-router'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import http from '../api/http'

const route = useRoute()
const isHome = computed(() => route.name === 'ceramic-home')

// Тире полоски email + анимация: случайные 2-3 тире иногда затухают и возвращаются.
const DASH_COUNT = 19
const dashes = Array.from({ length: DASH_COUNT }, (_, i) => i)
const hiddenDashes = ref(new Set())
let dashTimer = null

// Иногда вместо центральных тире проступает слово «email»: буквы появляются
// вразнобой (по одной, случайный порядок), держатся целиком, затем так же по одной уходят.
const showEmailWord = ref(false) // фаза слова активна - прячем только тире под буквами
const WORD_CENTER = new Set([8, 9, 10])
const wordLetters = ['e', 'm', 'a', 'i', 'l']
const visibleLetters = ref(new Set())
let wordTimeouts = []

function isDashHidden(i) {
  return hiddenDashes.value.has(i) || (showEmailWord.value && WORD_CENTER.has(i))
}

function laterWord(fn, ms) {
  wordTimeouts.push(setTimeout(fn, ms))
}
function clearWordTimeouts() {
  wordTimeouts.forEach(clearTimeout)
  wordTimeouts = []
}
function shuffled(arr) {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}
function setLetter(i, on) {
  const next = new Set(visibleLetters.value)
  if (on) next.add(i)
  else next.delete(i)
  visibleLetters.value = next
}
function startWord() {
  showEmailWord.value = true
  visibleLetters.value = new Set()
  const idx = wordLetters.map((_, i) => i)
  const step = 240
  const inOrder = shuffled(idx)
  inOrder.forEach((li, k) => laterWord(() => setLetter(li, true), 200 + k * step))
  const allInAt = 200 + inOrder.length * step
  const outStart = allInAt + 1500 // держим слово целиком
  const outOrder = shuffled(idx)
  outOrder.forEach((li, k) => laterWord(() => setLetter(li, false), outStart + k * step))
  const endAt = outStart + outOrder.length * step + 500
  laterWord(() => {
    showEmailWord.value = false
    scheduleWord()
  }, endAt)
}
function scheduleWord() {
  laterWord(startWord, 4000 + Math.random() * 4000)
}

function pulseDashes() {
  const count = 2 + Math.floor(Math.random() * 2) // 2 или 3
  const available = dashes.filter((i) => !hiddenDashes.value.has(i))
  const chosen = []
  for (let k = 0; k < count && available.length; k++) {
    chosen.push(available.splice(Math.floor(Math.random() * available.length), 1)[0])
  }
  if (!chosen.length) return
  const next = new Set(hiddenDashes.value)
  chosen.forEach((i) => next.add(i))
  hiddenDashes.value = next
  setTimeout(() => {
    const back = new Set(hiddenDashes.value)
    chosen.forEach((i) => back.delete(i))
    hiddenDashes.value = back
  }, 700 + Math.random() * 700)
}

onMounted(() => {
  dashTimer = setInterval(pulseDashes, 550 + Math.random() * 400)
  scheduleWord()
})
onUnmounted(() => {
  if (dashTimer) clearInterval(dashTimer)
  clearWordTimeouts()
})

const email = ref('')
const consent = ref(false)
const done = ref(false)
const error = ref(false)
const emailRef = ref(null)
const consentRef = ref(null)

function onEmailInvalid() {
  const el = emailRef.value
  el.setCustomValidity(
    el.validity.valueMissing
      ? 'Введите адрес электронной почты'
      : 'Введите корректный адрес электронной почты',
  )
}
function onConsentInvalid() {
  consentRef.value.setCustomValidity('Пожалуйста, дайте согласие на обработку персональных данных')
}

async function onSubmit() {
  error.value = false
  try {
    await http.post('/api/ceramic/subscribe', { email: email.value, consent: consent.value })
    done.value = true
  } catch {
    error.value = true
  }
}
</script>

<template>
  <footer class="tw:bg-ink-800 tw:text-clay-100 tw:text-sm tw:mt-auto" :style="isHome ? { scrollSnapAlign: 'start' } : {}">
    <form v-if="!done" @submit.prevent="onSubmit"
          class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:flex-wrap tw:items-center tw:gap-x-4 tw:gap-y-3 tw:justify-center">
      <span class="tw:text-white tw:font-bold tw:text-base tw:shrink-0">
        <span class="footer-point">👉</span>&nbsp;&nbsp;&nbsp;Подпишитесь на новости проекта
      </span>

      <div class="footer-email-box tw:shrink-0">
        <template v-if="!email">
          <div class="footer-email-dashes" aria-hidden="true">
            <span v-for="i in dashes" :key="i" class="footer-dash"
                  :style="{ opacity: isDashHidden(i) ? 0 : 1 }"></span>
          </div>
          <span class="footer-email-word" aria-hidden="true">
            <span v-for="(ch, i) in wordLetters" :key="i" class="footer-word-letter"
                  :style="{ opacity: visibleLetters.has(i) ? 1 : 0 }">{{ ch }}</span>
          </span>
        </template>
        <input ref="emailRef" v-model="email" type="email" name="email" required autocomplete="off"
               @invalid="onEmailInvalid" @input="emailRef.setCustomValidity('')"
               class="footer-email-input">
      </div>

      <span class="tw:flex tw:items-center tw:gap-2 tw:text-white/50 tw:text-xs tw:shrink-0">
        <input ref="consentRef" v-model="consent" type="checkbox" name="consent" required
               @invalid="onConsentInvalid" @change="consentRef.setCustomValidity('')"
               class="footer-consent">
        <span>Даю согласие на обработку <router-link to="/privacy" class="footer-privacy-link">персональных данных</router-link></span>
      </span>

      <button type="submit"
              class="tw:shrink-0 tw:px-4 tw:py-1.5 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white
                     tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors">
        Подписаться
      </button>
      <span v-if="error" class="tw:w-full tw:text-center tw:text-red-400 tw:text-xs">
        Что-то пошло не так, попробуйте позже
      </span>
    </form>
    <div v-else class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:justify-center">
      <span class="tw:text-white/80 tw:text-sm tw:py-2">✓ Вы подписаны на новости проекта</span>
    </div>
  </footer>
</template>

<style scoped>
@keyframes point {
  0%, 100% { transform: translateX(0); }
  50%      { transform: translateX(5px); }
}
.footer-point { display: inline-block; animation: point 1s ease-in-out infinite; }

/* Круглый чекбокс: белое кольцо без заливки; при отметке - красная заливка без точки */
.footer-consent {
  appearance: none;
  -webkit-appearance: none;
  width: 0.95rem;
  height: 0.95rem;
  border-radius: 9999px;
  border: 1px solid #ffffff;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  transition: background-color 0.15s, border-color 0.15s;
}
.footer-consent:checked {
  background: #dc2626;
  border-color: #dc2626;
}

/* Ссылка на политику: обычное подчёркивание */
.footer-privacy-link {
  color: inherit;
  text-decoration: underline;
}

/* Email: без рамки и заливки. Пока пусто - по центру высоты во всю ширину пунктир (тире);
   как только начинают вводить - тире скрываются (v-if), показывается белый текст. */
.footer-email-box {
  position: relative;
  width: 18rem;
  height: 2rem;
}
.footer-email-dashes {
  position: absolute;
  /* По центру поля, 19 отдельных тире (тире 8px + зазор 7px). Отдельные элементы
     нужны, чтобы анимировать затухание каждого тире независимо. */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 7px;
  pointer-events: none;
}
.footer-dash {
  width: 8px;
  height: 2px;
  background: rgba(255, 255, 255, 0.75);
  transition: opacity 1.1s ease;
}
.footer-email-word {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: rgba(255, 255, 255, 0.85);
  font-size: 1rem;
  letter-spacing: 0.06em;
  pointer-events: none;
  white-space: pre;
}
.footer-word-letter {
  transition: opacity 1.1s ease;
}
.footer-email-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: #ffffff;
  font-size: 1rem;
  text-align: left;
  padding: 0 0.15rem;
}
</style>
