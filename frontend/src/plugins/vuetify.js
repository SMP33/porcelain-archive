import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import '../assets/tailwind.css'
import '../assets/theme.css'
import { createVuetify } from 'vuetify'

// Палитра в духе фарфоровых заводов: clay (красный) как основной акцент,
// ink (почти чёрный) как вторичный, gold - предупреждения.
const archiveTheme = {
  dark: false,
  colors: {
    background: '#f6f1ea',
    surface: '#FFFFFF',
    primary: '#8c1b1b',
    'primary-darken-1': '#721616',
    secondary: '#1f1f1f',
    'secondary-darken-1': '#080808',
    error: '#dc2626',
    success: '#16a34a',
    warning: '#c8922a',
    info: '#2563eb',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'archive',
    themes: {
      archive: archiveTheme,
    },
  },
  defaults: {
    VBtn: { rounded: 'lg' },
    VCard: { rounded: 'lg' },
    VChip: { rounded: 'lg' },
    VTextField: { variant: 'outlined', density: 'comfortable', rounded: 'lg' },
    VSelect: { variant: 'outlined', density: 'comfortable', rounded: 'lg' },
  },
  icons: {
    defaultSet: 'mdi',
  },
})
