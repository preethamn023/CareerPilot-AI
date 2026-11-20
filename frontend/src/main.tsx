import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { Toaster } from "@/components/ui/sonner"
import { AppProvider } from "@/store/AppContext"
import App from "@/App"
import "@/index.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AppProvider>
        <App />
        <Toaster position="top-right" richColors closeButton />
      </AppProvider>
    </BrowserRouter>
  </StrictMode>,
)
