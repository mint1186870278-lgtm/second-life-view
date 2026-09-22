interface PlaceholderPageProps {
  code: string
  name: string
}

export function PlaceholderPage({ code, name }: PlaceholderPageProps) {
  return (
    <main className="development-placeholder">
      <strong>{code}</strong>
      <span>{name}</span>
    </main>
  )
}
