import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'
import type { Game, Run } from '@/types/api'

// Response shape for /api/runs/game/{game_slug}?category=...
export interface GameRunsResponse {
	game: Game
	count: number
	runs: Run[]
}

const API_BASE_URL = 'http://localhost:8001/api'

export interface UseTHPSGameDataParams {
	gameSlug: string
	category: string
	// Optional extra filters your backend supports; add as needed
	limit?: number
	player?: string
	platform?: string
	ordering?: string // e.g. 'time', '-time', 'date', '-date', 'points', '-points'
	embedPlayers?: boolean // convenience flag -> adds embed=players
	embedGame?: boolean // convenience flag -> adds embed=game
}

type QueryOptions = Omit<UseQueryOptions<GameRunsResponse, Error>, 'queryKey' | 'queryFn'>

// Build the request URL with proper encoding
const buildUrl = (params: UseTHPSGameDataParams) => {
	const { gameSlug, category, limit, player, platform, ordering, embedPlayers, embedGame } = params
	const search = new URLSearchParams()
	if (category) search.set('category', category) // encode automatically
	if (limit) search.set('limit', String(limit))
	if (player) search.set('player', player)
	if (platform) search.set('platform', platform)
	if (ordering) search.set('ordering', ordering)
	search.set('best_only', '1')

	const embeds: string[] = []
	if (embedPlayers) embeds.push('players')
	if (embedGame) embeds.push('game')
	if (embeds.length) search.set('embed', embeds.join(','))

	// Always request JSON
	search.set('format', 'json')

	return `${API_BASE_URL}/runs/game/${encodeURIComponent(gameSlug)}?${search.toString()}`
}

const fetchGameRuns = async (params: UseTHPSGameDataParams): Promise<GameRunsResponse> => {
	if (!params.gameSlug) throw new Error('gameSlug is required')
	if (!params.category) throw new Error('category is required')
	const url = buildUrl(params)
	const res = await fetch(url, { headers: { 'Accept': 'application/json' } })
	if (!res.ok) {
		throw new Error(`Failed to fetch game runs (${res.status})`)
	}
	return res.json()
}

/**
 * React Query hook to load runs for a specific game & category/level label.
 *
 * Example:
 * const { data, isLoading } = useTHPSGameData({ gameSlug: 'thug1', category: 'Any% (Beginner)', embedPlayers: true })
 */
export const useTHPSGameData = (
	params: UseTHPSGameDataParams,
	options?: QueryOptions
) => {
	const enabled = Boolean(params.gameSlug && params.category && (options?.enabled ?? true))
	return useQuery<GameRunsResponse, Error>({
		queryKey: ['game-runs', params.gameSlug, params.category, params.limit, params.player, params.ordering, params.embedPlayers, params.embedGame],
		queryFn: () => fetchGameRuns(params),
		staleTime: 60 * 1000, // 1 minute default
		refetchInterval: 60 * 1000,
		retry: 2,
		...options,
		enabled,
	})
}

// Convenience selectors
export const useGameRuns = (params: UseTHPSGameDataParams, options?: QueryOptions) => {
	const { data, ...rest } = useTHPSGameData(params, options)
	return { data: data?.runs ?? [], count: data?.count ?? 0, game: data?.game, ...rest }
}

