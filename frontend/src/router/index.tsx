import { createBrowserRouter } from "react-router"
import { AppLayout } from "@/components/layout/AppLayout"
import { DashboardPage } from "@/pages/DashboardPage"
import { ChatPage } from "@/pages/ChatPage"
import { AnalyzePage } from "@/pages/AnalyzePage"
import { SettingsPage } from "@/pages/SettingsPage"
import { BinanceCallbackPage } from "@/pages/BinanceCallbackPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "analyze", element: <AnalyzePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "auth/binance/callback", element: <BinanceCallbackPage /> },
    ],
  },
])
