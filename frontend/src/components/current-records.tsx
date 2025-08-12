import { useTHPSRuns } from "@/hooks/useTHPSData"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "./ui/table"
import * as flags from "country-flag-icons/react/3x2"

type CountryCode = keyof typeof flags

const CountryFlag = ({ countryCode }: { countryCode: CountryCode }) => {
    const FlagIcon = flags[countryCode.toUpperCase() as CountryCode]
    if(!FlagIcon) return <></>
    return <FlagIcon className="w-7 pr-1" />
}

export const CurrentRecords = () => {
    const { data: runs } = useTHPSRuns()

    return (
        <div className="flex-1 rounded-lg p-6 flex flex-col">
            <h1 className="text-xl font-semibold mb-4">
                Current Records
            </h1>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[100px]">Game</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead className="w-[300px]">Player</TableHead>
                        <TableHead>Time</TableHead>
                        <TableHead>Date</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {runs.map((run, i) => (
                        <TableRow key={i}>
                            <TableCell className="font-medium">{run.game.name}</TableCell>
                            <TableCell>{run.subcategory}</TableCell>
                            <TableCell className="flex items-center">{run.players[0].player?.country && <><CountryFlag countryCode={run.players[0].player?.country as CountryCode} />{run.players[0].player?.name}</>}</TableCell>
                            <TableCell>{run.time}</TableCell>
                            <TableCell>{run.players[0].date}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}