// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Select } from './FormControls'

afterEach(cleanup)

describe('Select', () => {
  it('renders caller-provided generic options including disabled state', () => {
    render(
      <Select
        aria-label="generic choice"
        options={[
          { value: 'alpha', label: 'Alpha' },
          { value: 'beta', label: 'Beta', disabled: true },
        ]}
      />,
    )

    const options = screen.getAllByRole('option')
    expect(options.map((option) => option.textContent)).toEqual(['请选择', 'Alpha', 'Beta'])
    expect((options[2] as HTMLOptionElement).disabled).toBe(true)
  })
})
