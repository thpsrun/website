import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'

import { API_BASE_URL } from '@/constants';


export interface LevelItem { id: string; name: string; slug: string }

type QueryOptions = Omit<UseQueryOptions<LevelItem[], Error>, 'queryKey' | 'queryFn'>

const fetchLevels = async (gameSlug: string): Promise<LevelItem[]> => {
    if (!gameSlug) throw new Error('gameSlug required')

    const res = await fetch(`${API_BASE_URL}/website/levels/${encodeURIComponent(gameSlug)}`)

    if (!res.ok) throw new Error(`Failed levels (${res.status})`)

    return res.json()
}


export const useGameLevels = (gameSlug: string, options?: QueryOptions) => {
    const enabled = !!gameSlug && (options?.enabled ?? true)

    return useQuery<LevelItem[], Error>({
        queryKey: ['levels', gameSlug],
        queryFn: () => fetchLevels(gameSlug),
        staleTime: 5 * 60 * 1000,
        ...options,
        enabled,
    })
}
