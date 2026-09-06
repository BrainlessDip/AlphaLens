import { useState } from "react"
import { Bot, Check, Copy, FileText, Info, RefreshCw, Share2 } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageAvatar, MessageContent, MessageFooter } from "@/components/ui/message"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { createShare } from "@/api/chats"
import { MarkdownMessage } from "./MarkdownMessage"
import { cn, formatPrice, formatVolume } from "@/lib/utils"
import type {
  ChatMessage as ChatMessageType,
  MarketData,
  StreamEvent,
  StreamMarketDataEvent,
  StreamToolEvent,
  StreamUnknownEvent,
  ToolUseItem,
} from "@/types/api"

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}

function MarketDataCard({ data }: { data: MarketData }) {
  const isUp = data.change_pct !== null && data.change_pct > 0
  const isDown = data.change_pct !== null && data.change_pct < 0

  return (
    <div className="mb-3 rounded-lg border border-border/50 bg-secondary/30 p-3">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-muted-foreground">{data.symbol}</span>
        <span className="text-[11px] text-muted-foreground/60">
          {formatRelativeTime(data.timestamp)}
        </span>
      </div>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="text-xl font-bold tracking-tight">
          {formatPrice(data.price)}
        </span>
        {data.change_pct !== null && (
          <span
            className={`text-sm font-medium ${
              isUp ? "text-green-500" : isDown ? "text-red-500" : "text-muted-foreground"
            }`}
          >
            {isUp ? "+" : ""}{data.change_pct.toFixed(2)}% 24h
          </span>
        )}
      </div>
      <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
        <span>Vol: {formatVolume(data.volume_24h)}</span>
        <span>Quote: ${formatVolume(data.quote_volume_24h)}</span>
      </div>
    </div>
  )
}

function ToolRow({ event }: { event: StreamToolEvent }) {
  return (
    <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
      {event.status === "running" && (
        <span className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-primary border-t-transparent" aria-hidden />
      )}
      {event.status === "completed" && (
        <Check className="h-3.5 w-3.5 shrink-0 text-green-500" aria-hidden />
      )}
      {event.status === "error" && (
        <span className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden>×</span>
      )}
      <span className={event.status === "completed" ? "text-muted-foreground/80" : undefined}>
        {event.label}
        <span className="sr-only">
          {event.status === "running" ? " (running)" : event.status === "completed" ? " (completed)" : " (failed)"}
        </span>
      </span>
    </div>
  )
}

function UnknownEventCard({ event }: { event: StreamUnknownEvent }) {
  const [expanded, setExpanded] = useState(false)
  const { raw } = event
  const keys = Object.keys(raw).filter((k) => k !== "type")

  return (
    <div className="mb-2 rounded-lg border border-dashed border-border/40 bg-muted/20 p-2.5">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 text-left text-xs text-muted-foreground hover:text-muted-foreground/80"
      >
        <Info className="h-3 w-3 shrink-0" />
        <span className="font-medium">{event.type}</span>
        {keys.length > 0 && (
          <span className="ml-auto text-[10px] text-muted-foreground/50">
            {expanded ? "hide" : `${keys.length} field${keys.length === 1 ? "" : "s"}`}
          </span>
        )}
      </button>
      {expanded && (
        <pre className="mt-2 overflow-x-auto rounded bg-muted/40 p-2 text-[11px] leading-relaxed text-muted-foreground">
          {JSON.stringify(raw, null, 2)}
        </pre>
      )}
    </div>
  )
}

interface StreamEventsRendererProps {
  events: StreamEvent[]
}

