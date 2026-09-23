/** Prototype-derived DEMO options only. They are not production enums. */
export interface ProjectOption {
  value: string
  label: string
}

export interface ProjectOptionSource {
  regionOptions: readonly ProjectOption[]
  projectTypeOptions: readonly ProjectOption[]
  projectStageOptions: readonly ProjectOption[]
}

export const demoProjectOptionSource: ProjectOptionSource = {
  regionOptions: [
    { value: '南京 · 江苏', label: '南京 · 江苏' },
    { value: '上海', label: '上海' },
    { value: '深圳 · 广东', label: '深圳 · 广东' },
    { value: '香港', label: '香港' },
  ],
  projectTypeOptions: [
    { value: '改造 / 翻新', label: '改造 / 翻新' },
    { value: '局部更新', label: '局部更新' },
    { value: '拆除 / 清退', label: '拆除 / 清退' },
  ],
  projectStageOptions: [
    { value: '拟拆改前评估', label: '拟拆改前评估' },
    { value: '方案设计中', label: '方案设计中' },
    { value: '施工前确认', label: '施工前确认' },
  ],
}
