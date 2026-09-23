import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

export function GuidancePanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel guidance-panel">
      <h2>{title}</h2>
      <div className="guidance-list">{children}</div>
    </section>
  )
}

export function GuidanceItem({
  icon: Icon,
  title,
  children,
  accent = false,
}: {
  icon: LucideIcon
  title: string
  children: ReactNode
  accent?: boolean
}) {
  return (
    <div className="guidance-item">
      <span className={`guidance-icon ${accent ? 'guidance-icon--accent' : ''}`}>
        <Icon size={25} strokeWidth={1.9} />
      </span>
      <div>
        <strong>{title}</strong>
        <p>{children}</p>
      </div>
    </div>
  )
}
