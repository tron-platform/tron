import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ComponentForm } from './ComponentForm'
import type { ComponentFormData } from './types'

// Mock dos sub-formulários
vi.mock('./WebappForm', () => ({
  WebappForm: ({ settings, onChange }: any) => (
    <div data-testid="webapp-form">
      <input
        data-testid="webapp-exposure"
        value={settings?.exposure?.visibility || ''}
        onChange={(e) => onChange({ ...settings, exposure: { visibility: e.target.value } })}
      />
    </div>
  ),
}))

vi.mock('./CronForm', () => ({
  CronForm: ({ settings, onChange }: any) => (
    <div data-testid="cron-form">
      <input
        data-testid="cron-schedule"
        value={settings?.schedule || ''}
        onChange={(e) => onChange({ ...settings, schedule: e.target.value })}
      />
    </div>
  ),
}))

vi.mock('./WorkerForm', () => ({
  WorkerForm: ({ settings, onChange }: any) => (
    <div data-testid="worker-form">
      <input
        data-testid="worker-metrics"
        value={settings?.custom_metrics?.enabled ? 'enabled' : 'disabled'}
        onChange={(e) =>
          onChange({
            ...settings,
            custom_metrics: { enabled: e.target.value === 'enabled' },
          })
        }
      />
    </div>
  ),
}))

describe('ComponentForm', () => {
  const mockOnChange = vi.fn()
  const mockOnRemove = vi.fn()

  const webappComponent: ComponentFormData = {
    name: 'my-webapp',
    type: 'webapp',
    enabled: true,
    visibility: 'public',
    url: 'https://example.com',
    settings: {
      exposure: {
        visibility: 'public',
        type: 'http',
      },
    },
  }

  const cronComponent: ComponentFormData = {
    name: 'my-cron',
    type: 'cron',
    enabled: true,
    visibility: 'cluster',
    settings: {
      schedule: '0 0 * * *',
    },
  }

  const workerComponent: ComponentFormData = {
    name: 'my-worker',
    type: 'worker',
    enabled: true,
    visibility: 'cluster',
    settings: {
      custom_metrics: {
        enabled: false,
      },
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders component name input', () => {
    render(
      <ComponentForm component={webappComponent} onChange={mockOnChange} />
    )

    const nameInput = screen.getByPlaceholderText('my-component')
    expect(nameInput).toBeInTheDocument()
    expect(nameInput).toHaveValue('my-webapp')
  })

  it('removes spaces from component name', () => {
    render(
      <ComponentForm component={webappComponent} onChange={mockOnChange} />
    )

    const nameInput = screen.getByPlaceholderText('my-component')
    fireEvent.change(nameInput, { target: { value: 'my component name' } })

    expect(mockOnChange).toHaveBeenCalledWith({
      ...webappComponent,
      name: 'mycomponentname',
    })
  })

  it('renders enabled/disabled radio buttons', () => {
    render(
      <ComponentForm component={webappComponent} onChange={mockOnChange} />
    )

    const enabledRadio = screen.getByLabelText('Enabled')
    const disabledRadio = screen.getByLabelText('Disabled')

    expect(enabledRadio).toBeInTheDocument()
    expect(disabledRadio).toBeInTheDocument()
    expect(enabledRadio).toBeChecked()
  })

  it('calls onChange when enabled state changes', () => {
    render(
      <ComponentForm component={webappComponent} onChange={mockOnChange} />
    )

    const disabledRadio = screen.getByLabelText('Disabled')
    fireEvent.click(disabledRadio)

    expect(mockOnChange).toHaveBeenCalledWith({
      ...webappComponent,
      enabled: false,
    })
  })

  it('renders remove button when showRemoveButton is true', () => {
    render(
      <ComponentForm
        component={webappComponent}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
        showRemoveButton={true}
      />
    )

    const removeButton = screen.getByRole('button')
    expect(removeButton).toBeInTheDocument()
  })

  it('calls onRemove when remove button is clicked', () => {
    render(
      <ComponentForm
        component={webappComponent}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    )

    const removeButton = screen.getByRole('button')
    fireEvent.click(removeButton)

    expect(mockOnRemove).toHaveBeenCalled()
  })

  it('hides remove button when showRemoveButton is false', () => {
    render(
      <ComponentForm
        component={webappComponent}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
        showRemoveButton={false}
      />
    )

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('renders WebappForm for webapp components', () => {
    render(
      <ComponentForm component={webappComponent} onChange={mockOnChange} />
    )

    expect(screen.getByTestId('webapp-form')).toBeInTheDocument()
  })

  it('renders CronForm for cron components', () => {
    render(
      <ComponentForm component={cronComponent} onChange={mockOnChange} />
    )

    expect(screen.getByTestId('cron-form')).toBeInTheDocument()
  })

  it('renders WorkerForm for worker components', () => {
    render(
      <ComponentForm component={workerComponent} onChange={mockOnChange} />
    )

    expect(screen.getByTestId('worker-form')).toBeInTheDocument()
  })

  it('displays component name as read-only when isEditing is true', () => {
    render(
      <ComponentForm
        component={webappComponent}
        onChange={mockOnChange}
        isEditing={true}
      />
    )

    const nameDisplay = screen.getByText('my-webapp')
    expect(nameDisplay).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('my-component')).not.toBeInTheDocument()
  })

  it('shows message that name cannot be changed when editing', () => {
    render(
      <ComponentForm
        component={webappComponent}
        onChange={mockOnChange}
        isEditing={true}
      />
    )

    expect(
      screen.getByText(/component name cannot be changed after creation/i)
    ).toBeInTheDocument()
  })

  it('forces visibility to cluster when Gateway API is not available', async () => {
    const componentWithPublicVisibility: ComponentFormData = {
      ...webappComponent,
      visibility: 'public',
      settings: {
        exposure: {
          visibility: 'public',
          type: 'http',
        },
      },
    }

    const { rerender } = render(
      <ComponentForm
        component={componentWithPublicVisibility}
        onChange={mockOnChange}
        hasGatewayApi={true}
      />
    )

    // Component should keep public visibility when Gateway API is available
    expect(mockOnChange).not.toHaveBeenCalled()

    // Now disable Gateway API
    rerender(
      <ComponentForm
        component={componentWithPublicVisibility}
        onChange={mockOnChange}
        hasGatewayApi={false}
      />
    )

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          visibility: 'cluster',
        })
      )
    })
  })
})
