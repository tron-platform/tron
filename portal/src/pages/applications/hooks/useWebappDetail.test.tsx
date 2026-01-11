import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebappDetail } from './useWebappDetail'

// Mock das dependências
const mockUseWebappPods = vi.fn()
const mockUseDeleteWebappPod = vi.fn()
const mockUseWebappPodLogs = vi.fn()
const mockUseExecWebappPodCommand = vi.fn()

vi.mock('../../../features/components', () => ({
  useWebappPods: () => mockUseWebappPods(),
  useDeleteWebappPod: () => mockUseDeleteWebappPod(),
  useWebappPodLogs: () => mockUseWebappPodLogs(),
  useExecWebappPodCommand: () => mockUseExecWebappPodCommand(),
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
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useWebappDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with default state', async () => {
    mockUseWebappPods.mockReturnValue({
      data: [],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: vi.fn(),
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    expect(result.current.selectedPod).toBe(null)
    expect(result.current.isLogsModalOpen).toBe(false)
    expect(result.current.isConsoleModalOpen).toBe(false)
    expect(result.current.isLiveTail).toBe(true)
    expect(result.current.commandOutput).toEqual([])
    expect(result.current.currentCommand).toBe('')
  })

  it('should handle viewing logs', async () => {
    mockUseWebappPods.mockReturnValue({
      data: [{ name: 'pod-1' }, { name: 'pod-2' }],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: { logs: ['log line 1', 'log line 2'] },
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: vi.fn(),
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    result.current.handleViewLogs('pod-1')

    await waitFor(() => {
      expect(result.current.selectedPod).toBe('pod-1')
      expect(result.current.isLogsModalOpen).toBe(true)
    })
  })

  it('should handle opening console', async () => {
    mockUseWebappPods.mockReturnValue({
      data: [{ name: 'pod-1' }],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: vi.fn(),
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    result.current.handleOpenConsole('pod-1')

    await waitFor(() => {
      expect(result.current.selectedPod).toBe('pod-1')
      expect(result.current.isConsoleModalOpen).toBe(true)
      expect(result.current.commandOutput).toEqual([])
    })
  })

  it('should handle closing modals', async () => {
    mockUseWebappPods.mockReturnValue({
      data: [],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: vi.fn(),
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    // Open logs modal first
    result.current.handleViewLogs('pod-1')
    await waitFor(() => {
      expect(result.current.isLogsModalOpen).toBe(true)
    })

    // Close logs modal
    result.current.handleCloseLogsModal()
    await waitFor(() => {
      expect(result.current.isLogsModalOpen).toBe(false)
      expect(result.current.selectedPod).toBe(null)
      expect(result.current.isLiveTail).toBe(true)
    })
  })

  it('should handle command submission', async () => {
    const mockMutate = vi.fn()
    const mockReset = vi.fn()

    mockUseWebappPods.mockReturnValue({
      data: [{ name: 'pod-1' }],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: mockReset,
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    // Wait for hook to initialize
    await waitFor(() => {
      expect(result.current.pods).toBeDefined()
    })

    // Open console first
    result.current.handleOpenConsole('pod-1')

    await waitFor(() => {
      expect(result.current.isConsoleModalOpen).toBe(true)
      expect(result.current.selectedPod).toBe('pod-1')
    })

    // Submit command
    result.current.handleCommandSubmit('ls -la')

    // Check that mutate was called
    expect(mockMutate).toHaveBeenCalledWith({
      uuid: 'component-1',
      podName: 'pod-1',
      command: ['ls', '-la'],
    })
  })

  it('should not submit empty commands', async () => {
    const mockMutate = vi.fn()

    mockUseWebappPods.mockReturnValue({
      data: [{ name: 'pod-1' }],
      isLoading: false,
    } as any)

    mockUseWebappPodLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    mockUseDeleteWebappPod.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    mockUseExecWebappPodCommand.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      reset: vi.fn(),
    } as any)

    const { result } = renderHook(
      () => useWebappDetail('component-1', 0),
      { wrapper: createWrapper() }
    )

    // Wait for hook to initialize
    await waitFor(() => {
      expect(result.current.pods).toBeDefined()
    })

    // Open console first
    result.current.handleOpenConsole('pod-1')

    await waitFor(() => {
      expect(result.current.isConsoleModalOpen).toBe(true)
    })

    // Try to submit empty command
    result.current.handleCommandSubmit('   ')

    // Should not call mutate
    expect(mockMutate).not.toHaveBeenCalled()
  })
})
