import { useTHPSNewWRs } from "@/hooks/useTHPSData"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "./ui/table"
import * as flags from "country-flag-icons/react/3x2"
import type React from "react"
import type { DetailedRun } from "@/types/api"

type CountryCode = keyof typeof flags

const CountryFlag = ({ countryCode }: { countryCode: CountryCode }) => {
    const FlagIcon = flags[countryCode.toUpperCase() as CountryCode]
    if(!FlagIcon) return <></>
    return <FlagIcon className="w-7 pr-1" />
}

const SlugMap = {
    "thps34": "THPS 3+4",
    "thug1": "THUG",
    "thps2": "THPS2",
} as const;

type LatestRunsProps = {
    title: string
    data: DetailedRun[]
}

export const LatestRuns: React.FC<LatestRunsProps> = ({ title, data }) => {
    return (
        <div className="flex-1 rounded-lg p-6 flex flex-col">
            <h1 className="text-xl font-semibold mb-4">
                {title}
            </h1>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[100px]">Game</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead className="w-[300px]">Player</TableHead>
                        <TableHead>Time</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((run, i) => (
                        <TableRow key={i}>
                            <TableCell className="font-medium">{SlugMap[run.game.slug as keyof typeof SlugMap] || ""}</TableCell>
                            <TableCell>{run.subcategory}</TableCell>
                            <TableCell className="flex items-center">{run.players.country && <><CountryFlag countryCode={run.players.country as CountryCode} /></>}{run.players.name || "Anonymous"}</TableCell>
                            <TableCell>{run.times.timeigt}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}