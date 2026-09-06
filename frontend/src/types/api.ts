export interface AuthUser {
  username: string
  token: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface HealthResponse {
  status: string
  model?: string | null
  binance_status?: string | null
}

export interface AnalyzeRequest {
  symbol: string
  question: string
}

export interface PriceInfo {
  symbol: string
  price: number
  change_pct: number | null
}

export interface VolumeInfo {
  volume_24h: number
  quote_volume_24h: number
}

export interface AnalyzeResponse {
  symbol: string
  current_price: number
  price_change: PriceInfo
  volume_info: VolumeInfo
  market_observations: string[]
  agent_analysis: string
  confidence_and_limitations: string
  data_timestamp: string
}

export interface ChatRequest {
  message: string
  chat_id?: string | null
}

export interface ChatSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ChatListResponse {
  items: ChatSummary[]
  total: number
}

export interface ChatMessageItem {
  id: string
  chat_id: string
  role: "user" | "assistant"
  content: string
  status: string
  created_at: string
}

export interface ChatDetailResponse {
  id: string
  title: string
  created_at: string
  updated_at: string
  messages: ChatMessageItem[]
}

export interface ToolUseItem {
  tool: string
  label: string
}

export interface ShareResponse {
  token: string
  url: string
}

export type ToolEventStatus = "running" | "completed" | "error"

export interface ToolEvent {
  id: string
  tool: string
  label: string
  status: ToolEventStatus
}

export type ChatMessageStatus = "streaming" | "completed" | "error"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: string
  status?: ChatMessageStatus
  dataTimestamp?: string
  streamEvents?: StreamEvent[]
  toolsUsed?: ToolUseItem[]
}

export interface MarketData {
  symbol: string
  price: number
  change_pct: number | null
  volume_24h: number
  quote_volume_24h: number
  timestamp: string
}

export interface SSEMessageStart {
  type: "message_start"
  chat_id: string
}

export interface SSEToolStart {
  type: "tool_start"
  tool: string
  label: string
}

export interface SSEToolComplete {
  type: "tool_complete"
  tool: string
}

export interface SSEAssistantDelta {
  type: "assistant_delta"
  content: string
}

export interface SSEMessageComplete {
  type: "message_complete"
  chat_id: string
  message_id: string
  data_timestamp?: string
  suggestions?: string[] | null
  tools_used?: ToolUseItem[] | null
}

export interface SSEMarketData {
  type: "market_data"
  symbol: string
  price: number
  change_pct: number | null
  volume_24h: number
  quote_volume_24h: number
  timestamp: string
}

export interface SSEError {
  type: "error"
  message: string
}

export interface SSEUnknown {
  type: string
  [key: string]: unknown
}

export type SSEEvent =
  | SSEMessageStart
  | SSEToolStart
  | SSEToolComplete
  | SSEAssistantDelta
  | SSEMessageComplete
  | SSEMarketData
  | SSEError
  | SSEUnknown

export type SSEKnownEvent = Exclude<SSEEvent, SSEUnknown>

export type SSEFrame =
  | { known: true; event: SSEKnownEvent }
  | { known: false; event: SSEUnknown }

export interface StreamEventBase {
  id: string
  receivedAt: string
}

export interface StreamMessageStartEvent extends StreamEventBase {
  type: "message_start"
  chatId: string
}

export interface StreamToolEvent extends StreamEventBase {
  type: "tool"
  tool: string
  label: string
  status: "running" | "completed" | "error"
}

export interface StreamAssistantDeltaEvent extends StreamEventBase {
  type: "assistant_delta"
  content: string
}

export interface StreamMessageCompleteEvent extends StreamEventBase {
  type: "message_complete"
  chatId: string
  messageId: string
  dataTimestamp?: string
  suggestions?: string[] | null
  toolsUsed?: ToolUseItem[] | null
}

export interface StreamMarketDataEvent extends StreamEventBase {
  type: "market_data"
  symbol: string
  price: number
  change_pct: number | null
  volume_24h: number
  quote_volume_24h: number
  timestamp: string
}

export interface StreamErrorEvent extends StreamEventBase {
  type: "error"
  message: string
}

export interface StreamUnknownEvent extends StreamEventBase {
  type: string
  raw: Record<string, unknown>
}

export type StreamEvent =
  | StreamMessageStartEvent
  | StreamToolEvent
  | StreamAssistantDeltaEvent
  | StreamMessageCompleteEvent
  | StreamMarketDataEvent
  | StreamErrorEvent
  | StreamUnknownEvent

export interface ApiError {
  error: {
    code: string
    message: string
  }
}
