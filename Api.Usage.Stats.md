# Api Usage Stats

| Действие пользователя | API метод | Где используется |
| --- | --- | --- |
| Авторизация | POST /api/users/login | ui/login.html |
| Выход из аккаунта | POST /api/users/logout | ui/document_list.html, кнопка logout |
| Проверка сессии | GET /api/users/me | ui/document_list.html, onMounted |
| Список документов | GET /api/documents/ | ui/document_list.html, таблица |
| Создание документа | POST /api/documents/create | ui/document_list.html, диалог создания |
| Смена пароля | POST /api/users/reset_password | ui/_toolbar.html, меню пользователя |
| Изменение ФИО | POST /api/users/set_display_name | ui/_toolbar.html, меню пользователя |
| Создание ветки редактирования | POST /api/documents/{document_id}/create_branch | ui/document.html, кнопка "Редактировать документ" |
| Загрузка страниц документа | POST /api/documents/branches/{branch_id}/pages | ui/edit.html, форма загрузки страниц |
| Удаление страниц | POST /api/documents/branches/{branch_id}/pages/remove | ui/edit.html, форма "Удалить страницы" |
| Список наборов изменений | GET /api/documents/branches/ | ui/branch_list.html, таблица |
| Список пользователей | GET /api/users/ | ui/user_list.html, таблица |
| Информация о документе | GET /api/documents/{document_id} | ui/document.html, название документа |
| Информация о ветке | GET /api/documents/branches/{branch_id} | ui/edit.html, название документа версии |
| Слияние ветки в master | POST /api/documents/branches/{branch_id}/merge | ui/edit.html, кнопка "Слить в master" (видна с правом review) |
| Задать текст (PDF) | POST /api/documents/branches/{branch_id}/text | ui/edit.html, форма "Задать текст" |
| Убрать текст | POST /api/documents/branches/{branch_id}/text/reset | ui/edit.html, форма "Убрать текст" |
| Количество страниц в наборе изменений | GET /api/documents/branches/{branch_id}/pages/count | ui/edit.html, отображение количества страниц; ui/document.html, размер галереи страниц |
| Допустимые расширения страниц | GET /api/documents/pages/allowed_extensions | ui/edit.html, атрибут accept формы загрузки |
| Список задач | GET /api/tasks/ | ui/task_list.html, таблица задач |
| Задачи по ветке | GET /api/tasks/branch/{branch_id} | ui/edit.html, блок "Задачи по этой ветке" |
| Лог задачи | GET /api/tasks/{task_id}/log | ui/task_list.html, вывод лога для выбранной задачи |
| Автообновление списка задач | WS /api/tasks/ws | ui/task_list.html, обновление таблицы и лога при изменении задач в БД; ui/edit.html, обновление задач ветки и количества страниц |
| Id основной (master) ветки документа | GET /api/documents/{document_id}/master_branch_id | ui/document.html, определение ветки для галереи страниц |
| Изображение страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/image | ui/edit.html и ui/document.html, полноразмерный просмотр страницы в диалоге |
| Превью изображения страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/image/preview | ui/edit.html и ui/document.html, миниатюры в галерее страниц |
| Текст страницы ветки | GET /api/documents/branches/{branch_id}/pages/{page_index}/text | ui/edit.html и ui/document.html, спаны текста и подсветка в диалоге просмотра страницы |
