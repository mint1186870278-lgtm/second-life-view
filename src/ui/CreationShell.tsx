import type { ReactNode } from 'react'
import { BrandLockup } from './BrandMark'
import { Button } from './Button'

const steps = ['项目设置', '素材接入', '分析处理'] as const

export function CreationStepper({ activeStep }: { activeStep: 1 | 2 | 3 }) {
  return (
    <ol className="creation-stepper" aria-label="创建进度">
      {steps.map((label, index) => {
        const step = index + 1
        return (
          <li key={label} className={step === activeStep ? 'is-active' : ''} aria-current={step === activeStep ? 'step' : undefined}>
            <span className="step-number">{step}</span>
            <span>{label}</span>
          </li>
        )
      })}
    </ol>
  )
}

export function CreationShell({ activeStep, children }: { activeStep: 1 | 2 | 3; children: ReactNode }) {
  return (
    <div className="app-frame creation-frame">
      <header className="creation-topbar">
        <BrandLockup />
        <CreationStepper activeStep={activeStep} />
        <div className="creation-topbar__actions">
          <Button variant="tertiary" disabled title="退出创建流程尚未定义">退出创建</Button>
        </div>
      </header>
      <main className="creation-page">{children}</main>
    </div>
  )
}
