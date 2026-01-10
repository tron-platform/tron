import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import type {
  Cluster,
  ClusterCreate,
  Environment,
  EnvironmentCreate,
  Namespace,
  NamespaceCreate,
  Workload,
  WorkloadCreate,
  Application,
  ApplicationCreate,
  WebappDeploy,
  WebappDeployCreate,
  Template,
  TemplateCreate,
  TemplateUpdate,
  ComponentTemplateConfig,
  ComponentTemplateConfigCreate,
  ComponentTemplateConfigUpdate,
  ApplicationComponent,
  ApplicationComponentCreate,
  Instance,
  InstanceCreate,
  User,
  UserCreate,
  LoginRequest,
  Token,
  RefreshTokenRequest,
  UpdateProfileRequest,
  ApiToken,
  ApiTokenCreate,
  ApiTokenUpdate,
  ApiTokenCreateResponse,
  CronJob,
  CronJobLogs,
  Pod,
  PodLogs,
  PodCommandResponse,
  DashboardOverview,
  KubernetesEvent,
} from '../types'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para refresh automático de token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Não tentar refresh em endpoints de autenticação (login, register, refresh)
    // Um 401 nesses endpoints significa credenciais inválidas, não token expirado
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/login') ||
                          originalRequest?.url?.includes('/auth/register') ||
                          originalRequest?.url?.includes('/auth/refresh')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const response = await axios.post<Token>(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token } = response.data
        localStorage.setItem('access_token', access_token)
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        return api(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Clusters
export const clustersApi = {
  list: async (): Promise<Cluster[]> => {
    const response = await api.get<Cluster[]>('/clusters/')
    return response.data
  },
  get: async (uuid: string): Promise<Cluster> => {
    const response = await api.get<Cluster>(`/clusters/${uuid}`)
    return response.data
  },
  create: async (data: ClusterCreate): Promise<Cluster> => {
    const response = await api.post<Cluster>('/clusters/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ClusterCreate>): Promise<Cluster> => {
    const response = await api.put<Cluster>(`/clusters/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/clusters/${uuid}`)
  },
}

// Environments
export const environmentsApi = {
  list: async (): Promise<Environment[]> => {
    const response = await api.get<Environment[]>('/environments/')
    return response.data
  },
  get: async (uuid: string): Promise<Environment> => {
    const response = await api.get<Environment>(`/environments/${uuid}`)
    return response.data
  },
  create: async (data: EnvironmentCreate): Promise<Environment> => {
    const response = await api.post<Environment>('/environments/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<EnvironmentCreate>): Promise<Environment> => {
    const response = await api.put<Environment>(`/environments/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/environments/${uuid}`)
  },
}

// Namespaces
export const namespacesApi = {
  list: async (): Promise<Namespace[]> => {
    const response = await api.get<Namespace[]>('/namespaces/')
    return response.data
  },
  get: async (uuid: string): Promise<Namespace> => {
    const response = await api.get<Namespace>(`/namespaces/${uuid}`)
    return response.data
  },
  create: async (data: NamespaceCreate): Promise<Namespace> => {
    const response = await api.post<Namespace>('/namespaces/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<NamespaceCreate>): Promise<Namespace> => {
    const response = await api.put<Namespace>(`/namespaces/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/namespaces/${uuid}`)
  },
}

// Workloads
export const workloadsApi = {
  list: async (): Promise<Workload[]> => {
    const response = await api.get<Workload[]>('/workloads/')
    return response.data
  },
  get: async (uuid: string): Promise<Workload> => {
    const response = await api.get<Workload>(`/workloads/${uuid}`)
    return response.data
  },
  create: async (data: WorkloadCreate): Promise<Workload> => {
    const response = await api.post<Workload>('/workloads/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<WorkloadCreate>): Promise<Workload> => {
    const response = await api.put<Workload>(`/workloads/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/workloads/${uuid}`)
  },
}

// Applications
export const applicationsApi = {
  list: async (): Promise<Application[]> => {
    const response = await api.get<Application[]>('/applications/')
    return response.data
  },
  get: async (uuid: string): Promise<Application> => {
    const response = await api.get<Application>(`/applications/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationCreate): Promise<Application> => {
    const response = await api.post<Application>('/applications/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationCreate>): Promise<Application> => {
    const response = await api.put<Application>(`/applications/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/applications/${uuid}`)
  },
}

// Webapp Deploys
export const webappDeploysApi = {
  list: async (): Promise<WebappDeploy[]> => {
    const response = await api.get<WebappDeploy[]>('/webapps/deploys/')
    return response.data
  },
  get: async (uuid: string): Promise<WebappDeploy> => {
    const response = await api.get<WebappDeploy>(`/webapps/deploys/${uuid}`)
    return response.data
  },
  create: async (data: WebappDeployCreate): Promise<WebappDeploy> => {
    const response = await api.post<WebappDeploy>('/webapps/deploys/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<WebappDeployCreate>): Promise<WebappDeploy> => {
    const response = await api.put<WebappDeploy>(`/webapps/deploys/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/webapps/deploys/${uuid}`)
  },
}

// Templates
export const templatesApi = {
  list: async (category?: string): Promise<Template[]> => {
    const params = category ? { category } : {}
    const response = await api.get<Template[]>('/templates/', { params })
    return response.data
  },
  get: async (uuid: string): Promise<Template> => {
    const response = await api.get<Template>(`/templates/${uuid}`)
    return response.data
  },
  create: async (data: TemplateCreate): Promise<Template> => {
    const response = await api.post<Template>('/templates/', data)
    return response.data
  },
  update: async (uuid: string, data: TemplateUpdate): Promise<Template> => {
    const response = await api.put<Template>(`/templates/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/templates/${uuid}`)
  },
}

// Component Template Configs
export const componentTemplateConfigsApi = {
  list: async (component_type?: string): Promise<ComponentTemplateConfig[]> => {
    const params = component_type ? { component_type } : {}
    const response = await api.get<ComponentTemplateConfig[]>('/component-template-configs/', { params })
    return response.data
  },
  get: async (uuid: string): Promise<ComponentTemplateConfig> => {
    const response = await api.get<ComponentTemplateConfig>(`/component-template-configs/${uuid}`)
    return response.data
  },
  create: async (data: ComponentTemplateConfigCreate): Promise<ComponentTemplateConfig> => {
    const response = await api.post<ComponentTemplateConfig>('/component-template-configs/', data)
    return response.data
  },
  update: async (uuid: string, data: ComponentTemplateConfigUpdate): Promise<ComponentTemplateConfig> => {
    const response = await api.put<ComponentTemplateConfig>(`/component-template-configs/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/component-template-configs/${uuid}`)
  },
  getTemplatesForComponent: async (component_type: string): Promise<any[]> => {
    const response = await api.get(`/component-template-configs/component/${component_type}/templates`)
    return response.data
  },
}

// Application Components - Webapp specific
export const applicationComponentsApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/webapp/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/webapp/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    // Only webapp type is supported for now
    if (data.type && data.type !== 'webapp') {
      throw new Error(`Component type ${data.type} is not yet supported. Only 'webapp' is available.`)
    }
    const response = await api.post<ApplicationComponent>('/application_components/webapp/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/webapp/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/webapp/${uuid}`)
  },
  getPods: async (uuid: string): Promise<Pod[]> => {
    const response = await api.get<Pod[]>(`/application_components/webapp/${uuid}/pods`)
    return response.data
  },
  deletePod: async (uuid: string, podName: string): Promise<void> => {
    await api.delete(`/application_components/webapp/${uuid}/pods/${podName}`)
  },
  getPodLogs: async (uuid: string, podName: string, containerName?: string, tailLines: number = 100): Promise<PodLogs> => {
    const params = new URLSearchParams()
    if (containerName) {
      params.append('container_name', containerName)
    }
    params.append('tail_lines', tailLines.toString())
    const response = await api.get<PodLogs>(`/application_components/webapp/${uuid}/pods/${podName}/logs?${params.toString()}`)
    return response.data
  },
  execPodCommand: async (uuid: string, podName: string, command: string[], containerName?: string): Promise<PodCommandResponse> => {
    const response = await api.post<PodCommandResponse>(`/application_components/webapp/${uuid}/pods/${podName}/exec`, {
      command,
      container_name: containerName,
    })
    return response.data
  },
}

// Application Components - Cron specific
export const cronsApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/cron/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/cron/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    const response = await api.post<ApplicationComponent>('/application_components/cron/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/cron/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/cron/${uuid}`)
  },
  getJobs: async (uuid: string): Promise<CronJob[]> => {
    const response = await api.get<CronJob[]>(`/application_components/cron/${uuid}/jobs`)
    return response.data
  },
  getJobLogs: async (uuid: string, jobName: string, containerName?: string, tailLines: number = 100): Promise<CronJobLogs> => {
    const params = new URLSearchParams()
    if (containerName) {
      params.append('container_name', containerName)
    }
    params.append('tail_lines', tailLines.toString())
    const response = await api.get<CronJobLogs>(`/application_components/cron/${uuid}/jobs/${jobName}/logs?${params.toString()}`)
    return response.data
  },
  deleteJob: async (uuid: string, jobName: string): Promise<void> => {
    await api.delete(`/application_components/cron/${uuid}/jobs/${jobName}`)
  },
}

// Application Components - Worker specific
export const workersApi = {
  list: async (): Promise<ApplicationComponent[]> => {
    const response = await api.get<ApplicationComponent[]>('/application_components/worker/')
    return response.data
  },
  get: async (uuid: string): Promise<ApplicationComponent> => {
    const response = await api.get<ApplicationComponent>(`/application_components/worker/${uuid}`)
    return response.data
  },
  create: async (data: ApplicationComponentCreate): Promise<ApplicationComponent> => {
    const response = await api.post<ApplicationComponent>('/application_components/worker/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<ApplicationComponentCreate>): Promise<ApplicationComponent> => {
    const response = await api.put<ApplicationComponent>(`/application_components/worker/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/application_components/worker/${uuid}`)
  },
}

// Instances
export const instancesApi = {
  list: async (): Promise<Instance[]> => {
    const response = await api.get<Instance[]>('/instances/')
    return response.data
  },
  get: async (uuid: string): Promise<Instance> => {
    const response = await api.get<Instance>(`/instances/${uuid}`)
    return response.data
  },
  create: async (data: InstanceCreate): Promise<Instance> => {
    const response = await api.post<Instance>('/instances/', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<InstanceCreate>): Promise<Instance> => {
    const response = await api.put<Instance>(`/instances/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/instances/${uuid}`)
  },
  getEvents: async (uuid: string): Promise<KubernetesEvent[]> => {
    const response = await api.get<KubernetesEvent[]>(`/instances/${uuid}/events`)
    return response.data
  },
  sync: async (uuid: string): Promise<{ detail: string; synced_components: number; total_components: number; errors: Array<{ component: string; error: string }> }> => {
    const response = await api.post(`/instances/${uuid}/sync`)
    return response.data
  },
}

// Auth
export const authApi = {
  login: async (data: LoginRequest): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', data)
    return response.data
  },
  register: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },
  refresh: async (data: RefreshTokenRequest): Promise<Token> => {
    const response = await api.post<Token>('/auth/refresh', data)
    return response.data
  },
  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },
  updateProfile: async (data: UpdateProfileRequest): Promise<User> => {
    const response = await api.put<User>('/auth/me', data)
    return response.data
  },
}

// Users API (Admin only)
export const usersApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }): Promise<User[]> => {
    const response = await api.get<User[]>('/users', { params })
    return response.data
  },
  get: async (uuid: string): Promise<User> => {
    const response = await api.get<User>(`/users/${uuid}`)
    return response.data
  },
  create: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/users', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<UserCreate & { is_active?: boolean; role?: string }>): Promise<User> => {
    const response = await api.put<User>(`/users/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/users/${uuid}`)
  },
}

// Tokens API (Admin only)
export const tokensApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }): Promise<ApiToken[]> => {
    const response = await api.get<ApiToken[]>('/tokens', { params })
    return response.data
  },
  get: async (uuid: string): Promise<ApiToken> => {
    const response = await api.get<ApiToken>(`/tokens/${uuid}`)
    return response.data
  },
  create: async (data: ApiTokenCreate): Promise<ApiTokenCreateResponse> => {
    const response = await api.post<ApiTokenCreateResponse>('/tokens', data)
    return response.data
  },
  update: async (uuid: string, data: ApiTokenUpdate): Promise<ApiToken> => {
    const response = await api.put<ApiToken>(`/tokens/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/tokens/${uuid}`)
  },
}

// Dashboard
export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const response = await api.get<DashboardOverview>('/dashboard/')
    return response.data
  },
}

export default api

