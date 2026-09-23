import { ImageIcon } from 'lucide-react'

export function MediaFallback({ label }: { label: string }) {
  return (
    <div className="media-fallback" role="img" aria-label={label}>
      <ImageIcon aria-hidden="true" />
      <span>360°</span>
    </div>
  )
}
