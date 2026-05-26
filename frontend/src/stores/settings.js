import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSettings, updateSettings } from '../api/settings'

export const useSettingsStore = defineStore('settings', () => {
  const hospitalName = ref('')
  const hospitalNameEn = ref('')
  const hospitalAddress = ref('')
  const hospitalPhone = ref('')
  const theme = ref('modern')
  const loaded = ref(false)

  async function fetchSettings() {
    if (loaded.value) return
    try {
      const res = await getSettings()
      const items = res.data || []
      const map = {}
      for (const item of items) {
        map[item.key] = item.value
      }
      hospitalName.value = map.hospital_name || ''
      hospitalNameEn.value = map.hospital_name_en || ''
      hospitalAddress.value = map.hospital_address || ''
      hospitalPhone.value = map.hospital_phone || ''
      theme.value = map.theme || 'modern'
      loaded.value = true
    } catch {
      loaded.value = true
    }
  }

  async function updateTheme(newTheme) {
    theme.value = newTheme
    try {
      await updateSettings({ settings: [{ key: 'theme', value: newTheme }] })
    } catch {
      // ignore
    }
  }

  return {
    hospitalName,
    hospitalNameEn,
    hospitalAddress,
    hospitalPhone,
    theme,
    loaded,
    fetchSettings,
    updateTheme,
  }
})
