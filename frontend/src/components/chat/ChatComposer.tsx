import { useEffect, useRef, useState } from "react"
import { Send, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface ChatComposerProps {
  onSend: (message: string) => void
  isStreaming: boolean
  onStop: () => void
  draftKey?: string
  placeholder?: string
  autoFocus?: boolean
}

export function ChatComposer({
  onSend,
  isStreaming,
  onStop,
  draftKey = "composer-draft",
  placeholder = "Ask AlphaLens anything...",
  autoFocus = false,
}: ChatComposerProps) {
  const [value, setValue] = useState(() => sessionStorage.getItem(draftKey) ?? "")
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    sessionStorage.setItem(draftKey, value)
  }, [value, draftKey])

  useEffect(() => {
    if (autoFocus) ref.current?.focus()
  }, [autoFocus])

  const canSend = value.trim().length > 0 && !isStreaming

  const handleSend = () => {
    const text = value.trim()
    if (!text || isStreaming) return
    setValue("")
    sessionStorage.removeItem(draftKey)
    onSend(text)
  }

  const autoresize = () => {
    const el = ref.current
    if (el) {
      el.style.height = "auto"
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`
    }
  }

  return (
    <div className="border-t bg-background px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
      <div
        className={cn(
          "mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border bg-secondary/40 p-2 pl-4",
          "focus-within:border-ring/50"
        )}
      >
        <Textarea
          ref={ref}
          value={value}
          rows={1}
          placeholder={placeholder}
          aria-label="Chat message"
          onChange={(e) => {
            setValue(e.target.value)
            autoresize()
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault()
              handleSend()
            }
          }}
          className="max-h-40 flex-1 resize-none border-0 bg-transparent p-0 text-sm shadow-none focus-visible:ring-0"
        />
        {isStreaming ? (
          <Button size="icon" variant="secondary" onClick={onStop} aria-label="Stop generation">
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button size="icon" onClick={handleSend} disabled={!canSend} aria-label="Send message">
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted-foreground">
        Market analysis is observational, not financial advice.
      </p>
    </div>
  )
}
