import * as React from "react"
import { cn } from "@/lib/utils"

interface MessageProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end"
}

const Message = React.forwardRef<HTMLDivElement, MessageProps>(
  ({ className, align = "start", ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex w-full gap-3", align === "end" ? "flex-row-reverse" : "flex-row", className)}
      {...props}
    />
  )
)
Message.displayName = "Message"

const MessageAvatar = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("shrink-0 pt-0.5", className)} {...props} />
  )
)
MessageAvatar.displayName = "MessageAvatar"

const MessageContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex min-w-0 max-w-[85%] flex-col gap-2 sm:max-w-[75%]", className)} {...props} />
  )
)
MessageContent.displayName = "MessageContent"

const MessageFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center gap-1 text-xs text-muted-foreground", className)} {...props} />
  )
)
MessageFooter.displayName = "MessageFooter"

export { Message, MessageAvatar, MessageContent, MessageFooter }
