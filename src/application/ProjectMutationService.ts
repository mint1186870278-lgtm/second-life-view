import type { ProjectId, SceneId } from '../domain'

export interface RenameSceneCommand {
  project_id: ProjectId
  scene_id: SceneId
  name: string
}

export interface RenameSceneResult {
  scene_id: SceneId
  name: string
}

/**
 * Application command boundary for confirmed Project mutations.
 * It defines no transport or backend endpoint semantics.
 */
export interface ProjectMutationService {
  renameScene(command: RenameSceneCommand): Promise<RenameSceneResult>
}
