import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { ProjectMutationService } from '../application'
import type { ProjectDataRepository } from '../data'
import type {
  AssessmentBatch,
  ComponentInstance,
  Project,
  ProjectId,
  Scene,
  SceneId,
  VerificationItem,
} from '../domain'

interface ProjectSessionValue {
  status: 'loading' | 'ready' | 'error'
  errorMessage?: string
  project: Project | null
  scenes: readonly Scene[]
  componentInstances: readonly ComponentInstance[]
  assessmentBatches: readonly AssessmentBatch[]
  verificationItems: readonly VerificationItem[]
  renameScene: (sceneId: SceneId, name: string) => Promise<void>
  reload: () => void
}

const ProjectSessionContext = createContext<ProjectSessionValue | null>(null)

interface ProjectSessionProviderProps {
  children: ReactNode
  projectId: ProjectId
  repository: ProjectDataRepository
  mutations: ProjectMutationService
}

export function ProjectSessionProvider({
  children,
  projectId,
  repository,
  mutations,
}: ProjectSessionProviderProps) {
  const [status, setStatus] = useState<ProjectSessionValue['status']>('loading')
  const [errorMessage, setErrorMessage] = useState<string>()
  const [project, setProject] = useState<Project | null>(null)
  const [scenes, setScenes] = useState<Scene[]>([])
  const [componentInstances, setComponentInstances] = useState<ComponentInstance[]>([])
  const [assessmentBatches, setAssessmentBatches] = useState<AssessmentBatch[]>([])
  const [verificationItems, setVerificationItems] = useState<VerificationItem[]>([])
  const [loadVersion, setLoadVersion] = useState(0)

  useEffect(() => {
    let active = true
    setStatus('loading')
    Promise.all([
      repository.getProject(projectId),
      repository.getScenes(projectId),
      repository.getComponentInstances(projectId),
      repository.getAssessmentBatches(projectId),
      repository.getVerificationItems(projectId),
    ])
      .then(([nextProject, nextScenes, nextInstances, nextBatches, nextItems]) => {
        if (!active) return
        if (!nextProject) throw new Error('未找到当前项目')
        setProject(nextProject)
        setScenes([...nextScenes])
        setComponentInstances([...nextInstances])
        setAssessmentBatches([...nextBatches])
        setVerificationItems([...nextItems])
        setErrorMessage(undefined)
        setStatus('ready')
      })
      .catch((error: unknown) => {
        if (!active) return
        setErrorMessage(error instanceof Error ? error.message : '项目数据加载失败')
        setStatus('error')
      })
    return () => {
      active = false
    }
  }, [projectId, repository, loadVersion])

  const value = useMemo<ProjectSessionValue>(() => ({
    status,
    errorMessage,
    project,
    scenes,
    componentInstances,
    assessmentBatches,
    verificationItems,
    renameScene: async (sceneId, name) => {
      const result = await mutations.renameScene({ project_id: projectId, scene_id: sceneId, name })
      setScenes((current) => current.map((scene) => (
        scene.scene_id === result.scene_id ? { ...scene, name: result.name } : scene
      )))
    },
    reload: () => setLoadVersion((version) => version + 1),
  }), [
    assessmentBatches,
    componentInstances,
    errorMessage,
    mutations,
    project,
    projectId,
    scenes,
    status,
    verificationItems,
  ])

  return <ProjectSessionContext.Provider value={value}>{children}</ProjectSessionContext.Provider>
}

export function useProjectSession() {
  const context = useContext(ProjectSessionContext)
  if (!context) throw new Error('useProjectSession must be used inside ProjectSessionProvider')
  return context
}
