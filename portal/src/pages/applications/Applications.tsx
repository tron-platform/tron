import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, Plus, Layers, Server } from 'lucide-react'
import { applicationsApi, instancesApi } from '../../services/api'
import type { Application, Instance } from '../../types'
import DataTable from '../../components/DataTable'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'

function Applications() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationsApi.list,
  })

  const { data: instances = [] } = useQuery({
    queryKey: ['instances'],
    queryFn: instancesApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: applicationsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
  })

  const handleDelete = (uuid: string) => {
    if (confirm('Are you sure you want to delete this application?')) {
      deleteMutation.mutate(uuid)
    }
  }

  const getInitials = (name: string): string => {
    const words = name.trim().split(/\s+/)
    if (words.length === 0) return ''
    if (words.length === 1) return words[0].substring(0, 2).toUpperCase()
    return (words[0][0] + words[words.length - 1][0]).toUpperCase()
  }

  const getColorFromName = (name: string): string => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-teal-500',
      'bg-orange-500',
      'bg-cyan-500',
    ]
    let hash = 0
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    return colors[Math.abs(hash) % colors.length]
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Applications', path: '/applications' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Applications" description="Manage applications" />
        <button
          onClick={() => navigate('/applications/new')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          <span>New Application</span>
        </button>
      </div>

      {/* Table */}
      <DataTable<Application>
        columns={[
          {
            key: 'avatar',
            label: '',
            width: '80px',
            render: (application) => (
              <div className={`w-10 h-10 rounded-full ${getColorFromName(application.name)} flex items-center justify-center text-white font-semibold text-sm`}>
                {getInitials(application.name)}
              </div>
            ),
          },
          {
            key: 'name',
            label: 'Name',
            render: (application) => (
              <div>
                <div className="text-sm font-medium text-slate-800">{application.name}</div>
                <small className="text-xs text-slate-500">{application.uuid}</small>
              </div>
            ),
          },
          {
            key: 'repository',
            label: 'Repository',
            render: (application) => (
              <div className="text-sm text-slate-600">{application.repository || '-'}</div>
            ),
          },
          {
            key: 'status',
            label: 'Status',
            render: (application) => (
              <div>
                {application.enabled ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Enabled
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Disabled
                  </span>
                )}
              </div>
            ),
          },
          {
            key: 'created_at',
            label: 'Creation Date',
            render: (application) => (
              <div className="text-sm text-slate-600">
                {new Date(application.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            ),
          },
          {
            key: 'updated_at',
            label: 'Update Date',
            render: (application) => (
              <div className="text-sm text-slate-600">
                {new Date(application.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            ),
          },
        ]}
        data={applications}
        isLoading={isLoading}
        emptyMessage="No applications found"
        loadingColor="blue"
        getRowKey={(application) => application.uuid}
        actions={(application) => {
          // Filtrar instâncias desta aplicação
          const applicationInstances = instances.filter(
            (instance: Instance) => instance.application.uuid === application.uuid
          )

          // Construir array de ações
          const actions = [
            {
              label: 'New Instance',
              icon: <Layers size={14} />,
              onClick: () => navigate(`/applications/${application.uuid}/instances/new`),
              variant: 'default' as const,
            },
          ]

          // Adicionar instâncias existentes
          if (applicationInstances.length > 0) {
            applicationInstances.forEach((instance: Instance) => {
              actions.push({
                label: `Instance: ${instance.environment.name}`,
                icon: <Server size={14} />,
                onClick: () => navigate(`/applications/${application.uuid}/instances/${instance.uuid}/components`),
                variant: 'default' as const,
              })
            })
          }

          // Adicionar ação de deletar no final
          actions.push({
            label: 'Delete',
            icon: <Trash2 size={14} />,
            onClick: () => handleDelete(application.uuid),
            variant: 'danger',
          } as any)

          return actions
        }}
      />
    </div>
  )
}

export default Applications
