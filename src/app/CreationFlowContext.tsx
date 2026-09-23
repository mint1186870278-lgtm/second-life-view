import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  fallbackDemoScenes,
  fetchDemoScenes,
  runDemoAnalysis,
  type DemoAnalysisResult,
  type DemoScene,
} from '../api/demo'
import type { Project } from '../domain'
import { useProjectSession } from './ProjectSessionContext'

/** Editable C01 form state. It is intentionally not a canonical Project entity. */
export interface ProjectFormDraft {
  name: string
  region: string
  projectType: string
  projectStage: string
  description: string
}

/** Confirmed on-site capture shown alongside demo sample cards on C02. */
export interface LiveScene {
  id: string
  name: string
  thumbnail_url: string
  width: number
  height: number
  file_size_bytes?: number
  capture_id: string
  local_path?: string | null
  source: 'live_capture'
}

interface CreationFlowValue {
  projectDraft: ProjectFormDraft
  updateProjectDraft: (patch: Partial<ProjectFormDraft>) => void
  demoScenes: readonly DemoScene[]
  liveScenes: readonly LiveScene[]
  selectedSceneIds: readonly string[]
  selectedLiveIds: readonly string[]
  sceneCatalogStatus: 'idle' | 'loading' | 'ready' | 'fallback'
  sceneCatalogError?: string
  analysisStatus: 'idle' | 'running' | 'completed' | 'error'
  analysisError?: string
  analysisResult: DemoAnalysisResult | null
  spatialPrompt: string
  setSpatialPrompt: (prompt: string) => void
  loadDemoScenes: () => Promise<void>
  toggleDemoScene: (sceneId: string) => void
  setAllDemoScenesSelected: (selected: boolean) => void
  addLiveScene: (scene: LiveScene) => void
  toggleLiveScene: (sceneId: string) => void
  setAllScenesSelected: (selected: boolean) => void
  clearSceneSelection: () => void
  startDemoAnalysis: () => Promise<DemoAnalysisResult>
}

const emptyProjectDraft: ProjectFormDraft = {
  name: '',
  region: '',
  projectType: '',
  projectStage: '',
  description: '',
}

export function createProjectFormDraft(project: Project): ProjectFormDraft {
  return {
    name: project.name,
    region: project.region,
    projectType: project.project_type,
    projectStage: project.project_stage,
    description: project.description ?? '',
  }
}

const CreationFlowContext = createContext<CreationFlowValue | null>(null)

