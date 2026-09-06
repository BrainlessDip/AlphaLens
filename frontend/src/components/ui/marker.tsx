import * as React from "react"
import { cn } from "@/lib/utils"

const Marker = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      role="status"
      className={cn(
        "flex items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-3 py-2 text-[13px] text-muted-foreground",
        className
      )}
      {...props}
    />
  )
)
Marker.displayName = "Marker"

const MarkerContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex-1 leading-snug", className)} {...props} />
  )
)
MarkerContent.displayName = "MarkerContent"

export { Marker, MarkerContent }
