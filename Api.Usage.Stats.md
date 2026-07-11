# Api Usage Stats

| Действие пользователя | API метод | Где используется |
| --- | --- | --- |
| Авторизация | POST /api/users/login | frontend/src/views/LoginView.vue |
| Выход из аккаунта | POST /api/users/logout | frontend/src/composables/useAuth.js, кнопка "Выйти" в AppToolbar |
| Проверка сессии | GET /api/users/me | frontend/src/composables/useAuth.js, checkAuth (вызывается роутером при первой навигации) |
| Список документов | GET /api/documents/ | frontend/src/views/DocumentListView.vue, таблица |
| Создание документа | POST /api/documents/create | frontend/src/views/DocumentListView.vue, диалог создания |
| Смена пароля | POST /api/users/reset_password | frontend/src/components/AppToolbar.vue, меню пользователя |
| Изменение ФИО | POST /api/users/set_display_name | frontend/src/components/AppToolbar.vue, меню пользователя |
| Создание ветки редактирования | POST /api/documents/{document_id}/create_branch | frontend/src/views/DocumentView.vue, кнопка "Редактировать документ" |
| Загрузка страниц документа | POST /api/documents/branches/{branch_id}/pages | frontend/src/components/edit/AddPagesPanel.vue |
| Удаление страниц | POST /api/documents/branches/{branch_id}/pages/remove | frontend/src/components/edit/RemovePagesPanel.vue |
| Список наборов изменений | GET /api/documents/branches/ | frontend/src/views/BranchListView.vue, таблица |
| Список пользователей | GET /api/users/ | frontend/src/views/UserListView.vue, таблица |
| Информация о документе | GET /api/documents/{document_id} | frontend/src/views/DocumentView.vue, название документа |
| Информация о ветке | GET /api/documents/branches/{branch_id} | frontend/src/views/EditView.vue, название документа версии |
| Слияние ветки в master | POST /api/documents/branches/{branch_id}/merge | frontend/src/components/edit/MergeBranchDialog.vue, кнопка "Завершить правки" (видна с правом review) |
| Задать текст (PDF) | POST /api/documents/branches/{branch_id}/text | frontend/src/components/edit/SetTextPanel.vue |
| Убрать текст | POST /api/documents/branches/{branch_id}/text/reset | frontend/src/components/edit/ResetTextPanel.vue |
| Количество страниц в наборе изменений | GET /api/documents/branches/{branch_id}/pages/count | frontend/src/views/EditView.vue, отображение количества страниц; frontend/src/views/DocumentView.vue, размер галереи страниц |
| Допустимые расширения страниц | GET /api/documents/pages/allowed_extensions | frontend/src/views/EditView.vue, атрибут accept формы загрузки (передаётся в AddPagesPanel.vue) |
| Список задач | GET /api/tasks/ | frontend/src/views/TaskListView.vue, таблица задач |
| Задачи по ветке | GET /api/tasks/branch/{branch_id} | frontend/src/components/edit/BranchTasksPanel.vue |
| Лог задачи | GET /api/tasks/{task_id}/log | frontend/src/views/TaskListView.vue, вывод лога для выбранной задачи |
| Автообновление списка задач | WS /api/tasks/ws | frontend/src/views/TaskListView.vue, обновление таблицы и лога при изменении задач в БД; frontend/src/views/EditView.vue, обновление задач ветки и количества страниц |
| Id основной (master) ветки документа | GET /api/documents/{document_id}/master_branch_id | frontend/src/views/DocumentView.vue, определение ветки для галереи страниц |
| Изображение страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/image | frontend/src/components/PageGalleryViewer.vue, полноразмерный просмотр страницы в диалоге |
| Превью изображения страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/image/preview | frontend/src/components/PageGalleryViewer.vue, миниатюры в галерее страниц |
| Текст страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/text | frontend/src/components/PageGalleryViewer.vue, спаны текста и подсветка в диалоге просмотра страницы |
| Создание пользователя | POST /api/users/create | frontend/src/views/UserListView.vue, диалог "Новый пользователь" (кнопка видна при is_admin) |
