// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { WORKSPACE_NAVIGATION_ITEMS } from '../app/workspaceNavigation'
import { WorkspaceSidebar } from './WorkspaceShell'

afterEach(cleanup)

describe('Workspace navigation', () => {
  it('renders the two authoritative entries from a typed model and delegates destination handling', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(
      <WorkspaceSidebar
        items={WORKSPACE_NAVIGATION_ITEMS}
        activeDestination="view"
        onNavigate={onNavigate}
      />,
    )

    const view = screen.getByRole('button', { name: '再生视图' })
    const review = screen.getByRole('button', { name: '项目审查' })
    expect(screen.getAllByRole('button')).toHaveLength(2)
    expect(view.getAttribute('aria-current')).toBe('page')
    expect(review.hasAttribute('aria-current')).toBe(false)

    await user.click(review)
    expect(onNavigate).toHaveBeenCalledWith('review')
  })
})
