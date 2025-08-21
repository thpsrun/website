import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'

import type { GameCategory } from '@/types/api'
import { API_BASE_URL } from '@/constants'

export interface UseGameCategoriesParams { gameId: string }

type QueryOptions = Omit<UseQueryOptions<GameCategory[], Error>, 'queryKey' | 'queryFn'>

const fetchCategories = async (gameId: string): Promise<GameCategory[]> => {
    if (!gameId) throw new Error('gameId required')

    const res = await fetch(`${API_BASE_URL}/website/categories/${encodeURIComponent(gameId)}`)

    if (!res.ok) throw new Error(`Failed categories (${res.status})`)

    return res.json()
}

export const useGameCategories = (params: UseGameCategoriesParams, options?: QueryOptions) => {
    const enabled = !!params.gameId && (options?.enabled ?? true)
    
    return useQuery<GameCategory[], Error>({
        queryKey: ['game-categories', params.gameId],
        queryFn: () => fetchCategories(params.gameId),
        staleTime: 5 * 60 * 1000,
        ...options,
        enabled,
    })
}
