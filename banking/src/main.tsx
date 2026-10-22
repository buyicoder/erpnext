import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import './lib/namespace'
import { DirectionProvider } from './components/ui/direction.tsx'
import { resolveTranslationMessages } from './lib/boot-translations.js'

function renderApp(layoutDirection: 'ltr' | 'rtl') {
  createRoot(document.getElementById('root') as HTMLElement).render(
    <StrictMode>
      <DirectionProvider dir={layoutDirection}>
        <App />
      </DirectionProvider>
    </StrictMode>,
  )
}

async function startProductionApp() {
  window.frappe._messages = await resolveTranslationMessages(
    window.frappe?._messages,
    window.frappe?._translations_loaded,
  )
  window.frappe.model.sync(window.frappe.boot.docs)
  renderApp(window.frappe?.boot?.layout_direction ?? 'ltr')
}

if (import.meta.env.DEV) {
  fetch('/api/method/erpnext.www.banking.get_context_for_dev', {
    method: 'POST',
  }).then(response => response.json()).then((values) => {
    if (!window.frappe) window.frappe = {};
    //@ts-expect-error - frappe will be available
    frappe.boot = JSON.parse(values.message.boot);
    //@ts-expect-error - frappe will be available
    frappe._messages = frappe.boot["__messages"];

    // Set document direction to rtl
    document.dir = values.message.layout_direction;
    window.frappe.model.sync(window.frappe.boot.docs);
    renderApp(values.message.layout_direction)

  })
} else {
  void startProductionApp()
}
