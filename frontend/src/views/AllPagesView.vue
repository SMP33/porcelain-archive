<script setup>
// Временная страница-заглушка со списком всех страниц Porcelain и ceramic -
// для ручной проверки после слияния проектов. Удалить, когда будет не нужна.

const porcelainPages = [
  { path: '/', title: 'Документы (список)' },
  { path: '/branches', title: 'Наборы изменений', note: 'требует входа' },
  { path: '/tasks', title: 'Задачи', note: 'требует входа' },
  { path: '/users', title: 'Пользователи', note: 'требует входа' },
  { path: '/server-log', title: 'Лог сервера', note: 'требует входа, роль admin' },
  { path: '/document/1', title: 'Документ (пример, id=1)' },
  { path: '/edit/1', title: 'Редактирование набора изменений (пример, id=1)' },
  { path: '/login', title: 'Вход' },
  { path: '/access-denied', title: 'Доступ запрещён' },
]

const ceramicPublicPages = [
  { path: '/ceramic', title: 'Главная' },
  { path: '/ceramic/materials', title: 'Материалы (список документов)' },
  { path: '/ceramic/document/1', title: 'Документ (пример, id=1)' },
  { path: '/ceramic/search', title: 'Поиск' },
  { path: '/ceramic/about', title: 'О проекте' },
  { path: '/ceramic/feedback', title: 'Обратная связь' },
]

const ceramicAdminPages = [
  { path: '/ceramic/admin/login', title: 'Вход в админку' },
  { path: '/ceramic/admin', title: 'Админка (редирект)', note: 'требует входа' },
  { path: '/ceramic/admin/feedback', title: 'Обратная связь (админка)', note: 'требует входа, роль admin' },
  { path: '/ceramic/admin/users', title: 'Пользователи (админка)', note: 'требует входа, роль admin' },
]
</script>

<template>
  <div class="tw:min-h-screen tw:bg-gray-100 tw:p-8">
    <div class="tw:max-w-3xl tw:mx-auto tw:space-y-6">
      <div class="tw:bg-amber-50 tw:border tw:border-amber-200 tw:text-amber-800 tw:text-sm tw:rounded-lg tw:px-4 tw:py-2">
        Временная страница со списком всех страниц проекта (Porcelain + ceramic) - для ручной проверки после слияния.
      </div>

      <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
        <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Porcelain (архив документов)</h2>
        <ul class="tw:divide-y tw:divide-gray-100">
          <li v-for="p in porcelainPages" :key="p.path" class="tw:py-2 tw:flex tw:items-center tw:justify-between tw:gap-4">
            <div>
              <router-link :to="p.path" class="tw:text-sm tw:font-medium tw:text-clay-600 tw:hover:text-clay-500 tw:transition-colors">{{ p.title }}</router-link>
              <span v-if="p.note" class="tw:text-xs tw:text-gray-400 tw:ml-2">({{ p.note }})</span>
            </div>
            <code class="tw:text-xs tw:text-gray-400">{{ p.path }}</code>
          </li>
        </ul>
      </div>

      <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
        <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">ceramic - публичная часть</h2>
        <ul class="tw:divide-y tw:divide-gray-100">
          <li v-for="p in ceramicPublicPages" :key="p.path" class="tw:py-2 tw:flex tw:items-center tw:justify-between tw:gap-4">
            <div>
              <router-link :to="p.path" class="tw:text-sm tw:font-medium tw:text-clay-600 tw:hover:text-clay-500 tw:transition-colors">{{ p.title }}</router-link>
              <span v-if="p.note" class="tw:text-xs tw:text-gray-400 tw:ml-2">({{ p.note }})</span>
            </div>
            <code class="tw:text-xs tw:text-gray-400">{{ p.path }}</code>
          </li>
        </ul>
      </div>

      <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
        <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">ceramic - админка</h2>
        <ul class="tw:divide-y tw:divide-gray-100">
          <li v-for="p in ceramicAdminPages" :key="p.path" class="tw:py-2 tw:flex tw:items-center tw:justify-between tw:gap-4">
            <div>
              <router-link :to="p.path" class="tw:text-sm tw:font-medium tw:text-clay-600 tw:hover:text-clay-500 tw:transition-colors">{{ p.title }}</router-link>
              <span v-if="p.note" class="tw:text-xs tw:text-gray-400 tw:ml-2">({{ p.note }})</span>
            </div>
            <code class="tw:text-xs tw:text-gray-400">{{ p.path }}</code>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
