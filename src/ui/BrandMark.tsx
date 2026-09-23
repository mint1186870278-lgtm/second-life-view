import { Leaf } from 'lucide-react'

export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <Leaf size={27} strokeWidth={2.2} />
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
