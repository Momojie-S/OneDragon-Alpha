/**
 * API configuration for different environments
 */

// Get API base URL from environment variables
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'

// Mock configuration
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false' && import.meta.env.DEV
export const ALLOW_RUNTIME_MOCK_SWITCH = import.meta.env.DEV

/**
 * Get API base URL for different environments
 * @returns API base URL
 */
export const getApiBaseUrl = (): string => {
  const runtimeMockEnabled = localStorage.getItem('mockEnabled') === 'true'
  const shouldUseMock = USE_MOCK || runtimeMockEnabled

  if (shouldUseMock && ALLOW_RUNTIME_MOCK_SWITCH) {
    return ''  // Vite mock server needs relative URLs without host
  }

  return API_BASE_URL
}
