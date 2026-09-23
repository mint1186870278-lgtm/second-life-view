import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

interface FormFieldProps {
  id: string
  label: string
  required?: boolean
  error?: string
  helper?: string
  children: ReactNode
}

export function FormField({ id, label, required, error, helper, children }: FormFieldProps) {
  return (
    <div className="form-field">
      <label className="form-label" htmlFor={id}>
        {label}{required && <span className="required-mark"> *</span>}
      </label>
      <div className="form-control-stack">
        {children}
        {helper && <div className="form-helper">{helper}</div>}
        {error && <div className="form-error" role="alert">{error}</div>}
      </div>
    </div>
  )
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`control ${className}`.trim()} {...props} />
}

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: readonly SelectOption[]
}

export function Select({ options, className = '', ...props }: SelectProps) {
  return (
    <select className={`control control--select ${className}`.trim()} {...props}>
      <option value="">请选择</option>
      {options.map((option) => (
        <option key={option.value} value={option.value} disabled={option.disabled}>
          {option.label}
        </option>
      ))}
    </select>
  )
}

export function Textarea({ className = '', ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`control textarea ${className}`.trim()} {...props} />
}
