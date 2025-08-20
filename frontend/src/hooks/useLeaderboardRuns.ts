import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'

import type { LeaderboardRun } from '@/types/api'
import { API_BASE_URL } from '@/constants'


export interface UseLeaderboardRunsParams {
    gameSlug: string // e.g. thps12
    pathSegments: string[] // e.g. ['all-goal-levels','new-game-plus']
    query?: Record<string, string | undefined> // extra query params (e.g. level)
}

type QueryOptions = Omit<UseQueryOptions<LeaderboardRun[], Error>, 'queryKey' | 'queryFn'>

const fetchLeaderboard = async ({ gameSlug, pathSegments, query }: UseLeaderboardRunsParams): Promise<LeaderboardRun[]> => {
    if (!gameSlug) throw new Error('gameSlug required')

    const path = pathSegments.filter(Boolean).map(encodeURIComponent).join('/')

    const qs = new URLSearchParams()
    if (query) {
        Object.entries(query).forEach(([k, v]) => { if (v) qs.set(k, v) })
    }

    const url = `${API_BASE_URL}/website/leaderboard/${encodeURIComponent(gameSlug)}/${path}${qs.toString() ? `?${qs.toString()}` : ''}`

    const res = await fetch(url, { headers: { 'Accept': 'application/json' } })

    const json = await res.json();

    if (json?.ERROR == "No runs could be returned.") return []

    if (!res.ok) throw new Error(`Failed leaderboard (${res.status})`)

    return json
}

export const useLeaderboardRuns = (params: UseLeaderboardRunsParams, options?: QueryOptions) => {
    const enabled = !!params.gameSlug && params.pathSegments.length > 0 && (options?.enabled ?? true)

    return useQuery<LeaderboardRun[], Error>({
        queryKey: ['leaderboard', params.gameSlug, ...params.pathSegments, params.query ? JSON.stringify(params.query) : ''],
        queryFn: () => fetchLeaderboard(params),
        staleTime: 60 * 1000,
        refetchInterval: 120 * 1000,
        retry: 2,
        ...options,
        enabled,
    })
}
