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

export interface BinanceStatusResponse {
  connected: boolean
  environment: "production" | "testnet"
  mode: "live" | "sandbox"
  authenticated: boolean
  api_credentials_configured: boolean
  trading_enabled: boolean
  sub_account_configured: boolean
  testnet_auto_enabled: boolean
}

export interface ApiError {
  error: {
    code: string
    message: string
  }
}

// ── Sub-Account Types ──────────────────────────────────────────────

export interface SubAccountInfo {
  email: string
  is_trader: boolean
  is_futures_enabled: boolean
  is_margin_enabled: boolean
  is_options_enabled: boolean
  update_time: number
}

export interface SubAccountStatus {
  email: string
  is_sub_account: boolean
  is_margin_enabled: boolean
  is_futures_enabled: boolean
  is_asset_enabled: boolean
}

export interface SubAccountAsset {
  asset: string
  free: string
  locked: string
  total: string
}

export interface SubAccountAssetsResponse {
  balances: SubAccountAsset[]
}

export interface SubAccountSpotSummary {
  total_freeze_btc: string
  total_freeze_usdt: string
  total_net_asset_btc: string
  total_net_asset_usdt: string
}

export interface FuturesAccountAsset {
  asset: string
  wallet_balance: string
  unrealized_profit: string
  margin_balance: string
  available_balance: string
  cross_pnl: string
}

export interface FuturesAccountResponse {
  total_wallet_balance: string
  total_unrealized_profit: string
  total_margin_balance: string
  total_cross_wallet_balance: string
  available_balance: string
  max_withdraw_amount: string
  assets: FuturesAccountAsset[]
}

export interface FuturesPosition {
  symbol: string
  position_amount: string
  entry_price: string
  mark_price: string
  unrealized_profit: string
  leverage: number
  position_side: string
}

export interface FuturesPositionRiskResponse {
  positions: FuturesPosition[]
}

export interface FuturesAccountSummaryItem {
  sub_account_id: string
  total_margin_balance: string
  total_unrealized_profit: string
  total_wallet_balance: string
}

export interface FuturesAccountSummaryResponse {
  total_account_number: number
  total_wallet_balance: string
  total_unrealized_profit: string
  total_margin_balance: string
  asset: string
  sub_accounts: FuturesAccountSummaryItem[]
}

export interface MarginAccountAsset {
  asset: string
  free: string
  locked: string
  borrowed: string
  interest: string
  net_asset: string
}

export interface MarginAccountResponse {
  total_net_asset: string
  total_asset_in_btc: string
  total_liability_in_btc: string
  total_collateral_value_in_usdt: string
  user_assets: MarginAccountAsset[]
}

export interface MarginAccountSummaryItem {
  sub_account_id: string
  total_net_asset: string
  borrowed: string
  free: string
  interest: string
}

export interface MarginAccountSummaryResponse {
  total_net_asset: string
  sub_accounts: MarginAccountSummaryItem[]
}

export interface SpotTransfer {
  timestamp: number
  asset: string
  amount: string
  from_account: string
  to_account: string
}

export interface FuturesTransfer {
  timestamp: number
  asset: string
  amount: string
  from_account: string
  to_account: string
}

export interface UniversalTransfer {
  timestamp: number
  asset: string
  amount: string
  from_account: string
  to_account: string
  status: string
}

export interface DepositRecord {
  timestamp: number
  coin: string
  amount: string
  network: string
  address: string
  status: number
  tx_id: string
}

export interface DepositHistoryResponse {
  deposits: DepositRecord[]
}

export interface SubAccountConfigResponse {
  configured: boolean
}
