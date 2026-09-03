import { Outlet } from "react-router"
import { Header } from "./Header"

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-screen-xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