export function CreationFlowProvider({ children }: { children: ReactNode }) {
  const { project } = useProjectSession()
  const initializedDraft = useRef<ProjectFormDraft | null>(null)
  const [editedDraft, setEditedDraft] = useState<ProjectFormDraft | null>(null)
  const [demoScenes, setDemoScenes] = useState<DemoScene[]>(fallbackDemoScenes)
  const [liveScenes, setLiveScenes] = useState<LiveScene[]>([])
  const [selectedSceneIds, setSelectedSceneIds] = useState<string[]>(fallbackDemoScenes.filter((scene) => scene.default_selected).map((scene) => scene.id))
  const [selectedLiveIds, setSelectedLiveIds] = useState<string[]>([])
  const [sceneCatalogStatus, setSceneCatalogStatus] = useState<CreationFlowValue['sceneCatalogStatus']>('idle')
  const [sceneCatalogError, setSceneCatalogError] = useState<string>()
  const [analysisStatus, setAnalysisStatus] = useState<CreationFlowValue['analysisStatus']>('idle')
  const [analysisError, setAnalysisError] = useState<string>()
  const [analysisResult, setAnalysisResult] = useState<DemoAnalysisResult | null>(null)
  const [spatialPrompt, setSpatialPrompt] = useState('保留原空间结构与尺度，更新为明亮、低碳、可逆施工的现代室内空间')
  const sceneRequest = useRef<Promise<void> | null>(null)

  if (!initializedDraft.current && !editedDraft && project) {
    initializedDraft.current = createProjectFormDraft(project)
  }

  const projectDraft = editedDraft ?? initializedDraft.current ?? emptyProjectDraft

  const loadDemoScenes = useCallback(async () => {
    if (sceneRequest.current) return sceneRequest.current
    setSceneCatalogStatus('loading')
    sceneRequest.current = fetchDemoScenes()
      .then((scenes) => {
        setDemoScenes(scenes)
        setSelectedSceneIds((current) => current.length ? current : scenes.filter((scene) => scene.default_selected).map((scene) => scene.id))
        setSceneCatalogError(undefined)
        setSceneCatalogStatus('ready')
      })
      .catch((error: unknown) => {
        setDemoScenes(fallbackDemoScenes)
        setSelectedSceneIds((current) => current.length ? current : fallbackDemoScenes.filter((scene) => scene.default_selected).map((scene) => scene.id))
        setSceneCatalogError(error instanceof Error ? error.message : '无法连接后端素材接口')
        setSceneCatalogStatus('fallback')
      })
      .finally(() => {
        sceneRequest.current = null
      })
    return sceneRequest.current
  }, [])

  const startDemoAnalysis = useCallback(async () => {
    const demoIds = selectedSceneIds.filter((id) => !id.startsWith('live_'))
    if (!demoIds.length) {
      if (selectedLiveIds.length) {
        throw new Error('实拍分析待后端接入，请同时选择下方样例场景，或等待上传接口完成后再仅用实拍分析。')
      }
      throw new Error('请至少选择一个样例场景')
    }
    setAnalysisStatus('running')
    setAnalysisError(undefined)
    try {
      const result = await runDemoAnalysis({
        scene_ids: demoIds,
        user_goal: projectDraft.description || '评估空间构件的再利用机会，并提出低碳翻新方案',
        region: projectDraft.region || undefined,
        spatial_prompt: spatialPrompt,
        include_web: false,
      })
      setAnalysisResult(result)
      setAnalysisStatus('completed')
      return result
    } catch (error) {
      const message = error instanceof Error ? error.message : '分析任务启动失败'
      setAnalysisError(message)
      setAnalysisStatus('error')
      throw error
    }
  }, [projectDraft.description, projectDraft.region, selectedLiveIds.length, selectedSceneIds, spatialPrompt])

  const value = useMemo<CreationFlowValue>(() => ({
    projectDraft,
    updateProjectDraft: (patch) => setEditedDraft((current) => ({
      ...(current ?? initializedDraft.current ?? emptyProjectDraft),
      ...patch,
    })),
    demoScenes,
    liveScenes,
    selectedSceneIds,
    selectedLiveIds,
    sceneCatalogStatus,
    sceneCatalogError,
    analysisStatus,
    analysisError,
    analysisResult,
    spatialPrompt,
    setSpatialPrompt,
    loadDemoScenes,
    toggleDemoScene: (sceneId) => setSelectedSceneIds((current) => (
      current.includes(sceneId) ? current.filter((id) => id !== sceneId) : [...current, sceneId]
    )),
    setAllDemoScenesSelected: (selected) => setSelectedSceneIds(selected ? demoScenes.map((scene) => scene.id) : []),
    addLiveScene: (scene) => {
      setLiveScenes((current) => {
        if (current.some((item) => item.id === scene.id)) return current
        return [scene, ...current]
      })
      setSelectedLiveIds((current) => (current.includes(scene.id) ? current : [scene.id, ...current]))
    },
    toggleLiveScene: (sceneId) => setSelectedLiveIds((current) => (
      current.includes(sceneId) ? current.filter((id) => id !== sceneId) : [...current, sceneId]
    )),
    setAllScenesSelected: (selected) => {
      setSelectedSceneIds(selected ? demoScenes.map((scene) => scene.id) : [])
      setSelectedLiveIds(selected ? liveScenes.map((scene) => scene.id) : [])
    },
    clearSceneSelection: () => {
      setSelectedSceneIds([])
      setSelectedLiveIds([])
    },
    startDemoAnalysis,
  }), [
    analysisError,
    analysisResult,
    analysisStatus,
    demoScenes,
    liveScenes,
    loadDemoScenes,
    projectDraft,
    sceneCatalogError,
    sceneCatalogStatus,
    selectedLiveIds,
    selectedSceneIds,
    spatialPrompt,
    startDemoAnalysis,
  ])

  return <CreationFlowContext.Provider value={value}>{children}</CreationFlowContext.Provider>
}

export function useCreationFlow() {
  const context = useContext(CreationFlowContext)
  if (!context) throw new Error('useCreationFlow must be used inside CreationFlowProvider')
  return context
}
