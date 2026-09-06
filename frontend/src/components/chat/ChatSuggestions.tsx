import { Button } from "@/components/ui/button"

interface ChatSuggestionsProps {
  suggestions: string[]
  onSelect: (suggestion: string) => void
}

export function ChatSuggestions({ suggestions, onSelect }: ChatSuggestionsProps) {
  if (suggestions.length === 0) return null
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-2">
      <p className="mb-2 text-xs text-muted-foreground">Ask a follow-up</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <Button
            key={suggestion}
            variant="outline"
            size="sm"
            className="font-normal"
            onClick={() => onSelect(suggestion)}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  )
}
