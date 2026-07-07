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
