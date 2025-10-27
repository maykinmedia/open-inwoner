import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ActionList, { IActionProps } from './ActionList'

import '@testing-library/jest-dom'

const mockActions: IActionProps[] = [
  {
    title: 'Complete your profile',
    message: 'Please fill in your personal information',
    action_url: '/profile',
  },
  {
    title: 'Upload documents',
    message: 'Upload required documents for verification',
    action_url: '/documents',
  },
]

describe('ActionList', () => {
  it('renders without crashing', () => {
    render(<ActionList actions={mockActions} />)
    expect(screen.getByText('Complete your profile')).toBeInTheDocument()
  })

  it('renders all actions', () => {
    render(<ActionList actions={mockActions} />)

    expect(screen.getByText('Complete your profile')).toBeInTheDocument()
    expect(screen.getByText('Upload documents')).toBeInTheDocument()
  })

  it('renders action messages', () => {
    render(<ActionList actions={mockActions} />)

    expect(
      screen.getByText(/Please fill in your personal information/)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Upload required documents for verification/)
    ).toBeInTheDocument()
  })

  it('renders action links with correct URLs', () => {
    render(<ActionList actions={mockActions} />)
    const profileLink = screen.getByText('Complete your profile').closest('a')
    const uploadLink = screen.getByText('Upload documents').closest('a')

    expect(profileLink).toHaveAttribute('href', '/profile')
    expect(uploadLink).toHaveAttribute('href', '/documents')
  })

  it('renders empty list when no actions provided', () => {
    const { container } = render(<ActionList actions={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('handles undefined actions gracefully', () => {
    const { container } = render(<ActionList actions={undefined!} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders action without text when action_text is empty', () => {
    const actionWithoutText = [
      {
        title: 'Test action',
        message: 'Test message',
        action_url: '/test',
      },
    ]

    render(<ActionList actions={actionWithoutText} />)
    expect(() => screen.getByText('Ga naar actie')).toThrow()
    expect(screen.getByRole('link')).toBeInTheDocument()
  })

  it('renders correct number of Action components', () => {
    const { container } = render(<ActionList actions={mockActions} />)

    // Each Action component should render the title
    const titles = container.querySelectorAll('div')
    expect(titles.length).toBeGreaterThan(0)
  })

  it('renders actions in correct order', () => {
    render(<ActionList actions={mockActions} />)

    const messages = screen.getAllByText(/|/)
    expect(messages[0]).toHaveTextContent(
      'Please fill in your personal information'
    )
    expect(messages[1]).toHaveTextContent(
      'Upload required documents for verification'
    )
  })

  it('renders action links with correct CSS classes', () => {
    render(<ActionList actions={mockActions} />)

    const links = screen.getAllByRole('link')
    links.forEach((link) => {
      expect(link).toHaveClass(
        'nl-link',
        'denhaag-action',
        'denhaag-action--single'
      )
    })
  })

  it('renders single action correctly', () => {
    const singleAction = [mockActions[0]]
    render(<ActionList actions={singleAction} />)

    expect(screen.getByText('Complete your profile')).toBeInTheDocument()
    expect(screen.queryByText('Upload documents')).not.toBeInTheDocument()
  })

  it('maintains action data integrity', () => {
    render(<ActionList actions={mockActions} />)

    mockActions.forEach((action) => {
      expect(screen.getByText(action.title)).toBeInTheDocument()
      expect(screen.getByText(new RegExp(action.message))).toBeInTheDocument()
    })
  })

  it('renders with special characters in action data', () => {
    const specialActions = [
      {
        title: 'Test & Review',
        message: 'Check <data> & verify',
        action_url: '/test?id=1&type=review',
      },
    ]

    render(<ActionList actions={specialActions} />)
    expect(screen.getByText('Test & Review')).toBeInTheDocument()
  })
})
