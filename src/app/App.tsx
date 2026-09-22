import { Navigate, Route, Routes } from 'react-router-dom'
import { PlaceholderPage } from './PlaceholderPage'
import { ImplementationRoutes } from './routes'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={ImplementationRoutes.c01} replace />} />
      <Route path={ImplementationRoutes.c01} element={<PlaceholderPage code="C01" name="项目设置" />} />
      <Route path={ImplementationRoutes.c02} element={<PlaceholderPage code="C02" name="素材接入" />} />
      <Route path={ImplementationRoutes.c03} element={<PlaceholderPage code="C03" name="分析处理" />} />
      <Route path={ImplementationRoutes.w01} element={<PlaceholderPage code="W01" name="再生视图" />} />
      <Route path={ImplementationRoutes.w02} element={<PlaceholderPage code="W02" name="项目审查（W02-A / W02-B 为内部视图）" />} />
      <Route path={ImplementationRoutes.d01} element={<PlaceholderPage code="D01" name="AssessmentBatch Detail / Human Verification" />} />
      <Route path="*" element={<PlaceholderPage code="404" name="Development route not found" />} />
    </Routes>
  )
}
