import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Trash2, Plus, Edit, Mail, UserCheck, UserX, Shield } from 'lucide-react'
import { usersApi } from '../../services/api'
import type { User, UserCreate } from '../../types'
import DataTable from '../../components/DataTable'
import { Breadcrumbs } from '../../components/Breadcrumbs'
import { PageHeader } from '../../components/PageHeader'
import { useAuth } from '../../contexts/AuthContext'

function Users() {
  const { user: currentUser } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users', searchTerm],
    queryFn: () => usersApi.list({ search: searchTerm || undefined }),
  })

  const [formData, setFormData] = useState<UserCreate & { is_active?: boolean; role?: string }>({
    email: '',
    password: '',
    full_name: '',
    is_active: true,
    role: 'user',
  })

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      setNotification({ type: 'success', message: 'User created successfully' })
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setIsOpen(false)
      setEditingUser(null)
      resetForm()
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error creating user',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: any }) => usersApi.update(uuid, data),
    onSuccess: () => {
      setNotification({ type: 'success', message: 'User updated successfully' })
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setIsOpen(false)
      setEditingUser(null)
      resetForm()
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error updating user',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      setNotification({ type: 'success', message: 'User deleted successfully' })
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error deleting user',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ uuid, is_active }: { uuid: string; is_active: boolean }) =>
      usersApi.update(uuid, { is_active }),
    onSuccess: (_, variables) => {
      setNotification({
        type: 'success',
        message: variables.is_active ? 'User activated successfully' : 'User deactivated successfully',
      })
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Error changing user status',
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  const handleToggleActive = (user: User) => {
    const action = user.is_active ? 'deactivate' : 'activate'
    if (window.confirm(`Are you sure you want to ${action} this user?`)) {
      toggleActiveMutation.mutate({ uuid: user.uuid, is_active: !user.is_active })
    }
  }

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      full_name: '',
      is_active: true,
      role: 'user',
    })
  }

  const handleOpenCreate = () => {
    setEditingUser(null)
    resetForm()
    setIsOpen(true)
  }

  const handleEdit = (user: User) => {
    setEditingUser(user)
    setFormData({
      email: user.email,
      password: '', // Não preencher senha
      full_name: user.full_name || '',
      is_active: user.is_active,
      role: user.role,
    })
    setIsOpen(true)
  }

  const handleDelete = (uuid: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      deleteMutation.mutate(uuid)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.email) {
        setNotification({ type: 'error', message: 'Email is required' })
      setTimeout(() => setNotification(null), 5000)
      return
    }

    if (editingUser) {
      // Atualizar usuário
      const updateData: any = {
        email: formData.email,
        full_name: formData.full_name || null,
        is_active: formData.is_active,
        role: formData.role,
      }

      // Só incluir senha se foi preenchida
      if (formData.password) {
        updateData.password = formData.password
      }

      updateMutation.mutate({ uuid: editingUser.uuid, data: updateData })
    } else {
      // Criar usuário
      if (!formData.password) {
        setNotification({ type: 'error', message: 'Password is required for new users' })
        setTimeout(() => setNotification(null), 5000)
        return
      }

      createMutation.mutate({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || null,
      })
    }
  }

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      admin: { label: 'Admin', color: 'bg-purple-100 text-purple-700' },
      user: { label: 'User', color: 'bg-blue-100 text-blue-700' },
      viewer: { label: 'Visualizador', color: 'bg-gray-100 text-gray-700' },
    }

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.user

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${config.color}`}>
        <Shield size={12} className="mr-1" />
        {config.label}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
          { label: 'Users', path: '/users' },
        ]}
      />

      <div className="flex items-center justify-between">
        <PageHeader title="Users" description="Manage platform users" />
        <button onClick={handleOpenCreate} className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          <span>New User</span>
        </button>
      </div>

      {notification && (
        <div
          className={`rounded-lg p-4 flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-success/10 border border-success/20 text-success'
              : 'bg-error/10 border border-error/20 text-error'
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Search Bar */}
      <div className="glass-effect-strong rounded-xl p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by email or name..."
              className="input w-full pl-10"
            />
            <Mail size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" />
          </div>
        </div>
      </div>

      <div className="glass-effect-strong rounded-2xl shadow-soft-lg overflow-hidden">
        <DataTable<User>
          searchable={false}
          columns={[
            {
              key: 'email',
              label: 'Email',
              render: (user) => (
                <div className="flex items-center gap-2">
                  <Mail size={16} className="text-neutral-400" />
                  <span className="text-sm font-medium text-neutral-800">{user.email}</span>
                </div>
              ),
            },
            {
              key: 'full_name',
              label: 'Name',
              render: (user) => (
                <div className="text-sm text-neutral-700">
                  {user.full_name || <span className="text-neutral-400 italic">No name</span>}
                </div>
              ),
            },
            {
              key: 'role',
              label: 'Role',
              render: (user) => getRoleBadge(user.role),
            },
            {
              key: 'is_active',
              label: 'Status',
              render: (user) => (
                <div className="flex items-center gap-2">
                  {user.is_active ? (
                    <>
                      <UserCheck size={16} className="text-success" />
                      <span className="text-sm text-success font-medium">Active</span>
                    </>
                  ) : (
                    <>
                      <UserX size={16} className="text-error" />
                      <span className="text-sm text-error font-medium">Inactive</span>
                    </>
                  )}
                </div>
              ),
            },
            {
              key: 'created_at',
              label: 'Created at',
              render: (user) => (
                <div className="text-sm text-neutral-600">
                  {new Date(user.created_at).toLocaleDateString('pt-BR')}
                </div>
              ),
            },
          ]}
          data={users}
          isLoading={isLoading}
          emptyMessage="No users found"
          loadingColor="blue"
          getRowKey={(user) => user.uuid}
          actions={(user) => {
            const actions = []

            // Não permitir editar/deletar/desativar o próprio usuário
            if (user.uuid !== currentUser?.uuid) {
              actions.push({
                label: user.is_active ? 'Deactivate' : 'Activate',
                icon: user.is_active ? <UserX size={14} /> : <UserCheck size={14} />,
                onClick: () => handleToggleActive(user),
                variant: user.is_active ? ('warning' as const) : ('default' as const),
              })

              actions.push({
                label: 'Edit',
                icon: <Edit size={14} />,
                onClick: () => handleEdit(user),
                variant: 'default' as const,
              })

              actions.push({
                label: 'Delete',
                icon: <Trash2 size={14} />,
                onClick: () => handleDelete(user.uuid),
                variant: 'danger' as const,
              })
            }

            return actions
          }}
        />
      </div>

      {/* Modal Create/Edit */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-effect-strong rounded-2xl shadow-soft-lg w-full max-w-md p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gradient">
                {editingUser ? 'Edit User' : 'New User'}
              </h2>
              <button
                onClick={() => {
                  setIsOpen(false)
                  setEditingUser(null)
                  resetForm()
                }}
                className="p-2 rounded-lg text-neutral-600 hover:bg-neutral-100 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-2">
                  Email *
                </label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input w-full"
                  placeholder="usuario@exemplo.com"
                  required
                />
              </div>

              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-neutral-700 mb-2">
                  Full Name
                </label>
                <input
                  id="full_name"
                  type="text"
                  value={formData.full_name || ''}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input w-full"
                  placeholder="User name"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
                  Password {editingUser ? '(leave blank to keep unchanged)' : '*'}
                </label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input w-full"
                  placeholder={editingUser ? 'New password (optional)' : 'User password'}
                  required={!editingUser}
                  minLength={6}
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-neutral-700 mb-2">
                  Role
                </label>
                <select
                  id="role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="input w-full"
                >
                  <option value="user">User</option>
                  <option value="admin">Administrator</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              {editingUser && (
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm font-medium text-neutral-700">Active user</span>
                  </label>
                </div>
              )}

              <div className="flex items-center justify-end gap-4 pt-4 border-t border-neutral-200">
                <button
                  type="button"
                  onClick={() => {
                    setIsOpen(false)
                    setEditingUser(null)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="btn-primary"
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Saving...</span>
                    </div>
                  ) : (
                    <span>{editingUser ? 'Save' : 'Create'}</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Users

