export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 4C11 4 5 8 5 15c0 3 2 5 5 5 7 0 9-8 9-16Z" />
        <path d="M5 20c3-5 6-8 11-11" />
      </svg>
    </span>
  )
}

export function BrandLockup() {
  return (
    <div className="brand-lockup">
      <BrandMark />
      <div>
        <div className="brand-title">Second Life View｜再生视图</div>
        <div className="brand-subtitle">从旧建筑到新的开始</div>
      </div>
    </div>
  )
}
