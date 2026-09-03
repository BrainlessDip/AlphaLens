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
}

export interface BinanceAuthStatus {
  connected: boolean
  expires_at: string | null
  needs_reauth: boolean
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
}

export interface ChatRequest {
  message: string
}

export interface SSEToken {
  type: "token"
  content: string
}

export interface SSEDone {
  type: "done"
  conversation_id: string
}

export interface SSEError {
  type: "error"
  message: string
}

export type SSEEvent = SSEToken | SSEDone | SSEError

export interface ApiError {
  error: {
    code: string
    message: string
  }
}
