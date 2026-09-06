import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

const CommandDialog = ({
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root>) => (
  <DialogPrimitive.Root {...props}>
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60" />
      <DialogPrimitive.Content
        className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 overflow-hidden rounded-xl border bg-popover shadow-lg"
        aria-describedby={undefined}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  </DialogPrimitive.Root>
)

interface CommandItemProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: React.ReactNode
}

const CommandInput = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <div className="flex items-center gap-2 border-b px-4">
      <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
      <input
        ref={ref}
        className={cn(
          "h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground",
          className
        )}
        {...props}
      />
    </div>
  )
)
CommandInput.displayName = "CommandInput"

const CommandList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} role="listbox" className={cn("max-h-72 overflow-y-auto p-2", className)} {...props} />
  )
)
CommandList.displayName = "CommandList"

const CommandItem = React.forwardRef<HTMLButtonElement, CommandItemProps>(
  ({ className, icon, children, ...props }, ref) => (
    <button
      ref={ref}
      role="option"
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-left transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:outline-none",
        className
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
)
CommandItem.displayName = "CommandItem"

export { CommandDialog, CommandInput, CommandList, CommandItem }
