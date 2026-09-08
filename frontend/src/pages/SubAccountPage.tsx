import { useState } from "react"
import { RefreshCw, Wallet, TrendingUp, ArrowUpDown, History, ChevronDown, AlertCircle, FlaskConical } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { EnvironmentBadge } from "@/components/binance/EnvironmentBadge"
import {
  useSubAccountConfig,
  useSubAccounts,
  useSubAccountAssets,
  useSubAccountSpotSummary,
  useFuturesAccount,
  useFuturesPositions,
  useFuturesSummary,
  useMarginSummary,
  useSpotTransfers,
  useDepositHistory,
} from "@/hooks/useSubAccount"
import { useBinanceStatus } from "@/hooks/useBinanceStatus"
import type { SubAccountInfo, SubAccountAsset, FuturesPosition, SpotTransfer, DepositRecord } from "@/types/api"

function formatUsdt(val: string | number): string {
  const n = typeof val === "string" ? parseFloat(val) : val
  if (isNaN(n)) return "$0.00"
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatAmount(val: string | number): string {
  const n = typeof val === "string" ? parseFloat(val) : val
  if (isNaN(n)) return "0"
  if (Math.abs(n) < 0.0001 && n !== 0) return n.toExponential(2)
  return n.toLocaleString(undefined, { maximumFractionDigits: 6 })
}

function timeAgo(ts: number): string {
  if (!ts) return ""
  const diff = Date.now() - ts
  if (diff < 60_000) return "just now"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return `${Math.floor(diff / 86_400_000)}d ago`
}

function StatusDot({ configured }: { configured: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <span className={`h-2 w-2 rounded-full ${configured ? "bg-green-500" : "bg-red-500"}`} />
      {configured ? "Connected" : "Not Configured"}
    </span>
  )
}

// ── Asset Table ──────────────────────────────────────────────────────

function AssetTable({ assets, loading }: { assets: SubAccountAsset[]; loading: boolean }) {
  const [hideZero, setHideZero] = useState(true)
  const [search, setSearch] = useState("")

  const filtered = assets.filter((a) => {
    if (hideZero && parseFloat(a.total) === 0) return false
    if (search && !a.asset.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <input
          type="text"
          placeholder="Search asset..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex h-8 w-40 rounded-md border bg-background px-3 py-1 text-sm"
        />
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none">
          <input
            type="checkbox"
            checked={hideZero}
            onChange={(e) => setHideZero(e.target.checked)}
            className="accent-primary"
          />
          Hide zero
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="pb-2 font-medium">Asset</th>
              <th className="pb-2 font-medium text-right">Available</th>
              <th className="pb-2 font-medium text-right">Locked</th>
              <th className="pb-2 font-medium text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-4 text-center text-muted-foreground">
                  No assets found
                </td>
              </tr>
            ) : (
              filtered.map((a) => (
                <tr key={a.asset} className="border-b last:border-0">
                  <td className="py-2 font-medium">{a.asset}</td>
                  <td className="py-2 text-right tabular-nums">{formatAmount(a.free)}</td>
                  <td className="py-2 text-right tabular-nums text-muted-foreground">
                    {formatAmount(a.locked)}
                  </td>
                  <td className="py-2 text-right tabular-nums font-medium">{formatAmount(a.total)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Positions Table ──────────────────────────────────────────────────

function PositionsTable({ positions, loading }: { positions: FuturesPosition[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">No open positions</p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="pb-2 font-medium">Symbol</th>
            <th className="pb-2 font-medium text-right">Size</th>
            <th className="pb-2 font-medium text-right">Entry</th>
            <th className="pb-2 font-medium text-right">Mark</th>
            <th className="pb-2 font-medium text-right">PnL</th>
            <th className="pb-2 font-medium text-right">Leverage</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p, i) => {
            const pnl = parseFloat(p.unrealized_profit)
            return (
              <tr key={`${p.symbol}-${i}`} className="border-b last:border-0">
                <td className="py-2 font-medium">{p.symbol}</td>
                <td className="py-2 text-right tabular-nums">{formatAmount(p.position_amount)}</td>
                <td className="py-2 text-right tabular-nums">{formatAmount(p.entry_price)}</td>
                <td className="py-2 text-right tabular-nums">{formatAmount(p.mark_price)}</td>
                <td className={`py-2 text-right tabular-nums font-medium ${pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {pnl >= 0 ? "+" : ""}{formatAmount(p.unrealized_profit)}
                </td>
                <td className="py-2 text-right">{p.leverage}x</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Transfers Table ──────────────────────────────────────────────────

function TransfersTable({ transfers, loading }: { transfers: SpotTransfer[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    )
  }

  if (transfers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">No transfer history</p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="pb-2 font-medium">Time</th>
            <th className="pb-2 font-medium">Asset</th>
            <th className="pb-2 font-medium text-right">Amount</th>
            <th className="pb-2 font-medium">From</th>
            <th className="pb-2 font-medium">To</th>
          </tr>
        </thead>
        <tbody>
          {transfers.map((t, i) => (
            <tr key={`${t.timestamp}-${i}`} className="border-b last:border-0">
              <td className="py-2 text-muted-foreground">{timeAgo(t.timestamp)}</td>
              <td className="py-2 font-medium">{t.asset}</td>
              <td className="py-2 text-right tabular-nums">{formatAmount(t.amount)}</td>
              <td className="py-2 text-xs text-muted-foreground truncate max-w-[120px]">{t.from_account}</td>
              <td className="py-2 text-xs text-muted-foreground truncate max-w-[120px]">{t.to_account}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────

function TestnetBanner() {
  const { data: status } = useBinanceStatus()
  if (!status || status.environment !== "testnet") return null

  return (
    <Card className="border-amber-500/20 bg-amber-500/5">
      <CardContent className="flex items-center gap-3 py-3">
        <FlaskConical className="h-5 w-5 text-amber-500 shrink-0" />
        <div className="text-sm">
          <span className="font-medium text-amber-600 dark:text-amber-400">Binance Testnet</span>
          <span className="text-muted-foreground ml-2">
            {status.testnet_auto_enabled
              ? "No API credentials detected — running in sandbox mode. All account data is simulated."
              : "Running in sandbox mode. Account data is from the testnet, not production."}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}


export function SubAccountPage() {
  const { data: config, isLoading: configLoading } = useSubAccountConfig()
  const { data: accounts, isLoading: accountsLoading, refetch: refetchAccounts } = useSubAccounts()
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"assets" | "futures" | "margin" | "transfers" | "deposits">("assets")

  const { data: assets, isLoading: assetsLoading, refetch: refetchAssets } = useSubAccountAssets(selectedEmail)
  const { data: spotSummary } = useSubAccountSpotSummary(selectedEmail ?? undefined)
  const { data: futuresData, isLoading: futuresLoading, refetch: refetchFutures } = useFuturesAccount(selectedEmail)
  const { data: positions, isLoading: positionsLoading } = useFuturesPositions(selectedEmail)
  const { data: futuresSummary } = useFuturesSummary()
  const { data: marginSummary } = useMarginSummary()
  const { data: transfers, isLoading: transfersLoading } = useSpotTransfers({
    to_email: selectedEmail ?? undefined,
    limit: 50,
  })
  const { data: deposits, isLoading: depositsLoading } = useDepositHistory(selectedEmail)

  const configured = config?.configured ?? false

  // Auto-select first account
  const accountList = accounts ?? []
  if (!selectedEmail && accountList.length > 0 && !accountsLoading) {
    setSelectedEmail(accountList[0].email)
  }

  const handleRefresh = () => {
    refetchAccounts()
    if (selectedEmail) {
      refetchAssets()
      refetchFutures()
    }
  }

  if (configLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (!configured) {
    return (
      <div className="space-y-6">
        <TestnetBanner />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Sub Account</h1>
            <EnvironmentBadge />
          </div>
          <StatusDot configured={false} />
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
            <AlertCircle className="h-12 w-12 text-muted-foreground" />
            <p className="text-muted-foreground text-center max-w-md">
              Sub-account API is not configured. Set <code className="bg-muted px-1 rounded text-xs">BINANCE_SUB_ACCOUNT_API_KEY</code> and <code className="bg-muted px-1 rounded text-xs">BINANCE_SUB_ACCOUNT_API_SECRET</code> environment variables to enable sub-account access.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const tabs = [
    { id: "assets" as const, label: "Assets", icon: Wallet },
    { id: "futures" as const, label: "Futures", icon: TrendingUp },
    { id: "margin" as const, label: "Margin", icon: TrendingUp },
    { id: "transfers" as const, label: "Transfers", icon: ArrowUpDown },
    { id: "deposits" as const, label: "Deposits", icon: History },
  ]

  return (
    <div className="space-y-6">
      {/* Environment Banner */}
      <TestnetBanner />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Sub Account</h1>
          <StatusDot configured={true} />
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-1.5" />
          Refresh
        </Button>
      </div>

      {/* Sub-account selector */}
      {accountList.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Account:</span>
          <div className="relative">
            <select
              value={selectedEmail ?? ""}
              onChange={(e) => setSelectedEmail(e.target.value || null)}
              className="h-8 appearance-none rounded-md border bg-background px-3 pr-8 text-sm"
            >
              {accountList.map((a) => (
                <option key={a.email} value={a.email}>
                  {a.email}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 pointer-events-none text-muted-foreground" />
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Net Asset</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tabular-nums">
              {spotSummary ? `${formatAmount(spotSummary.total_net_asset_usdt)}` : "—"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {spotSummary ? `${formatAmount(spotSummary.total_net_asset_btc)} BTC` : ""}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Spot Assets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tabular-nums">
              {assets ? `${assets.balances.length} coins` : "—"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedEmail || "Select an account"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Futures PnL</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tabular-nums">
              {futuresData ? (
                <span className={parseFloat(futuresData.total_unrealized_profit) >= 0 ? "text-green-500" : "text-red-500"}>
                  {formatUsdt(futuresData.total_unrealized_profit)}
                </span>
              ) : "—"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {futuresData ? `Balance: ${formatUsdt(futuresData.total_wallet_balance)}` : ""}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sub-Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accountList.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {accountList.filter((a) => a.is_futures_enabled).length} with futures
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-3.5 w-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <Card>
        <CardContent className="p-4">
          {activeTab === "assets" && (
            <AssetTable assets={assets?.balances ?? []} loading={assetsLoading} />
          )}
          {activeTab === "futures" && (
            <div className="space-y-4">
              {futuresData && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">Wallet</p>
                    <p className="font-medium tabular-nums">{formatUsdt(futuresData.total_wallet_balance)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Margin</p>
                    <p className="font-medium tabular-nums">{formatUsdt(futuresData.total_margin_balance)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Unrealized PnL</p>
                    <p className={`font-medium tabular-nums ${parseFloat(futuresData.total_unrealized_profit) >= 0 ? "text-green-500" : "text-red-500"}`}>
                      {formatUsdt(futuresData.total_unrealized_profit)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Available</p>
                    <p className="font-medium tabular-nums">{formatUsdt(futuresData.available_balance)}</p>
                  </div>
                </div>
              )}
              <div>
                <h3 className="text-sm font-medium mb-2">Open Positions</h3>
                <PositionsTable positions={positions?.positions ?? []} loading={positionsLoading} />
              </div>
            </div>
          )}
          {activeTab === "margin" && (
            <div className="space-y-4">
              {marginSummary && (
                <div className="text-sm">
                  <p className="text-muted-foreground">Total Net Asset</p>
                  <p className="font-medium tabular-nums">{formatAmount(marginSummary.total_net_asset)}</p>
                </div>
              )}
              {marginSummary?.sub_accounts && marginSummary.sub_accounts.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 font-medium">Account</th>
                        <th className="pb-2 font-medium text-right">Net Asset</th>
                        <th className="pb-2 font-medium text-right">Borrowed</th>
                        <th className="pb-2 font-medium text-right">Free</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marginSummary.sub_accounts.map((s) => (
                        <tr key={s.sub_account_id} className="border-b last:border-0">
                          <td className="py-2 text-xs font-mono">{s.sub_account_id}</td>
                          <td className="py-2 text-right tabular-nums">{formatAmount(s.total_net_asset)}</td>
                          <td className="py-2 text-right tabular-nums">{formatAmount(s.borrowed)}</td>
                          <td className="py-2 text-right tabular-nums">{formatAmount(s.free)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">No margin data</p>
              )}
            </div>
          )}
          {activeTab === "transfers" && (
            <TransfersTable transfers={transfers ?? []} loading={transfersLoading} />
          )}
          {activeTab === "deposits" && (
            <div>
              {depositsLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : (deposits?.deposits ?? []).length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No deposit history</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 font-medium">Time</th>
                        <th className="pb-2 font-medium">Coin</th>
                        <th className="pb-2 font-medium text-right">Amount</th>
                        <th className="pb-2 font-medium">Network</th>
                        <th className="pb-2 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(deposits?.deposits ?? []).map((d: DepositRecord, i: number) => {
                        const statusMap: Record<number, { label: string; color: string }> = {
                          0: { label: "Pending", color: "text-yellow-500" },
                          1: { label: "Success", color: "text-green-500" },
                          6: { label: "Credited", color: "text-green-500" },
                          7: { label: "Wrong", color: "text-red-500" },
                          8: { label: "Waiting", color: "text-yellow-500" },
                        }
                        const st = statusMap[d.status] ?? { label: `Status ${d.status}`, color: "text-muted-foreground" }
                        return (
                          <tr key={`${d.timestamp}-${i}`} className="border-b last:border-0">
                            <td className="py-2 text-muted-foreground">{timeAgo(d.timestamp)}</td>
                            <td className="py-2 font-medium">{d.coin}</td>
                            <td className="py-2 text-right tabular-nums">{formatAmount(d.amount)}</td>
                            <td className="py-2">{d.network}</td>
                            <td className={`py-2 font-medium ${st.color}`}>{st.label}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
