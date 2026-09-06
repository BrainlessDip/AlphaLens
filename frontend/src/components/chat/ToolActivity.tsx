import { Check, Loader2, X } from "lucide-react"
import { Marker, MarkerContent } from "@/components/ui/marker"
import type { ToolEvent } from "@/types/api"
import { cn } from "@/lib/utils"

export function ToolActivity({ events }: { events: ToolEvent[] }) {
  if (events.length === 0) return null

  return (
    <div className="flex flex-col gap-1.5" role="status" aria-live="polite" aria-label="Agent activity">
      {events.map((event) => (
        <Marker key={event.id}>
          {event.status === "running" && (
            <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-primary" aria-hidden />
          )}
          {event.status === "completed" && (
            <Check className="h-3.5 w-3.5 shrink-0 text-green-500" aria-hidden />
          )}
          {event.status === "error" && (
            <X className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden />
          )}
          <MarkerContent className={cn(event.status === "completed" && "text-muted-foreground/80")}>
            {event.label}
            <span className="sr-only">
              {event.status === "running" ? " (running)" : event.status === "completed" ? " (completed)" : " (failed)"}
            </span>
          </MarkerContent>
        </Marker>
      ))}
    </div>
  )
}
