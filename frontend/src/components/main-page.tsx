import { useTHPSNewRuns, useTHPSNewWRs } from "@/hooks/useTHPSData"
import { CurrentRecords } from "./current-records"
import { LatestRuns } from "./latest-runs"

export const MainPage = () => {
    const { data: latestRecords } = useTHPSNewWRs();
    const { data: latestRuns } = useTHPSNewRuns();

    console.log(latestRecords, latestRuns);


    return (
        <div className="w-full h-full flex gap-4">
            {/* Left section - stretches full height */}
            <div className="flex-2 bg-background-transparent bg-opacity-10 backdrop-blur-sm rounded-lg flex">
                <CurrentRecords />
            </div>

            {/* Right column with two sections */}
            <div className="flex-1 flex flex-col gap-4">
                {/* Top right section */}
                <div className="flex-1 bg-background-transparent bg-opacity-10 backdrop-blur-sm rounded-lg flex">
                    <LatestRuns title="Latest Records" data={latestRecords} />
                </div>

                {/* Bottom right section */}
                <div className="flex-1 bg-background-transparent bg-opacity-10 backdrop-blur-sm rounded-lg flex">
                    <LatestRuns title="Latest Runs" data={latestRuns} />
                </div>
            </div>
        </div>
    )
}
