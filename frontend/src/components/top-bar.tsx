import { NavMenu } from "./nav-menu"
import { Logo } from "./logo"
import { Socials } from "./socials"

export const TopBar = () => {
  return (
    <div className="w-full h-8 bg-background p-6 flex items-center justify-between rounded-lg z-1">
      <div className="flex items-center space-x-4">
        <Logo/>
        <NavMenu/>
      </div>
      <Socials/>
    </div> 
  )
}
