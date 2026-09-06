import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const bubbleVariants = cva("rounded-xl px-4 py-3 text-sm leading-relaxed", {
  variants: {
    variant: {
      default: "bg-primary text-primary-foreground",
      muted: "bg-secondary/60 text-foreground",
    },
  },
  defaultVariants: { variant: "muted" },
})

const Bubble = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-2", className)} {...props} />
  )
)
Bubble.displayName = "Bubble"

interface BubbleContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof bubbleVariants> {}

const BubbleContent = React.forwardRef<HTMLDivElement, BubbleContentProps>(
  ({ className, variant, ...props }, ref) => (
    <div ref={ref} className={cn(bubbleVariants({ variant }), className)} {...props} />
  )
)
BubbleContent.displayName = "BubbleContent"

const BubbleGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-2", className)} {...props} />
  )
)
BubbleGroup.displayName = "BubbleGroup"

const BubbleReactions = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center gap-1", className)} {...props} />
  )
)
BubbleReactions.displayName = "BubbleReactions"

export { Bubble, BubbleContent, BubbleGroup, BubbleReactions }
