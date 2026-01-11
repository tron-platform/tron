import { describe, it, expect } from 'vitest'
import { formatAge } from './formatAge'

describe('formatAge', () => {
  it('should format seconds correctly', () => {
    expect(formatAge(0)).toBe('0s')
    expect(formatAge(30)).toBe('30s')
    expect(formatAge(59)).toBe('59s')
  })

  it('should format minutes correctly', () => {
    expect(formatAge(60)).toBe('1m')
    expect(formatAge(120)).toBe('2m')
    expect(formatAge(3599)).toBe('59m')
  })

  it('should format hours and minutes correctly', () => {
    expect(formatAge(3600)).toBe('1h0m')
    expect(formatAge(3660)).toBe('1h1m')
    expect(formatAge(3720)).toBe('1h2m')
    expect(formatAge(7200)).toBe('2h0m')
    expect(formatAge(86399)).toBe('23h59m')
  })

  it('should format days and hours correctly', () => {
    expect(formatAge(86400)).toBe('1d0h')
    expect(formatAge(90000)).toBe('1d1h')
    expect(formatAge(172800)).toBe('2d0h')
    expect(formatAge(176400)).toBe('2d1h')
  })

  it('should handle edge cases', () => {
    expect(formatAge(1)).toBe('1s')
    expect(formatAge(59)).toBe('59s')
    expect(formatAge(60)).toBe('1m')
    expect(formatAge(3599)).toBe('59m')
    expect(formatAge(3600)).toBe('1h0m')
    expect(formatAge(86399)).toBe('23h59m')
    expect(formatAge(86400)).toBe('1d0h')
  })
})
