import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import { validateForm, getFieldError } from './validation'

describe('validateForm', () => {
  const testSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().email('Invalid email'),
    age: z.number().min(18, 'Must be at least 18'),
  })

  it('should return success when data is valid', () => {
    const validData = {
      name: 'John Doe',
      email: 'john@example.com',
      age: 25,
    }

    const result = validateForm(testSchema, validData)

    expect(result.success).toBe(true)
    expect(result.data).toEqual(validData)
    expect(result.errors).toBeUndefined()
  })

  it('should return errors when data is invalid', () => {
    const invalidData = {
      name: '',
      email: 'invalid-email',
      age: 15,
    }

    const result = validateForm(testSchema, invalidData)

    expect(result.success).toBe(false)
    expect(result.data).toBeUndefined()
    expect(result.errors).toBeDefined()
    expect(result.errors?.name).toBe('Name is required')
    expect(result.errors?.email).toBe('Invalid email')
    expect(result.errors?.age).toBe('Must be at least 18')
  })

  it('should handle missing fields', () => {
    const incompleteData = {
      name: 'John Doe',
    }

    const result = validateForm(testSchema, incompleteData)

    expect(result.success).toBe(false)
    expect(result.errors).toBeDefined()
    expect(result.errors?.email).toBeDefined()
    expect(result.errors?.age).toBeDefined()
  })

  it('should handle errors without path', () => {
    const schemaWithCustomError = z.object({
      value: z.string(),
    }).refine(() => false, { message: 'Custom error' })

    const result = validateForm(schemaWithCustomError, { value: 'test' })

    expect(result.success).toBe(false)
    expect(result.errors).toBeDefined()
    expect(result.errors?._form).toBe('Custom error')
  })
})

describe('getFieldError', () => {
  it('should return error message for existing field', () => {
    const errors = {
      name: 'Name is required',
      email: 'Invalid email',
    }

    expect(getFieldError(errors, 'name')).toBe('Name is required')
    expect(getFieldError(errors, 'email')).toBe('Invalid email')
  })

  it('should return undefined for non-existent field', () => {
    const errors = {
      name: 'Name is required',
    }

    expect(getFieldError(errors, 'email')).toBeUndefined()
  })

  it('should return undefined when errors object is undefined', () => {
    expect(getFieldError(undefined, 'name')).toBeUndefined()
  })
})
