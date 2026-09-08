import { createBrowserRouter, Navigate } from "react-router"
import { AppLayout } from "@/components/layout/AppLayout"
import { ChatPage } from "@/pages/ChatPage"
import { AnalyzePage } from "@/pages/AnalyzePage"
import { SettingsPage } from "@/pages/SettingsPage"
import { SubAccountPage } from "@/pages/SubAccountPage"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"
import { SharedChatPage } from "@/pages/SharedChatPage"
import { AuthGuard } from "@/components/auth/AuthGuard"

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
  {
    path: "/shared/:chatId",
    element: <SharedChatPage />,
  },
  {
    path: "/",
    element: (
      <AuthGuard>
        <AppLayout />
      </AuthGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: "analyze", element: <AnalyzePage /> },
      { path: "sub-account", element: <SubAccountPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
  {
    // Optional param keeps ChatPage mounted when a new chat gets its id,
    // so an in-flight first-message stream is never aborted by a remount.
    path: "/chat/:chatId?",
    element: (
      <AuthGuard>
        <ChatPage />
      </AuthGuard>
    ),
  },
])
