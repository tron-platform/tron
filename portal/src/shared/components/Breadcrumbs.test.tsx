import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Breadcrumbs } from './Breadcrumbs'

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Breadcrumbs', () => {
  it('renders breadcrumb items', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Applications', path: '/applications' },
      { label: 'My App' },
    ]

    renderWithRouter(<Breadcrumbs items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Applications')).toBeInTheDocument()
    expect(screen.getByText('My App')).toBeInTheDocument()
  })

  it('renders links for items with paths (except last)', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Applications', path: '/applications' },
      { label: 'My App' },
    ]

    renderWithRouter(<Breadcrumbs items={items} />)

    const homeLink = screen.getByText('Home').closest('a')
    const applicationsLink = screen.getByText('Applications').closest('a')
    const lastItem = screen.getByText('My App').closest('span')

    expect(homeLink).toBeInTheDocument()
    expect(homeLink).toHaveAttribute('href', '/')
    expect(applicationsLink).toBeInTheDocument()
    expect(applicationsLink).toHaveAttribute('href', '/applications')
    expect(lastItem).toBeInTheDocument()
  })

  it('renders last item as non-clickable span', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Current Page' },
    ]

    renderWithRouter(<Breadcrumbs items={items} />)

    const lastItem = screen.getByText('Current Page').closest('span')
    expect(lastItem).toBeInTheDocument()
    expect(lastItem).toHaveClass('text-neutral-900', 'font-semibold')
  })

  it('returns null when items array is empty', () => {
    const { container } = renderWithRouter(<Breadcrumbs items={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders single item without separator', () => {
    const items = [{ label: 'Home' }]

    const { container } = renderWithRouter(<Breadcrumbs items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    // Single item should not have any links (no path provided)
    const links = container.querySelectorAll('a')
    expect(links.length).toBe(0)
  })
})
