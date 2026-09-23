import { createContext, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
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

interface CreationFlowValue {
  projectDraft: ProjectFormDraft
  updateProjectDraft: (patch: Partial<ProjectFormDraft>) => void
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

  if (!initializedDraft.current && !editedDraft && project) {
    initializedDraft.current = createProjectFormDraft(project)
  }

  const projectDraft = editedDraft ?? initializedDraft.current ?? emptyProjectDraft

  const value = useMemo<CreationFlowValue>(() => ({
    projectDraft,
    updateProjectDraft: (patch) => setEditedDraft((current) => ({
      ...(current ?? initializedDraft.current ?? emptyProjectDraft),
      ...patch,
    })),
  }), [projectDraft])

  return <CreationFlowContext.Provider value={value}>{children}</CreationFlowContext.Provider>
}

export function useCreationFlow() {
  const context = useContext(CreationFlowContext)
  if (!context) throw new Error('useCreationFlow must be used inside CreationFlowProvider')
  return context
}
