import { SiDiscord, SiTwitch, SiYoutube } from "@icons-pack/react-simple-icons"

export const Socials = () => {
    return (
        <div className="flex items-center space-x-4">
            <SiDiscord className="w-5 h-5 cursor-pointer text-ring hover:text-white transition-colors duration-200 ease-in-out" />
            <SiTwitch className="w-5 h-5 cursor-pointer text-ring hover:text-white transition-colors duration-200 ease-in-out" />
            <SiYoutube className="w-5 h-5 cursor-pointer text-ring hover:text-white transition-colors duration-200 ease-in-out" />
        </div>
    )
}
