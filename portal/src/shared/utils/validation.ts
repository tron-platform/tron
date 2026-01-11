import { z } from 'zod'

export const validateForm = <T>(schema: z.ZodSchema<T>, data: unknown): { success: boolean; data?: T; errors?: Record<string, string> } => {
  try {
    const validatedData = schema.parse(data)
    return { success: true, data: validatedData }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {}
      // ZodError sempre tem a propriedade issues (não errors)
      if (error.issues && Array.isArray(error.issues)) {
        error.issues.forEach((issue) => {
          // Verifica se há path e se não está vazio
          if (issue.path && Array.isArray(issue.path) && issue.path.length > 0) {
            const fieldName = issue.path[0] as string
            // Se já existe erro para este campo, mantém o primeiro ou concatena
            if (!errors[fieldName]) {
              errors[fieldName] = issue.message
            }
          } else {
            // Se não houver path ou path estiver vazio, usar _form como fallback
            // Se já existe _form, concatena ou mantém o primeiro
            if (!errors._form) {
              errors._form = issue.message
            }
          }
        })
      }
      // Se não houver erros específicos, adicionar erro genérico
      if (Object.keys(errors).length === 0) {
        errors._form = 'Validation failed'
      }
      return { success: false, errors }
    }
    console.error('Validation error:', error)
    return { success: false, errors: { _form: 'Validation failed' } }
  }
}

export const getFieldError = (errors: Record<string, string> | undefined, field: string): string | undefined => {
  return errors?.[field]
}
