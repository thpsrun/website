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
  platform: string
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
  players: Player // Player ID/name as string or "Anonymous"
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

// Detailed run with embedded game object (used in latest_wrs, latest_pbs)
export interface DetailedRun {
  id: string
  runtype: string
  game: Game // Full game object with embedded data
  category: string // Category ID as string
  level: string | null // Level ID as string or null
  subcategory: string
  place: number
  lb_count: number
  players: Player // Full player object with embedded data
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
