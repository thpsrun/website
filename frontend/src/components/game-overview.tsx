import { TrophyIcon, VideoIcon, Loader2, Play } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
import * as flags from "country-flag-icons/react/3x2"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTHPSGameData } from "@/hooks/useTHPSGameData";
import { useTHPSGameSubcategories } from "@/hooks/useTHPSGameSubcategories";

type CountryCode = keyof typeof flags

const getRankBackground = (place: number) => {
    if (place === 1) return "bg-yellow-500/50";
    if (place === 2) return "bg-gray-300/50";
    if (place === 3) return "bg-orange-500/50";
    return "bg-gray-700";
}

const CountryFlag = ({ countryCode }: { countryCode: CountryCode }) => {
    const FlagIcon = flags[countryCode.toUpperCase() as CountryCode]
    if(!FlagIcon) return <></>
    return <FlagIcon className="w-7 pl-2 inline" />
}

export const GameOverview = () => {
  // TODO: derive slug from router params once route updated to /game/:slug
  const gameSlug = 'thps12'; // TODO: Derive from route params
  const [mode, setMode] = useState<"full" | "level">("full");

  // Fetch subcategories for current mode (per-game vs per-level)
  const subType = mode === 'full' ? 'per-game' : 'per-level';
  const { data: subcats, isLoading: loadingSubcats, isError: subcatError, error: subcatErrObj } = useTHPSGameSubcategories({
    gameSlug,
    type: subType,
  });

  const categories = useMemo(() => (subcats ? subcats.map(s => s.name) : []), [subcats]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  // When categories list updates or mode changes, ensure selection valid
  useEffect(() => {
    if (categories.length && !categories.includes(selectedCategory)) {
      setSelectedCategory(categories[0]);
    }
  }, [categories, mode]);

  const { data, isLoading, isError, error } = useTHPSGameData({
    gameSlug,
    category: selectedCategory,
    limit: 50,
    ordering: 'time',
    embedPlayers: true,
  }, { enabled: Boolean(gameSlug && selectedCategory) });

  const runs = data?.runs ?? [];
  const sortedRuns = useMemo(() => {
    // Use provided order if place > 0 else sort by time_secs asc
    const hasPlaces = runs.some(r => r.place && r.place > 0);
    if (hasPlaces) return runs.slice().sort((a,b) => (a.place || 99999) - (b.place || 99999));
    return runs.slice().sort((a,b) => a.times.time_secs - b.times.time_secs);
  }, [runs]);

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
      <div className="bg-background-transparent p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white mb-2">Leaderboard</h2>
          <Select
            value={mode}
            onValueChange={(value: string) => setMode(value as 'full' | 'level')}
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select Mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="full">Full Game</SelectItem>
              <SelectItem value="level">Individual Level</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          {/* Multi-line tabs: use flex-wrap + h-auto so rows expand; custom trigger height */}
          <TabsList className="flex flex-wrap gap-1 h-auto items-stretch bg-background-accent/40 backdrop-blur supports-[backdrop-filter]:bg-accent/40 p-1 rounded-md">
            {loadingSubcats && (
              <TabsTrigger disabled value="loading">Loading…</TabsTrigger>
            )}
            {subcatError && (
              <TabsTrigger disabled value="error">Error</TabsTrigger>
            )}
            {!loadingSubcats && !subcatError && categories.map(cat => (
              <TabsTrigger className="cursor-pointer hover:bg-accent h-8" key={cat} value={cat}>{cat}</TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={selectedCategory} className="mt-4">
            {(isLoading || loadingSubcats) && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground p-4"><Loader2 className="h-4 w-4 animate-spin" /> Loading runs…</div>
            )}
            {subcatError && (
              <div className="text-sm text-red-500 p-4">Category load error: {subcatErrObj?.message}</div>
            )}
            {isError && !isLoading && !loadingSubcats && !subcatError && (
              <div className="text-sm text-red-500 p-4">Error: {error?.message}</div>
            )}
            {!isLoading && !loadingSubcats && !isError && !subcatError && selectedCategory && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16 pl-4">Rank</TableHead>
                    <TableHead className="w-8">Player</TableHead>
                    <TableHead className="text-right">Time</TableHead>
                    <TableHead className="text-right">Points</TableHead>
                    <TableHead className="text-right pr-4">Date</TableHead>
                    <TableHead className="text-right pr-4">Video</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedRuns.slice(0,50).map((run, idx) => {
                    const rank = run.place && run.place > 0 ? run.place : idx + 1;
                    const dateOnly = run.date ? new Date(run.date).toISOString().split('T')[0] : '';
                    const timeDisplay = run.times.time != "0" ? run.times.time : run.times.timeigt;
                    const playerName = typeof run.players === 'string' ? run.players : (run.players?.name || 'Unknown');
                    return (
                      <TableRow key={run.id} className={`${run.status.obsolete ? 'opacity-60' : ''} ${idx % 2 === 1 ? 'bg-muted/30' : ''}`}>
                        <TableCell className="pl-4 w-16">
                            <div className={`flex items-center justify-center w-8 h-8 rounded-full ${getRankBackground(rank)} text-center`}>
                                    {rank}
                            </div>
                        </TableCell>
                        <TableCell className="">{playerName}{run.players.country && <><CountryFlag countryCode={run.players.country as CountryCode} /></>}</TableCell>
                        <TableCell className="text-right font-mono tabular-nums tracking-tight">{timeDisplay}</TableCell>
                        <TableCell className="text-right font-mono tabular-nums tracking-tight">{run.meta.points}</TableCell>
                        <TableCell className="text-right pr-4">{dateOnly}</TableCell>
                        <TableCell className="pr-6">{run.videos.video ? <a href={run.videos.video} target="_blank" rel="noopener noreferrer" className="flex justify-end"><Play size={16} /></a> : 'N/A'}</TableCell>
                      </TableRow>
                    )
                  })}
                  {sortedRuns.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-sm text-muted-foreground">No runs found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