function CompareTable({ rows }: { rows: StreamMarketDataEvent[] }) {
  return (
    <div className="mb-2 overflow-hidden rounded-lg border border-border/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border/50 bg-muted/30 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
            <th className="px-3 py-2 font-medium">Symbol</th>
            <th className="px-3 py-2 text-right font-medium">Price</th>
            <th className="px-3 py-2 text-right font-medium">24h</th>
            <th className="px-3 py-2 text-right font-medium">Volume</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const isUp = row.change_pct !== null && row.change_pct > 0
            const isDown = row.change_pct !== null && row.change_pct < 0
            return (
              <tr key={row.symbol} className="border-b border-border/30 last:border-0">
                <td className="px-3 py-2 font-medium">{row.symbol}</td>
                <td className="px-3 py-2 text-right tabular-nums">{formatPrice(row.price)}</td>
                <td
                  className={cn(
                    "px-3 py-2 text-right tabular-nums",
                    isUp ? "text-green-500" : isDown ? "text-red-500" : "text-muted-foreground"
                  )}
                >
                  {row.change_pct === null ? "—" : `${isUp ? "+" : ""}${row.change_pct.toFixed(2)}%`}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                  {formatVolume(row.quote_volume_24h)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

type Bias = "Bullish" | "Bearish" | "Neutral"
type Confidence = "High" | "Moderate" | "Low"

interface Insights {
  bias?: Bias
  confidence?: Confidence
}

function extractInsights(content: string): Insights {
  const lower = content.toLowerCase()
  const insights: Insights = {}
  if (/\bbullish\b/.test(lower)) insights.bias = "Bullish"
  else if (/\bbearish\b/.test(lower)) insights.bias = "Bearish"
  else if (/\bneutral\b/.test(lower)) insights.bias = "Neutral"
  const match = lower.match(/\bconfidence[:\s]+(high|moderate|medium|low)\b/)
  if (match) {
    const level = match[1]
    insights.confidence = (level === "medium" ? "Moderate" : level.charAt(0).toUpperCase() + level.slice(1)) as Confidence
  }
  return insights
}

function BiasBadge({ bias }: { bias: Bias }) {
  const styles: Record<Bias, string> = {
    Bullish: "border-green-500/30 bg-green-500/10 text-green-500",
    Bearish: "border-red-500/30 bg-red-500/10 text-red-500",
    Neutral: "border-border/60 bg-muted/40 text-muted-foreground",
  }
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${styles[bias]}`}>
      {bias}
    </span>
  )
}

const TOOL_ENDPOINTS: Record<string, string> = {
  get_ticker: "GET /api/v3/ticker/price",
  get_24h_stats: "GET /api/v3/ticker/24hr",
  get_klines: "GET /api/v3/klines",
  get_order_book: "GET /api/v3/depth",
  get_recent_trades: "GET /api/v3/trades",
  get_exchange_info: "GET /api/v3/exchangeInfo",
  get_indicators: "computed from GET /api/v3/klines",
}

function sourcesFromMessage(message: ChatMessageType) {
  const tools: ToolUseItem[] =
    message.toolsUsed && message.toolsUsed.length > 0
      ? message.toolsUsed
      : (message.streamEvents ?? [])
          .filter((e): e is StreamToolEvent => e.type === "tool" && "status" in e)
          .map((e) => ({ tool: e.tool, label: e.label }))
  const symbols = (message.streamEvents ?? [])
    .filter((e): e is StreamMarketDataEvent => e.type === "market_data")
    .map((e) => e.symbol)
  return { tools, symbols }
}

function SourceDrawer({ message }: { message: ChatMessageType }) {
  const { tools, symbols } = sourcesFromMessage(message)
  const timeframes = new Set<string>()
  for (const t of tools) {
    const m = t.label.match(/\b(1m|5m|15m|1h|4h|1d|1w)\b/i)
    if (m) timeframes.add(m[1].toLowerCase())
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="h-7 w-7" aria-label="How did you get this?">
          <FileText className="h-3.5 w-3.5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>How AlphaLens got this</SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-4 text-sm">
          {message.dataTimestamp && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Data freshness</p>
              <p className="text-xs">Market data · Updated {formatRelativeTime(message.dataTimestamp)}</p>
            </div>
          )}
          {tools.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Data sources</p>
              <ul className="flex flex-col gap-1.5">
                {tools.map((t, i) => (
                  <li key={i} className="text-xs">
                    <span className="block font-medium">{t.label}</span>
                    <span className="text-muted-foreground/70">{TOOL_ENDPOINTS[t.tool] ?? t.tool}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {symbols.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Symbols</p>
              <p className="text-xs">{symbols.join(", ")}</p>
            </div>
          )}
          {timeframes.size > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Timeframes</p>
              <p className="text-xs">{[...timeframes].join(", ")}</p>
            </div>
          )}
          <p className="border-t border-border/50 pt-3 text-[11px] text-muted-foreground/60">
            Verifiable inputs and methodology — not reasoning. Prices come from live Binance market data.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function ShareRow({ chatId }: { chatId: string }) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    if (url) return
    setError(null)
    try {
      const res = await createShare(chatId)
      setUrl(`${window.location.origin}${res.url}`)
    } catch {
      setError("Couldn't create a share link. Try again.")
    }
  }

  const handleCopy = async () => {
    if (!url) return
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard unavailable — user can select the input manually
    }
  }

  return (
    <div className="mt-1 flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-1.5">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 gap-1 px-1.5 text-xs text-muted-foreground"
          onClick={handleShare}
          aria-label="Share analysis"
        >
          <Share2 className="h-3 w-3" />
          {url ? "Link ready" : "Share analysis"}
        </Button>
        {url && (
          <>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 gap-1 px-1.5 text-xs text-muted-foreground"
              onClick={handleCopy}
              aria-label="Copy share link"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy link"}
            </Button>
            <a href={url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">
              Open
            </a>
          </>
        )}
      </div>
      {url && (
        <input
          readOnly
          value={url}
          onFocus={(e) => e.currentTarget.select()}
          className="h-7 w-full rounded border border-border/60 bg-muted/30 px-2 text-[11px] text-muted-foreground"
          aria-label="Share link"
        />
      )}
      {error && <p className="text-[11px] text-destructive">{error}</p>}
    </div>
  )
}

function StreamEventsRenderer({ events }: StreamEventsRendererProps) {
  const rendered: React.ReactNode[] = []
  let accumulatedContent = ""
  let contentKey = 0
  const marketData: StreamMarketDataEvent[] = []

  function flushContent() {
    if (accumulatedContent) {
      rendered.push(
        <Bubble key={`content-${contentKey++}`}>
          <BubbleContent variant="muted">
            <MarkdownMessage content={accumulatedContent} />
          </BubbleContent>
        </Bubble>
      )
      accumulatedContent = ""
    }
  }

  function flushMarketData() {
    if (marketData.length === 0) return
    const bySymbol = new Map<string, StreamMarketDataEvent>()
    for (const d of marketData) {
      if (!bySymbol.has(d.symbol)) bySymbol.set(d.symbol, d)
    }
    const rows = [...bySymbol.values()]
    if (rows.length >= 2) {
      rendered.push(
        <CompareTable key={`compare-${rows.map((r) => r.symbol).join("-")}`} rows={rows} />
      )
    } else {
      rendered.push(...rows.map((d) => <MarketDataCard key={d.id} data={d} />))
    }
    marketData.length = 0
  }

  const toolEvents = events.filter((e): e is StreamToolEvent => e.type === "tool" && "status" in e)
  const collapseTools = toolEvents.length > 0 && toolEvents.every((e) => e.status !== "running")
  let toolsSummaryRendered = false

  for (const event of events) {
    switch (event.type) {
      case "tool":
        if (!("status" in event)) break
        flushContent()
        flushMarketData()
        if (collapseTools) {
          if (!toolsSummaryRendered) {
            toolsSummaryRendered = true
            rendered.push(
              <div key="tools-summary" className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                <Check className="h-3.5 w-3.5 shrink-0 text-green-500" aria-hidden />
                <span>
                  Checked {toolEvents.length} data source{toolEvents.length === 1 ? "" : "s"}
                </span>
              </div>
            )
          }
        } else {
          rendered.push(<ToolRow key={event.id} event={event} />)
        }
        break
      case "assistant_delta":
        if (!("content" in event)) break
        flushMarketData()
        accumulatedContent += event.content
        break
      case "market_data":
        marketData.push(event as StreamMarketDataEvent)
        break
      case "message_start":
      case "message_complete":
      case "error":
        break
      default:
        flushContent()
        flushMarketData()
        rendered.push(<UnknownEventCard key={event.id} event={event as StreamUnknownEvent} />)
        break
    }
  }

  flushMarketData()
  flushContent()

  return <>{rendered}</>
}

interface ChatMessageProps {
  message: ChatMessageType
  chatId?: string
  onRegenerate?: () => void
  onCopy?: (content: string) => void
}

export function ChatMessage({ message, chatId, onRegenerate, onCopy }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)
  const isUser = message.role === "user"
  const showActions = !isUser && message.status !== "streaming" && message.content !== ""
  const insights: Insights =
    !isUser && message.content !== "" ? extractInsights(message.content) : {}
  const { tools } = sourcesFromMessage(message)
  const hasSources = !!message.dataTimestamp || tools.length > 0
  const showShare = !isUser && !!chatId && message.status !== "streaming" && message.content !== ""

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
    } catch {
      onCopy?.(message.content)
      return
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const hasStreamEvents = message.role === "assistant" && !!message.streamEvents?.length

  return (
    <Message align={isUser ? "end" : "start"} className="group">
      {!isUser && (
        <MessageAvatar>
          <Avatar>
            <AvatarFallback className="bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
        </MessageAvatar>
      )}

      <MessageContent>
        <div className="flex flex-col gap-2">
          {hasStreamEvents ? (
            <StreamEventsRenderer events={message.streamEvents!} />
          ) : (
            message.content !== "" && (
              <Bubble>
                <BubbleContent variant={isUser ? "default" : "muted"}>
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <MarkdownMessage content={message.content} />
                  )}
                </BubbleContent>
              </Bubble>
            )
          )}
          {message.status === "streaming" && message.content === "" && !hasStreamEvents && (
            <Bubble>
              <BubbleContent variant="muted">
                <span className="flex gap-1 py-1" aria-label="Thinking">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
                </span>
              </BubbleContent>
            </Bubble>
          )}
        </div>

        {(insights.bias || insights.confidence) && message.status !== "streaming" && (
          <div className="flex flex-wrap items-center gap-1.5">
            {insights.bias && <BiasBadge bias={insights.bias} />}
            {insights.confidence && (
              <span className="rounded-full border border-border/60 px-2 py-0.5 text-[11px] text-muted-foreground">
                Confidence: {insights.confidence}
              </span>
            )}
          </div>
        )}

        {showActions && (
          <MessageFooter className="opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100 max-sm:opacity-100">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy} aria-label="Copy response">
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied" : "Copy"}</TooltipContent>
            </Tooltip>
            {onRegenerate && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={onRegenerate}
                    aria-label="Regenerate response"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Regenerate</TooltipContent>
              </Tooltip>
            )}
            {hasSources && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div>
                    <SourceDrawer message={message} />
                  </div>
                </TooltipTrigger>
                <TooltipContent>How did you get this?</TooltipContent>
              </Tooltip>
            )}
            {showShare && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => setShareOpen((v) => !v)}
                    aria-label="Share analysis"
                  >
                    <Share2 className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{shareOpen ? "Hide share link" : "Share analysis"}</TooltipContent>
              </Tooltip>
            )}
          </MessageFooter>
        )}
        {!isUser && message.dataTimestamp && message.status !== "streaming" && (
          <p className="mt-1 text-[11px] text-muted-foreground/50">
            Data checked {formatRelativeTime(message.dataTimestamp)}
          </p>
        )}
        {shareOpen && chatId && <ShareRow chatId={chatId} />}
      </MessageContent>
    </Message>
  )
}
