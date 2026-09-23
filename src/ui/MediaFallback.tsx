export function MediaFallback({ label }: { label: string }) {
  return (
    <div className="media-fallback" role="img" aria-label={label}>
      <span>360°</span>
    </div>
  )
}
