// API Response Types

export interface Game {
  id: string
  name: string
  slug: string
  release: string
  boxart: string
  twitch: string
  defaulttime: string
  idefaulttime: string
  pointsmax: number
  ipointsmax: number
}

export interface Award {
  name: string
}

export interface Player {
  id: string
  name: string
  nickname?: string | null
  url: string
  pfp?: string | null
  country: string
  pronouns?: string | null
  twitch?: string | null
  youtube?: string | null
  twitter?: string | null
  ex_stream: boolean
  awards: Award[]
  stats: {
    total_pts: number
    main_pts: number
    il_pts: number
    total_runs: number
  }
}

export interface Times {
  defaulttime: string
  time: string
  time_secs: number
  timenl: string
  timenl_secs: number
  timeigt: string
  timeigt_secs: number
}

export interface System {
  platform: string | { id: string; name: string }
  emulated: boolean
}

export interface Status {
  vid_status: string
  approver?: string | null
  v_date: string
  obsolete: boolean
}

export interface Videos {
  video: string
  arch_video?: string | null
}

export interface Meta {
  points: number
  url: string
}

export interface Run {
  id: string
  runtype: string
  game: string // Game ID as string for basic runs
  category: string // Category ID as string
  level: string | null // Level ID as string or null
  subcategory: string
  place: number
  lb_count: number
  players: Player[] // Array of players for multi-player runs
  date: string
  record: string
  times: Times
  system: System
  status: Status
  videos: Videos
  variables: { [key: string]: any }
  meta: Meta
  description?: string | null
}

// Hierarchical category structures (speedrun.com style)
export interface CategoryVariableValue { value: string; name: string; hidden: boolean }
export interface CategoryVariable {
  id: string
  name: string
  all_cats: boolean
  scope: string
  hidden: boolean
  values: CategoryVariableValue[]
}
export interface GameCategory {
  id: string
  name: string
  type: 'per-game' | 'per-level'
  url: string
  hidden: boolean
  variables: CategoryVariable[]
}

// Leaderboard run (same as Run but ensure players is Player, system.platform may be object)
export type LeaderboardRun = Run

// Detailed run with embedded game object (used in latest_wrs, latest_pbs)
export interface DetailedRun {
  id: string
  game: Game // Full game object with embedded data
  category: { name: string } | null // Category object with name
  subcategory: string
  players: Player[] // Array of players with full player objects
  time: string
  date: string // ISO date string
  video: string
  url: string
  place?: number // Only included for latest_pbs
}

export interface RecordPlayer {
  player: Player | null
  url: string
  date: string
}

export interface Record {
  game: Game // Full game object with embedded data
  subcategory: string
  time: string
  players: RecordPlayer[]
}

export interface ApiResponse {
  latest_wrs?: DetailedRun[]
  latest_pbs?: DetailedRun[]
  latest?: Run[]
  new_runs?: Run[]
  records?: Record[]
  streamers?: any[]
  runs?: any[]
}
