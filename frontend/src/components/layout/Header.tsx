import { Link, useLocation } from "react-router"
import { LayoutDashboard, MessageSquare, BarChart3, Settings, Menu, X, LogOut } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useBinanceStatus } from "@/hooks/useBinanceStatus"
import { useAuth } from "@/contexts/AuthContext"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/analyze", label: "Analyze", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings },
]

export function Header() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const { data: binance } = useBinanceStatus()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center px-4">
        <Link to="/" className="mr-6 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <span className="hidden font-bold sm:inline-block">AlphaLens</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                location.pathname === item.to
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex-1" />

        <div className="hidden md:flex items-center gap-3">
          <Badge variant={binance?.connected ? "success" : "secondary"}>
            {binance?.connected ? "Binance Connected" : "Binance Disconnected"}
          </Badge>

          {user && (
            <>
              <span className="text-xs text-muted-foreground">{user.username}</span>
              <Button variant="ghost" size="icon" onClick={logout} title="Logout">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t">
          <nav className="flex flex-col p-2">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent",
                  location.pathname === item.to ? "bg-accent" : ""
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
            <div className="px-3 py-2 flex items-center justify-between">
              <Badge variant={binance?.connected ? "success" : "secondary"}>
                {binance?.connected ? "Binance Connected" : "Binance Disconnected"}
              </Badge>
              {user && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{user.username}</span>
                  <Button variant="ghost" size="icon" onClick={logout} title="Logout">
                    <LogOut className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  )
}
