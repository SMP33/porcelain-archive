<script setup>
</script>

<template>
  <div>
    <div class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2">
        <router-link to="/" class="tw:hover:text-clay-500 tw:transition-colors">Каталог</router-link>
        <span>›</span>
        <span class="tw:text-ink-800">О проекте</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
      <div class="tw:max-w-2xl">

        <h1 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-6">О проекте</h1>

        <div class="tw:prose tw:prose-stone tw:space-y-5 tw:text-sm tw:leading-relaxed tw:text-gray-700">

          <p>
            Этот архив собирает и сохраняет оцифрованные документы российских керамических
            и фарфоровых заводов — технические условия, приказы, патенты, переписку,
            каталоги изделий и другие материалы, отражающие историю отечественной
            керамической промышленности.
          </p>

          <p>
            Документы поступают из региональных и ведомственных архивов, частных коллекций
            и от потомков работников заводов. Каждый документ проходит описание
            и привязывается к конкретному предприятию.
          </p>

          <h2 class="tw:font-serif tw:text-xl tw:font-semibold tw:text-ink-900 tw:mt-8 tw:mb-3">Как пользоваться архивом</h2>
          <ul class="tw:list-disc tw:list-inside tw:space-y-2">
            <li>Перейдите в <router-link to="/materials" class="tw:text-clay-500 tw:hover:underline">Материалы</router-link> и выберите нужный документ</li>
            <li>Просматривайте страницы документа в виде галереи</li>
            <li>Используйте <router-link to="/search" class="tw:text-clay-500 tw:hover:underline">Поиск</router-link> для поиска по названию, автору или типу документа</li>
            <li>Нажмите на документ, чтобы открыть все его страницы</li>
            <li>Кликните на страницу для просмотра в полном размере</li>
          </ul>

          <h2 class="tw:font-serif tw:text-xl tw:font-semibold tw:text-ink-900 tw:mt-8 tw:mb-3">Участие в проекте</h2>
          <p>
            Если у вас есть документы, фотографии или сведения о керамических заводах —
            свяжитесь с нами через форму <router-link to="/feedback" class="tw:text-clay-500 tw:hover:underline">Обратной связи</router-link>.
            Мы будем рады пополнить архив новыми материалами.
          </p>

        </div>

      </div>
    </main>
  </div>
</template>
