// API Response Types

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
  awards: any[]
  stats: {
    total_pts: number
    main_pts: number
    il_pts: number
    total_runs: number
  }
}

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

export interface RunPlayer {
  player: Player | null
  url: string
  date: string
}

export interface Run {
  game: Game
  subcategory: string
  time: string
  players: RunPlayer[]
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

export interface DetailedRun {
  id: string
  runtype: string
  game: Game
  category: string
  level: string
  subcategory: string
  place: number
  lb_count: number
  players: Player
  date: string
  record: string
  times: Times
  system: System
  status: Status
  videos: Videos
  variables: Record<string, any>
  meta: Meta
  description?: string | null
}

export interface ApiResponse {
  streamers: any[]
  runs: Run[]
  new_runs: DetailedRun[]
  new_wrs: DetailedRun[]
}
