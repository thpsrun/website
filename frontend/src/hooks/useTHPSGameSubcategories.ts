import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'

const API_BASE_URL = 'http://localhost:8001/api'

export interface RawSubcategoryCountItem { name: string; run_count: number }
export type RawSubcategories = string[] | RawSubcategoryCountItem[]

export interface GameSubcategoriesResponse {
  game: {
    id: string
    name: string
    slug: string
    release: string
  }
  type?: 'per-level' | 'per-game'
  count: number
  subcategories: RawSubcategories
}

export interface NormalizedSubcategoryItem {
  name: string
  run_count?: number
}

export interface UseTHPSGameSubcategoriesParams {
  gameSlug: string
  type?: 'per-level' | 'per-game'
  includeCounts?: boolean
}

type QueryOptions = Omit<UseQueryOptions<NormalizedSubcategoryItem[], Error>, 'queryKey' | 'queryFn'>

const buildUrl = ({ gameSlug, type, includeCounts }: UseTHPSGameSubcategoriesParams) => {
  const qs = new URLSearchParams()
  if (type) qs.set('type', type)
  if (includeCounts) qs.set('include_counts', '1')
  return `${API_BASE_URL}/runs/game/${encodeURIComponent(gameSlug)}/subcategories?${qs.toString()}`
}

const fetchGameSubcategories = async (params: UseTHPSGameSubcategoriesParams): Promise<NormalizedSubcategoryItem[]> => {
  if (!params.gameSlug) throw new Error('gameSlug is required')
  const res = await fetch(buildUrl(params), { headers: { 'Accept': 'application/json' } })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`Failed to fetch subcategories (${res.status}) ${txt}`)
  }
  const data: GameSubcategoriesResponse = await res.json()
  // Normalize to array of { name, run_count? }
  const normalized: NormalizedSubcategoryItem[] = Array.isArray(data.subcategories)
    ? data.subcategories.map((item: any) => {
        if (typeof item === 'string') return { name: item }
        return { name: item.name, run_count: item.run_count }
      })
    : []
  return normalized
}

export const useTHPSGameSubcategories = (
  params: UseTHPSGameSubcategoriesParams,
  options?: QueryOptions
) => {
  const enabled = Boolean(params.gameSlug) && (options?.enabled ?? true)
  return useQuery<NormalizedSubcategoryItem[], Error>({
    queryKey: ['game-subcategories', params.gameSlug, params.type, params.includeCounts],
    queryFn: () => fetchGameSubcategories(params),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
    ...options,
    enabled,
  })
}

// Convenience variant to always include counts
export const useTHPSGameSubcategoriesWithCounts = (
  params: Omit<UseTHPSGameSubcategoriesParams, 'includeCounts'>,
  options?: QueryOptions
) => useTHPSGameSubcategories({ ...params, includeCounts: true }, options)
