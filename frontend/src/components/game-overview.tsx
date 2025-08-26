import { useState, useEffect, useMemo } from "react";
import { Navigate, useParams } from "react-router";

import { TrophyIcon, VideoIcon, Play } from "lucide-react";
import * as flags from "country-flag-icons/react/3x2"

import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { useGameCategories } from '@/hooks/useGameCategories'
import { useLeaderboardRuns } from '@/hooks/useLeaderboardRuns'
import { useGameLevels } from '@/hooks/useGameLevels'

import { cn, slugify } from '@/utils'

import type { LeaderboardRun } from '@/types/api'


type CountryCode = keyof typeof flags

const getRankBackground = (place: number) => {
    if (place === 1) return "bg-yellow-500/50";
    if (place === 2) return "bg-gray-300/50";
    if (place === 3) return "bg-orange-500/50";
    return "bg-gray-700";
}

const CountryFlag = ({ countryCode }: { countryCode: CountryCode }) => {
    const FlagIcon = flags[countryCode.toUpperCase() as CountryCode]
    if (!FlagIcon) return <></>
    return <FlagIcon className="w-7 pl-2 inline" />
}

export const GameOverview = () => {
    // Get the game slug from the URL parameters
    const { gameSlug } = useParams<{ gameSlug: string }>();
    if (!gameSlug) return <Navigate to='/' replace />;

    // Fetch game categories from API
    const { data: categories, isLoading: catsLoading, error: catsError } = useGameCategories({ gameId: gameSlug })

    // State for the current tab mode - matched to API category types
    const [mode, setMode] = useState<'per-game' | 'per-level'>('per-game')

    const perGameCats = useMemo(() => (categories || []).filter(c => c.type === 'per-game'), [categories])
    const perLevelCats = useMemo(() => (categories || []).filter(c => c.type === 'per-level'), [categories])
    const catList = mode === 'per-game' ? perGameCats : perLevelCats

    const [selectedCategoryId, setSelectedCategoryId] = useState('')
    useEffect(() => { setSelectedCategoryId(catList[0]?.id || '') }, [mode, catList])
    const selectedCategory = catList.find(c => c.id === selectedCategoryId)

    // Variable selections (per-game only usually)
    const [variableSelections, setVariableSelections] = useState<Record<string, string>>({})
    const variableList = selectedCategory?.variables || []

    // Ugly useEffect to set default selections
    useEffect(() => {
        if (selectedCategoryId && variableList.length > 0) {
            const defaults: Record<string, string> = {};
            for (const v of variableList) {
                if (v.values && v.values.length > 0) {
                    defaults[v.id] = v.values[0].value;
                }
            }
            setVariableSelections(defaults);
        } else {
            setVariableSelections({});
        }
    }, [selectedCategoryId, variableList])

    // Levels (for per-level mode)
    const { data: levels } = useGameLevels(gameSlug, { enabled: mode === 'per-level' })
    const [selectedLevelSlug, setSelectedLevelSlug] = useState('')

    // Another ugly useEffect
    useEffect(() => {
        if (mode === 'per-level' && levels?.length) {
            const first = levels[0]
            setSelectedLevelSlug(first.slug || (first as any).id || slugify(first.name))
        }
    }, [mode, levels])

    // Build path for per-game leaderboard categories: /categories/<game>/<base>/<varValSlug...>
    const perGamePathSegments = useMemo(() => {
        if (mode !== 'per-game' || !selectedCategory) return []
        const segs = [slugify(selectedCategory.name)]
        for (const v of variableList) {
            const valId = variableSelections[v.id]
            if (!valId) return segs
            const valObj = v.values.find(val => val.value === valId)
            if (valObj) segs.push(slugify(valObj.name))
        }
        return segs
    }, [mode, selectedCategory, variableSelections, variableList])

    const perGameReady = mode === 'per-game' && selectedCategory && variableList.every(v => variableSelections[v.id])

    // Build per-level leaderboard: /leaderboard/<game>/<category-slug>?level=<levelSlug>
    const perLevelCategorySlug = useMemo(() => selectedCategory ? selectedCategory.slug : '', [selectedCategory])

    const { data: runs, isLoading: runsLoading, error: runsError } = useLeaderboardRuns(
        mode === 'per-game'
            ? { gameSlug, pathSegments: perGamePathSegments }
            : { gameSlug, pathSegments: [perLevelCategorySlug], query: { level: selectedLevelSlug } },
        { enabled: mode === 'per-game' ? perGameReady : Boolean(perLevelCategorySlug && selectedLevelSlug) }
    )

    const sortedRuns: LeaderboardRun[] = useMemo(() => {
        if (!runs) return []
        const hasPlaces = runs.some(r => r.place && r.place > 0)
        if (hasPlaces) return runs.slice().sort((a, b) => (a.place || 99999) - (b.place || 99999))
        return runs.slice().sort((a, b) => a.times.time_secs - b.times.time_secs)
    }, [runs])

    return (
        <div className="w-full flex flex-col gap-8">
            <div className="relative w-full h-64 rounded-lg bg-background shadow-md shadow-black/30">
                {/* Background image container - constrained width with transparency */}
                <div
                    className="absolute left-0 top-0 bottom-0 w-1/3 bg-cover bg-center bg-no-repeat opacity-80"
                    style={{
                        backgroundImage: "url('/src/assets/headers/thps1_2.jpeg')",
                    }}
                />
                {/* Gradient overlay that fades the image to background - more gradual */}
                <div className="absolute left-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-background from-10% via-40% via-background/20 to-transparent" />
                {/* Content container */}
                <div className="flex w-full mih-full">
                    <div className="w-1/3 h-2"></div>
                    <div className="relative p-6 w-1/2">
                        {/* Your content goes here */}
                        <CardHeader className="p-0 bg-transparent">
                            <CardTitle className="text-3xl font-bold text-white mb-2">
                                Tony Hawk's Pro Skater 1+2
                            </CardTitle>
                            <div className="flex flex-wrap mb-4 gap-2">
                                <Badge>PlayStation 4</Badge>
                                <Badge>PlayStation 5</Badge>
                                <Badge>PC</Badge>
                                <Badge>Xbox One</Badge>
                                <Badge>Xbox Series X/S</Badge>
                                <Badge>Nintendo Switch</Badge>
                            </div>
                            <CardDescription className="text-gray-400 mb-4">
                                Tony Hawk's Pro Skater 1 + 2 faithfully remasters the first two
                                games with rebuilt levels, original skaters and soundtrack, and
                                updated controls. Skate Warehouse, School, and more, complete
                                challenges, and stack high scores. Create a skater or park, then
                                play solo, split-screen, or online.
                            </CardDescription>
                            <div className="flex items-center text-sm text-gray-400">
                                <div className="flex items-center mr-4">
                                    <TrophyIcon size={16} className="mr-1 text-yellow-500" />
                                    <span>154 Runs</span>
                                </div>
                                <div className="flex items-center">
                                    <VideoIcon size={16} className="mr-1 text-red-500" />
                                    <span>87 Videos</span>
                                </div>
                            </div>
                        </CardHeader>
                    </div>
                </div>
            </div>

            {/* LEADERBOARD PANEL */}
            <div className="rounded-lg border border-border/40 bg-background/70 backdrop-blur-sm shadow-sm">
                <div className="border-b border-border/40 px-4 pt-4 pb-2 flex flex-col gap-3">
                    {/* Mode + Category */}
                    <div className="flex flex-col gap-3">
                        <div className="flex flex-wrap items-center gap-4">
                            <Tabs value={mode} onValueChange={(v) => setMode(v as any)}>
                                <TabsList className="h-auto flex gap-1 bg-muted/30 p-1 rounded-md">
                                    <TabsTrigger value="per-game" className="px-3 py-1 rounded-sm data-[state=active]:bg-background data-[state=active]:shadow">Full Game</TabsTrigger>
                                    <TabsTrigger value="per-level" className="px-3 py-1 rounded-sm data-[state=active]:bg-background data-[state=active]:shadow">Individual Level</TabsTrigger>
                                </TabsList>
                            </Tabs>
                        </div>
                        <Tabs value={selectedCategoryId} onValueChange={setSelectedCategoryId}>
                            <TabsList className="flex flex-wrap gap-1 bg-muted/20 p-1 rounded-md max-h-32 overflow-y-auto">
                                {catsLoading && <TabsTrigger disabled value="loading">Loading…</TabsTrigger>}
                                {catsError && <TabsTrigger disabled value="error">Error</TabsTrigger>}
                                {!catsLoading && !catsError && catList.map(cat => (
                                    <TabsTrigger
                                        key={cat.id}
                                        value={cat.id}
                                        className="px-3 py-1 rounded-sm text-xs data-[state=active]:bg-background data-[state=active]:shadow"
                                    >{cat.name}</TabsTrigger>
                                ))}
                            </TabsList>
                        </Tabs>
                    </div>
                    {/* Variable / Level selectors */}
                    {selectedCategory && (
                        <div className="flex flex-col gap-3">
                            {mode === 'per-game' && variableList.map(variable => {
                                const values = variable.values
                                const compact = values.length <= 6 // use pill group
                                return (
                                    <div key={variable.id} className="flex flex-col gap-2">
                                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{variable.name}</div>
                                        {compact ? (
                                            <div className="flex flex-wrap gap-1">
                                                {values.map(v => {
                                                    const active = variableSelections[variable.id] === v.value
                                                    return (
                                                        <button
                                                            key={v.value}
                                                            onClick={() => setVariableSelections(p => ({ ...p, [variable.id]: v.value }))}
                                                            className={cn('px-2.5 py-1 rounded-md text-xs border transition',
                                                                active ? 'bg-background shadow border-border/60' : 'bg-muted/30 hover:bg-muted/50 border-transparent')}
                                                        >{v.name}</button>
                                                    )
                                                })}
                                            </div>
                                        ) : (
                                            <div className="w-64">
                                                <Select value={variableSelections[variable.id] || ''} onValueChange={(val) => setVariableSelections(p => ({ ...p, [variable.id]: val }))}>
                                                    <SelectTrigger className="h-8 text-xs"><SelectValue placeholder={`Select ${variable.name}`} /></SelectTrigger>
                                                    <SelectContent className="max-h-60">
                                                        {values.map(v => <SelectItem key={v.value} value={v.value}>{v.name}</SelectItem>)}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                            {mode === 'per-level' && levels && (
                                <Tabs value={selectedLevelSlug} onValueChange={setSelectedLevelSlug}>
                                    <TabsList className="flex gap-1 overflow-x-auto scrollbar-thin scrollbar-thumb-muted/30 rounded-md bg-muted/20 p-1">
                                        {levels.map(l => {
                                            const key = (l as any).id || l.slug || slugify(l.name)
                                            const value = l.slug || (l as any).id || slugify(l.name)
                                            return <TabsTrigger key={key} value={value} className="whitespace-nowrap px-3 py-1 text-xs data-[state=active]:bg-background data-[state=active]:shadow">{l.name}</TabsTrigger>
                                        })}
                                    </TabsList>
                                </Tabs>
                            )}

                            {/* Selection summary */}
                            <div className="text-xs text-muted-foreground">
                                {mode === 'per-game' && selectedCategory && (
                                    <span>Selected: <strong>{selectedCategory.name}</strong>{variableList.length > 0 && ': '}{variableList.map(v => {
                                        const val = v.values.find(val => val.value === variableSelections[v.id])
                                        return val ? val.name : '—'
                                    }).filter(Boolean).join(' / ')}</span>
                                )}
                                {mode === 'per-level' && selectedCategory && selectedLevelSlug && (
                                    <span>Selected: <strong>{selectedCategory.name}</strong>{' / '}<strong>{levels?.find(l => (l.slug || (l as any).id) === selectedLevelSlug)?.name}</strong></span>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Runs Table */}
                <div className="p-4">
                    {runsLoading && (
                        <div className="space-y-2 animate-pulse">
                            {[...Array(6)].map((_, i) => <div key={i} className="h-6 rounded bg-muted/30" />)}
                        </div>
                    )}
                    {runsError && !runsLoading && <div className="text-sm text-red-500 p-4 border border-red-500/20 rounded">Error loading runs</div>}
                    {((mode === 'per-game' && perGameReady) || (mode === 'per-level' && selectedLevelSlug)) && !runsLoading && !runsError && (
                        <div className="rounded-md border border-border/40 overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow className="bg-muted/20">
                                        <TableHead className="w-16 pl-4">#</TableHead>
                                        <TableHead className="w-40">Player</TableHead>
                                        <TableHead className="text-right">Time</TableHead>
                                        <TableHead className="text-right">Points</TableHead>
                                        <TableHead className="text-right pr-4">Date</TableHead>
                                        <TableHead className="text-right pr-4">Video</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {sortedRuns.map((r, idx) => {
                                        const rank = r.place && r.place > 0 ? r.place : idx + 1;
                                        const dateOnly = r.date ? new Date(r.date).toISOString().split('T')[0] : '';
                                        const playerName = Array.isArray(r.players) && r.players.length > 0 
                                            ? r.players.map(p => p.name || 'Anonymous').join(', ') 
                                            : 'Unknown';
                                        let timeDisplay;
                                        switch (r.times.defaulttime) {
                                            case "ingame":
                                                timeDisplay = r.times.timeigt !== "0" ? r.times.timeigt : r.times.time; // fallback to realtime if ingame is "0"
                                                break;
                                            case "realtime_noloads":
                                                timeDisplay = r.times.timenl;
                                                break;
                                            case "realtime":
                                            default:
                                                timeDisplay = r.times.time;
                                                break;
                                        }
                                        return (
                                            <TableRow key={r.id} className={cn('transition hover:bg-muted/30', idx % 2 === 1 ? 'bg-muted/10' : '')}>
                                                <TableCell className="pl-4 w-16">
                                                    <div className={cn('flex items-center justify-center w-8 h-8 rounded-full text-center text-xs font-semibold', getRankBackground(rank))}>{rank}</div>
                                                </TableCell>
                                                <TableCell className="text-sm">
                                                    {playerName}
                                                    {Array.isArray(r.players) && r.players.length > 0 && r.players[0].country && (
                                                        <CountryFlag countryCode={r.players[0].country as CountryCode} />
                                                    )}
                                                </TableCell>
                                                <TableCell className="text-right font-mono tabular-nums tracking-tight text-sm">{timeDisplay}</TableCell>
                                                <TableCell className="text-right font-mono tabular-nums tracking-tight text-sm">{r.meta.points}</TableCell>
                                                <TableCell className="text-right pr-4 text-xs">{dateOnly}</TableCell>
                                                <TableCell className="pr-6 text-right">{r.videos.video ? <a href={r.videos.video} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center h-6 w-6 rounded hover:bg-muted/40"><Play size={14} /></a> : <span className="text-muted-foreground/50 text-xs">—</span>}</TableCell>
                                            </TableRow>
                                        )
                                    })}
                                    {sortedRuns.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">No runs found.</TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                    {!runsLoading && !runsError && mode === 'per-game' && selectedCategory && !perGameReady && (
                        <div className="text-sm text-muted-foreground p-4 border border-dashed border-border/40 rounded">Select all variables to view leaderboard.</div>
                    )}
                    {!runsLoading && !runsError && mode === 'per-level' && selectedCategory && !selectedLevelSlug && (
                        <div className="text-sm text-muted-foreground p-4 border border-dashed border-border/40 rounded">Select a level to view leaderboard.</div>
                    )}
                </div>
            </div>
        </div>
    );
};
