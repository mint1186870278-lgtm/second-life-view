// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ProjectMutationService } from '../application'
import { FixtureProjectDataRepository } from '../data'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import { CreationFlowProvider, useCreationFlow } from './CreationFlowContext'
import { ProjectSessionProvider, useProjectSession } from './ProjectSessionContext'

afterEach(cleanup)

const repository = new FixtureProjectDataRepository(creationDemoGraph)

function CanonicalProbe() {
  const { project, scenes, renameScene, reload } = useProjectSession()
  return (
    <section>
      <output aria-label="canonical-project-name">{project?.name}</output>
      <output aria-label="first-scene-name">{scenes[0]?.name}</output>
      <button
        type="button"
        onClick={() => void renameScene(creationDemoGraph.scenes[0].scene_id, '服务确认名称')}
      >
        rename through service
      </button>
      <button onClick={reload}>reload project</button>
    </section>
  )
}

function DraftProbe() {
  const { projectDraft, updateProjectDraft } = useCreationFlow()
  return (
    <section>
      <output aria-label="draft-project-name">{projectDraft.name}</output>
      <button type="button" onClick={() => updateProjectDraft({ name: '未提交草稿名称' })}>
        edit draft
      </button>
    </section>
  )
}

describe('Project/session ownership boundaries', () => {
  it('provides canonical project data without CreationFlowProvider', async () => {
    const mutations: ProjectMutationService = {
      renameScene: vi.fn(async (command) => ({ scene_id: command.scene_id, name: command.name })),
    }
    render(
      <ProjectSessionProvider
        projectId={CREATION_DEMO_PROJECT_ID}
        repository={repository}
        mutations={mutations}
      >
        <CanonicalProbe />
      </ProjectSessionProvider>,
    )

    expect((await screen.findByLabelText('canonical-project-name')).textContent).toContain('HSBC MKK')
  })

  it('keeps the editable C01 draft separate from canonical Project truth', async () => {
    const user = userEvent.setup()
    const refreshingRepository = new FixtureProjectDataRepository(creationDemoGraph)
    vi.spyOn(refreshingRepository, 'getProject').mockImplementation(async (projectId) => {
      const project = await repository.getProject(projectId)
      return project ? { ...project } : null
    })
    const mutations: ProjectMutationService = {
      renameScene: vi.fn(async (command) => ({ scene_id: command.scene_id, name: command.name })),
    }
    render(
      <ProjectSessionProvider
        projectId={CREATION_DEMO_PROJECT_ID}
        repository={refreshingRepository}
        mutations={mutations}
      >
        <CanonicalProbe />
        <CreationFlowProvider><DraftProbe /></CreationFlowProvider>
      </ProjectSessionProvider>,
    )

    expect((await screen.findByLabelText('draft-project-name')).textContent).toContain('HSBC MKK')
    await user.click(screen.getByRole('button', { name: 'edit draft' }))
    expect(screen.getByLabelText('draft-project-name').textContent).toContain('未提交草稿名称')
    expect(screen.getByLabelText('canonical-project-name').textContent).toContain('HSBC MKK')

    await user.click(screen.getByRole('button', { name: 'reload project' }))
    await waitFor(() => {
      expect(screen.getByLabelText('draft-project-name').textContent).toContain('未提交草稿名称')
    })
  })

  it('routes Scene rename through the mutation service before updating the session snapshot', async () => {
    const user = userEvent.setup()
    const renameScene = vi.fn(async (command) => ({
      scene_id: command.scene_id,
      name: `confirmed:${command.name}`,
    }))
    render(
      <ProjectSessionProvider
        projectId={CREATION_DEMO_PROJECT_ID}
        repository={repository}
        mutations={{ renameScene }}
      >
        <CanonicalProbe />
      </ProjectSessionProvider>,
    )

    expect((await screen.findByLabelText('first-scene-name')).textContent).toContain('屋顶花园')
    await user.click(screen.getByRole('button', { name: 'rename through service' }))
    await waitFor(() => expect(renameScene).toHaveBeenCalledWith({
      project_id: CREATION_DEMO_PROJECT_ID,
      scene_id: creationDemoGraph.scenes[0].scene_id,
      name: '服务确认名称',
    }))
    expect(screen.getByLabelText('first-scene-name').textContent).toContain('confirmed:服务确认名称')
  })
})
