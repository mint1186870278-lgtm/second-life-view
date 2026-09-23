import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import {
  creationProjectMutationService,
  creationProjectRepository,
} from '../data'
import { CREATION_DEMO_PROJECT_ID } from '../fixtures'
import {
  C01ProjectSetupPage,
  C02SceneIngestionPage,
  C03AnalysisPage,
  W01WorkspacePlaceholderPage,
} from '../pages'
import { CreationFlowProvider } from './CreationFlowContext'
import { PlaceholderPage } from './PlaceholderPage'
import { ProjectSessionProvider } from './ProjectSessionContext'
import { ImplementationRoutes } from './routes'

export function App() {
  return (
    <ProjectSessionProvider
      projectId={CREATION_DEMO_PROJECT_ID}
      repository={creationProjectRepository}
      mutations={creationProjectMutationService}
    >
      <Routes>
        <Route path="/" element={<Navigate to={ImplementationRoutes.c01} replace />} />
        <Route element={<CreationFlowRoutes />}>
          <Route path={ImplementationRoutes.c01} element={<C01ProjectSetupPage />} />
          <Route path={ImplementationRoutes.c02} element={<C02SceneIngestionPage />} />
          <Route path={ImplementationRoutes.c03} element={<C03AnalysisPage />} />
        </Route>
        <Route path={ImplementationRoutes.w01} element={<W01WorkspacePlaceholderPage />} />
        <Route path={ImplementationRoutes.w02} element={<PlaceholderPage code="W02" name="项目审查（W02-A / W02-B 为内部视图）" />} />
        <Route path={ImplementationRoutes.d01} element={<PlaceholderPage code="D01" name="AssessmentBatch Detail / Human Verification" />} />
        <Route path="*" element={<PlaceholderPage code="404" name="Development route not found" />} />
      </Routes>
    </ProjectSessionProvider>
  )
}

function CreationFlowRoutes() {
  return (
    <CreationFlowProvider>
      <Outlet />
    </CreationFlowProvider>
  )
}
