<template>
  <v-navigation-drawer permanent width="232" theme="dark" class="app-sidebar">
    <router-link to="/" class="app-sidebar-brand tw:flex tw:items-center tw:gap-3 tw:px-5 tw:py-5 tw:text-white tw:no-underline">
      <span
        class="tw:flex tw:items-center tw:justify-center tw:w-8 tw:h-8 tw:shrink-0 tw:rounded tw:bg-clay-500"
        style="transform: skewX(-10deg);"
      >
        <v-icon size="18" color="white" style="transform: skewX(10deg);">mdi-book-open-page-variant</v-icon>
      </span>
      <span class="tw:text-base tw:leading-tight">Архив</span>
    </router-link>

    <v-list nav density="compact" class="tw:px-2 tw:py-3">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
        class="app-sidebar-link"
        active-class="app-sidebar-link--active"
      ></v-list-item>
    </v-list>

    <template v-slot:append>
      <div class="app-sidebar-foot tw:px-2 tw:py-3">
        <div v-if="user" class="tw:px-3 tw:pb-2 tw:text-xs tw:truncate" style="color: rgba(255,255,255,0.45);">
          {{ user.display_name || user.username }}
        </div>

        <v-menu v-if="user" location="end">
          <template v-slot:activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-account-cog" title="Аккаунт" class="app-sidebar-link"></v-list-item>
          </template>
          <v-list>
            <v-list-item title="Список задач" to="/tasks"></v-list-item>
            <v-list-item title="Сменить пароль" @click="showResetPasswordDialog = true"></v-list-item>
            <v-list-item title="Изменить ФИО" @click="showSetDisplayNameDialog = true"></v-list-item>
          </v-list>
        </v-menu>

        <v-list-item
          v-if="user"
          prepend-icon="mdi-logout"
          title="Выйти"
          class="app-sidebar-link"
          @click="handleLogout"
        ></v-list-item>
        <v-list-item
          v-else
          prepend-icon="mdi-login"
          title="Войти"
          class="app-sidebar-link"
          to="/login"
        ></v-list-item>
      </div>
    </template>
  </v-navigation-drawer>

  <v-dialog v-model="showResetPasswordDialog" max-width="400">
    <v-card>
      <v-card-title>Смена пароля</v-card-title>
      <v-card-text>
        <v-text-field
          v-model="oldPassword"
          label="Текущий пароль"
          type="password"
          autofocus
        ></v-text-field>
        <v-text-field
          v-model="newPassword"
          label="Новый пароль"
          type="password"
          @keyup.enter="handleResetPassword"
        ></v-text-field>
        <v-alert v-if="resetPasswordError" type="error" density="compact">{{ resetPasswordError }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="showResetPasswordDialog = false">Отмена</v-btn>
        <v-btn color="primary" :loading="resetPasswordLoading" @click="handleResetPassword">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="showSetDisplayNameDialog" max-width="400">
    <v-card>
      <v-card-title>Изменение ФИО</v-card-title>
      <v-card-text>
        <v-text-field
          v-model="displayNameInput"
          label="ФИО"
          autofocus
          @keyup.enter="handleSetDisplayName"
        ></v-text-field>
        <v-alert v-if="setDisplayNameError" type="error" density="compact">{{ setDisplayNameError }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="showSetDisplayNameDialog = false">Отмена</v-btn>
        <v-btn color="primary" :loading="setDisplayNameLoading" @click="handleSetDisplayName">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'

const {
  user, handleLogout,
  showResetPasswordDialog, oldPassword, newPassword, resetPasswordLoading, resetPasswordError, handleResetPassword,
  showSetDisplayNameDialog, displayNameInput, setDisplayNameLoading, setDisplayNameError, handleSetDisplayName,
} = useAuth()

const navItems = [
  { to: '/', title: 'Документы', icon: 'mdi-file-document-multiple-outline' },
  { to: '/branches', title: 'Наборы изменений', icon: 'mdi-source-branch' },
  { to: '/tasks', title: 'Задачи', icon: 'mdi-format-list-checks' },
  { to: '/users', title: 'Пользователи', icon: 'mdi-account-group-outline' },
]
</script>
