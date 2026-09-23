/**
 * D01 presentation density from the approved prototype.
 * These values are not canonical entities, selectors, identifiers, or writes.
 */
export const d01DemoProjection = {
  assessment_date: '2026.09.22',
  updated_date: '2026.09.22',
  evidence_labels: ['主视图', '细节 01', '细节 02', '细节 03', '细节 04'],
  evidence_count: 6,
  observable_facts: [
    '表面腐损轻微',
    '结构基本完整',
    '安装方式疑似螺栓固定',
    '涂层存在老化',
    '周边环境为屋顶花园，暴露于室外',
  ],
  assessment_rationale: '现有构件整体结构仍具保留价值，但表面处理与隐藏损伤仍需核实；建议确认可拆卸性后进行修复翻新。',
  references: [
    { title: '欧洲办公建筑改造', copy: '拆卸 → 清理 → 打磨 → 再涂装 → 室内隔断 / 景观构件', tags: ['木构件', '修复再利用'] },
    { title: '日本旧木再利用', copy: '拆解 → 分级 → 局部修补 → 家具 / 室内构件', tags: ['木构件', '改造再利用'] },
  ],
  guideline: { title: '行业指南 · 可拆卸设计', copy: '优先保留完整截面，采用可拆卸连接，便于重复使用与再加工。' },
  local_opportunities: [
    { title: '南京木构件修复中心', copy: '木构件修复 / 重新加工', status: '能力已核实', tone: 'green' },
    { title: '本地再利用渠道', copy: '二手建材市场 / 供需对接', status: '存在性已核实', tone: 'blue' },
    { title: '创意再生工作室', copy: '定制化再利用 / 景观构件', status: '线索待核实', tone: 'amber' },
  ],
} as const
