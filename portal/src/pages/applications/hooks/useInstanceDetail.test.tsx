import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { useInstanceDetail } from './useInstanceDetail'

// Mock das dependências
vi.mock('../../../features/instances', () => ({
  useInstance: vi.fn(),
  useUpdateInstance: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteInstance: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useSyncInstance: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
}))

vi.mock('../../../features/applications', () => ({
  useApplication: vi.fn(),
}))

vi.mock('../../../features/clusters', () => ({
  useClusters: vi.fn(),
}))

vi.mock('../../../features/components', () => ({
  useUpdateWebappComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteWebappComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useCreateWebappComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useUpdateCronComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteCronComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useCreateCronComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useUpdateWorkerComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteWorkerComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useCreateWorkerComponent: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
}))

// Mock do window.confirm
global.confirm = vi.fn(() => true)

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('useInstanceDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return instance data and grouped components', async () => {
    const { useInstance } = await import('../../../features/instances')
    const { useApplication } = await import('../../../features/applications')
    const { useClusters } = await import('../../../features/clusters')

    const mockInstance = {
      uuid: 'instance-1',
      image: 'my-image',
      version: 'v1.0.0',
      environment: { uuid: 'env-1', name: 'dev' },
      components: [
        { uuid: 'comp-1', type: 'webapp', name: 'webapp-1' },
        { uuid: 'comp-2', type: 'worker', name: 'worker-1' },
        { uuid: 'comp-3', type: 'cron', name: 'cron-1' },
      ],
    }

    vi.mocked(useInstance).mockReturnValue({
      data: mockInstance,
      isLoading: false,
    } as any)

    vi.mocked(useApplication).mockReturnValue({
      data: { uuid: 'app-1', name: 'My App' },
    } as any)

    vi.mocked(useClusters).mockReturnValue({
      data: [],
    } as any)

    const { result } = renderHook(
      () => useInstanceDetail('app-1', 'instance-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.instance).toEqual(mockInstance)
      expect(result.current.componentsByType.webapp).toHaveLength(1)
      expect(result.current.componentsByType.worker).toHaveLength(1)
      expect(result.current.componentsByType.cron).toHaveLength(1)
    })
  })

  it('should detect Gateway API availability', async () => {
    const { useInstance } = await import('../../../features/instances')
    const { useApplication } = await import('../../../features/applications')
    const { useClusters } = await import('../../../features/clusters')

    const mockInstance = {
      uuid: 'instance-1',
      environment: { uuid: 'env-1', name: 'dev' },
      components: [],
    }

    const mockClusters = [
      {
        uuid: 'cluster-1',
        environment: { uuid: 'env-1' },
        gateway: {
          api: { enabled: true, resources: ['HTTPRoute'] },
          reference: { namespace: 'gateway', name: 'main' },
        },
      },
    ]

    vi.mocked(useInstance).mockReturnValue({
      data: mockInstance,
      isLoading: false,
    } as any)

    vi.mocked(useApplication).mockReturnValue({
      data: { uuid: 'app-1' },
    } as any)

    vi.mocked(useClusters).mockReturnValue({
      data: mockClusters,
    } as any)

    const { result } = renderHook(
      () => useInstanceDetail('app-1', 'instance-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.hasGatewayApi).toBe(true)
      expect(result.current.gatewayResources).toContain('HTTPRoute')
      expect(result.current.gatewayReference).toEqual({
        namespace: 'gateway',
        name: 'main',
      })
    })
  })

  it('should handle missing instance', async () => {
    const { useInstance } = await import('../../../features/instances')
    const { useApplication } = await import('../../../features/applications')
    const { useClusters } = await import('../../../features/clusters')

    vi.mocked(useInstance).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    vi.mocked(useApplication).mockReturnValue({
      data: undefined,
    } as any)

    vi.mocked(useClusters).mockReturnValue({
      data: [],
    } as any)

    const { result } = renderHook(
      () => useInstanceDetail('app-1', 'instance-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.instance).toBeUndefined()
      expect(result.current.isLoadingInstance).toBe(true)
      expect(result.current.hasGatewayApi).toBe(false)
    })
  })
})
