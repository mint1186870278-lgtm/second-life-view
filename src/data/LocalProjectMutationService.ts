import type {
  ProjectMutationService,
  RenameSceneCommand,
  RenameSceneResult,
} from '../application'

/**
 * Deterministic Phase 1B demo command implementation.
 * It owns no canonical collection; ProjectSession applies the confirmed result.
 */
export class LocalProjectMutationService implements ProjectMutationService {
  async renameScene(command: RenameSceneCommand): Promise<RenameSceneResult> {
    const name = command.name.trim()
    if (!name) throw new Error('场景名称不能为空')
    return { scene_id: command.scene_id, name }
  }
}
