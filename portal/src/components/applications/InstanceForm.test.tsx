import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { InstanceForm } from './InstanceForm'
import * as api from '../../services/api'

// Mock da API
vi.mock('../../services/api', () => ({
  environmentsApi: {
    list: vi.fn(),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('InstanceForm', () => {
  const mockEnvironments = [
    { uuid: 'env-1', name: 'Development' },
    { uuid: 'env-2', name: 'Production' },
  ]

  const defaultData = {
    environment_uuid: '',
    image: '',
    version: '',
  }

  beforeEach(() => {
    vi.mocked(api.environmentsApi.list).mockResolvedValue(mockEnvironments)
  })

  it('renders form fields', async () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    // Wait for environments to load
    await screen.findByText('Select an environment')

    // Find elements by their labels or placeholders
    // Use getAllByText and check that at least one exists, or be more specific
    const environmentLabels = screen.getAllByText(/environment/i)
    expect(environmentLabels.length).toBeGreaterThan(0)
    expect(screen.getByPlaceholderText('my-image')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('v1.0.0')).toBeInTheDocument()

    // Also verify the select element exists
    const selectElement = screen.getByText('Select an environment').closest('select')
    expect(selectElement).toBeInTheDocument()
  })

  it('displays info card by default', () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText(/instance represents a specific deployment/i)).toBeInTheDocument()
  })

  it('hides info card when showInfoCard is false', () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} showInfoCard={false} />,
      { wrapper: createWrapper() }
    )

    expect(screen.queryByText(/instance represents a specific deployment/i)).not.toBeInTheDocument()
  })

  it('calls onChange when environment is selected', async () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    // Wait for environments to load
    await screen.findByText('Development')

    // Find select by finding the option text, then get the parent select
    const developmentOption = screen.getByText('Development')
    const environmentSelect = developmentOption.closest('select') as HTMLSelectElement

    fireEvent.change(environmentSelect, { target: { value: 'env-1' } })

    expect(onChange).toHaveBeenCalledWith({
      ...defaultData,
      environment_uuid: 'env-1',
    })
  })

  it('calls onChange when image is entered', async () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    // Wait for form to render
    await screen.findByPlaceholderText('my-image')

    const imageInput = screen.getByPlaceholderText('my-image')
    fireEvent.change(imageInput, { target: { value: 'my-image' } })

    expect(onChange).toHaveBeenCalledWith({
      ...defaultData,
      image: 'my-image',
    })
  })

  it('calls onChange when version is entered', async () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    // Wait for form to render
    await screen.findByPlaceholderText('v1.0.0')

    const versionInput = screen.getByPlaceholderText('v1.0.0')
    fireEvent.change(versionInput, { target: { value: 'v1.0.0' } })

    expect(onChange).toHaveBeenCalledWith({
      ...defaultData,
      version: 'v1.0.0',
    })
  })

  it('displays current data values', async () => {
    const onChange = vi.fn()
    const data = {
      environment_uuid: 'env-1',
      image: 'my-image',
      version: 'v1.0.0',
    }

    render(
      <InstanceForm data={data} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    // Wait for environments to load
    await screen.findByText('Development')

    // Find select by its value (it should show "Development" as selected)
    const environmentSelect = screen.getByDisplayValue('Development') as HTMLSelectElement
    const imageInput = screen.getByDisplayValue('my-image')
    const versionInput = screen.getByDisplayValue('v1.0.0')

    expect(environmentSelect.value).toBe('env-1')
    expect(imageInput).toHaveValue('my-image')
    expect(versionInput).toHaveValue('v1.0.0')
  })

  it('renders environment options', async () => {
    const onChange = vi.fn()
    render(
      <InstanceForm data={defaultData} onChange={onChange} />,
      { wrapper: createWrapper() }
    )

    await screen.findByText('Development')
    expect(screen.getByText('Development')).toBeInTheDocument()
    expect(screen.getByText('Production')).toBeInTheDocument()
  })
})
