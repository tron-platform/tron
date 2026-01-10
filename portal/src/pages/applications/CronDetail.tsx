import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, X, Clock, Trash2 } from 'lucide-react'
import { cronsApi, instancesApi, applicationsApi } from '../../services/api'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'
import DataTable from '../../components/DataTable'
import type { CronJob } from '../../types'

function CronDetail() {
  const { uuid: applicationUuid, instanceUuid, componentUuid } = useParams<{
    uuid: string
    instanceUuid: string
    componentUuid: string
  }>()

  const { data: component } = useQuery({
    queryKey: ['cron', componentUuid],
    queryFn: () => cronsApi.get(componentUuid!),
    enabled: !!componentUuid,
  })

  const { data: instance } = useQuery({
    queryKey: ['instances', instanceUuid],
    queryFn: () => instancesApi.get(instanceUuid!),
    enabled: !!instanceUuid,
  })

  const { data: application } = useQuery({
    queryKey: ['application', applicationUuid],
    queryFn: () => applicationsApi.get(applicationUuid!),
    enabled: !!applicationUuid,
  })

  const [refreshInterval, setRefreshInterval] = useState<number>(10000) // Default: 10 seconds
  const queryClient = useQueryClient()

  const { data: jobs = [], isLoading: isLoadingJobs } = useQuery({
    queryKey: ['cron-jobs', componentUuid],
    queryFn: () => cronsApi.getJobs(componentUuid!),
    enabled: !!componentUuid,
    refetchInterval: refreshInterval > 0 ? refreshInterval : false,
  })

  const deleteJobMutation = useMutation({
    mutationFn: (jobName: string) => cronsApi.deleteJob(componentUuid!, jobName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cron-jobs', componentUuid] })
    },
  })

  const handleDeleteJob = (jobName: string) => {
    if (confirm(`Are you sure you want to delete the job "${jobName}"? This action cannot be undone.`)) {
      deleteJobMutation.mutate(jobName)
    }
  }

  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [isLogsModalOpen, setIsLogsModalOpen] = useState(false)
  const [isLiveTail, setIsLiveTail] = useState(true)
  const logsContainerRef = useRef<HTMLPreElement>(null)

  const { data: jobLogs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['cron-job-logs', componentUuid, selectedJob],
    queryFn: () => cronsApi.getJobLogs(componentUuid!, selectedJob!),
    enabled: !!selectedJob && isLogsModalOpen && !!componentUuid,
    refetchInterval: isLiveTail ? 2000 : false,
  })

  // Scroll automático para o final quando os logs mudarem
  useEffect(() => {
    if (isLogsModalOpen && logsContainerRef.current) {
      setTimeout(() => {
        if (logsContainerRef.current) {
          logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
        }
      }, 100)
    }
  }, [jobLogs?.logs, isLogsModalOpen, isLiveTail])

  useEffect(() => {
    if (isLiveTail && logsContainerRef.current && jobLogs?.logs) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [jobLogs?.logs, isLiveTail])

  const formatAge = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      return `${minutes}m`
    } else if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}h${minutes}m`
    } else {
      const days = Math.floor(seconds / 86400)
      const hours = Math.floor((seconds % 86400) / 3600)
      return `${days}d${hours}h`
    }
  }

  const formatDuration = (seconds: number | null): string => {
    if (seconds === null) return '-'
    if (seconds < 60) {
      return `${seconds}s`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${minutes}m ${secs}s`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}h ${minutes}m`
    }
  }

  const formatDateTime = (dateTime: string | null): string => {
    if (!dateTime) return '-'
    try {
      const date = new Date(dateTime)
      return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return dateTime
    }
  }

  const schedule = (component?.settings as any)?.schedule || '-'

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Applications', path: '/applications' },
          { label: application?.name || 'Application' },
          { label: instance?.environment.name || 'Environment', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: 'Components', path: `/applications/${applicationUuid}/instances/${instanceUuid}/components` },
          { label: component?.name || 'Cron' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader
          title={component?.name || 'Cron Details'}
          description={`Schedule: ${schedule === '-' ? '-' : schedule}`}
        />
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-neutral-700">
            <span>Refresh:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="input pr-10"
            >
              <option value={0}>Disabled</option>
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
            </select>
          </label>
        </div>
      </div>

      <DataTable<CronJob>
        columns={[
          {
            key: 'name',
            label: 'Job Name',
            render: (job) => (
              <div className="text-sm font-medium text-neutral-900">{job.name}</div>
            ),
          },
          {
            key: 'status',
            label: 'Status',
            render: (job) => {
              const statusClasses: Record<string, string> = {
                Succeeded: 'badge-success',
                Failed: 'badge-error',
                Active: 'badge-warning',
                Unknown: 'badge bg-neutral-100 text-neutral-800 border-neutral-200',
              }
              const badgeClass = statusClasses[job.status] || statusClasses.Unknown
              return (
                <span className={badgeClass}>
                  {job.status}
                </span>
              )
            },
          },
          {
            key: 'start_time',
            label: 'Start Time',
            render: (job) => (
              <div className="text-sm text-neutral-700">
                {formatDateTime(job.start_time)}
              </div>
            ),
          },
          {
            key: 'completion_time',
            label: 'Completion Time',
            render: (job) => (
              <div className="text-sm text-neutral-700">
                {formatDateTime(job.completion_time)}
              </div>
            ),
          },
          {
            key: 'duration',
            label: 'Duration',
            render: (job) => (
              <div className="text-sm text-neutral-700">
                {formatDuration(job.duration_seconds)}
              </div>
            ),
          },
          {
            key: 'age',
            label: 'Age',
            render: (job) => (
              <div className="text-sm text-neutral-700 flex items-center gap-1">
                <Clock size={14} className="text-neutral-400" />
                {formatAge(job.age_seconds)}
              </div>
            ),
          },
          {
            key: 'counts',
            label: 'Counts',
            render: (job) => (
              <div className="text-sm text-neutral-700">
                {job.succeeded > 0 && (
                  <span className="text-green-600">✓ {job.succeeded}</span>
                )}
                {job.failed > 0 && (
                  <span className={`text-red-600 ${job.succeeded > 0 ? ' ml-2' : ''}`}>
                    ✗ {job.failed}
                  </span>
                )}
                {job.active > 0 && (
                  <span className={`text-yellow-600 ${(job.succeeded > 0 || job.failed > 0) ? ' ml-2' : ''}`}>
                    ⏳ {job.active}
                  </span>
                )}
                {job.succeeded === 0 && job.failed === 0 && job.active === 0 && (
                  <span className="text-neutral-400">-</span>
                )}
              </div>
            ),
          },
        ]}
        data={jobs}
        isLoading={isLoadingJobs}
        emptyMessage="No job executions found"
        loadingColor="blue"
        getRowKey={(job) => job.name}
        actions={(job) => {
          const actions = [
            {
              label: 'View Logs',
              icon: <FileText size={14} />,
              onClick: () => {
                setSelectedJob(job.name)
                setIsLogsModalOpen(true)
              },
              variant: 'default' as const,
            },
          ]

          // Adicionar ação de delete apenas se o status for Active
          if (job.status === 'Active') {
            actions.push({
              label: 'Delete',
              icon: <Trash2 size={14} />,
              onClick: () => handleDeleteJob(job.name),
              variant: 'danger',
            } as any)
          }

          return actions
        }}
      />

      {/* Logs Modal */}
      {isLogsModalOpen && selectedJob && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-soft-lg max-w-4xl w-full border border-slate-200/60 animate-zoom-in max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b border-slate-200/60 bg-slate-50/50">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">Job Logs</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Job: {selectedJob}
                  {jobLogs?.pod_name && ` • Pod: ${jobLogs.pod_name}`}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={isLiveTail}
                    onChange={(e) => setIsLiveTail(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Live Tail</span>
                </label>
                <button
                  onClick={() => {
                    setIsLogsModalOpen(false)
                    setSelectedJob(null)
                  }}
                  className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded-md transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-5 flex-1 overflow-auto">
              {isLoadingLogs ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : jobLogs?.logs ? (
                <pre
                  ref={logsContainerRef}
                  className="bg-slate-900 rounded-lg p-4 text-slate-100 font-mono text-xs whitespace-pre-wrap overflow-x-auto"
                  style={{ maxHeight: 'calc(90vh - 200px)' }}
                >
                  {jobLogs.logs}
                </pre>
              ) : (
                <div className="bg-slate-900 rounded-lg p-4 text-slate-100 font-mono text-xs">
                  <p className="text-slate-400">No logs available for this job execution.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CronDetail

