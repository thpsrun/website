import { useQuery } from '@tanstack/react-query'
import type { ApiResponse } from '@/types/api'

const API_BASE_URL = 'http://localhost:8001'

// Fetch function
const fetchTHPSData = async (): Promise<ApiResponse> => {
  const response = await fetch(`${API_BASE_URL}/`)
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

// React Query hook
export const useTHPSData = () => {
  return useQuery({
    queryKey: ['thps-data'],
    queryFn: fetchTHPSData,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

// Separate hooks for specific data if needed
export const useTHPSRuns = () => {
  const { data, ...rest } = useTHPSData()
  return {
    data: data?.runs || [],
    ...rest
  }
}

export const useTHPSNewRuns = () => {
  const { data, ...rest } = useTHPSData()
  return {
    data: data?.new_runs || [],
    ...rest
  }
}

export const useTHPSNewWRs = () => {
  const { data, ...rest } = useTHPSData()
  return {
    data: data?.new_wrs || [],
    ...rest
  }
}

export const useTHPSStreamers = () => {
  const { data, ...rest } = useTHPSData()
  return {
    data: data?.streamers || [],
    ...rest
  }
}
