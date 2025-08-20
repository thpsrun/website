import './App.css'
import { ThemeProvider } from '@/components/ui/theme-provider'
import { TopBar } from '@/components/top-bar'
import { Outlet } from 'react-router'

function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <div className="hero-container">
        {/* Background Image with Blur */}
        <div className="background-image" />

        {/* Optional overlay for better contrast */}
        <div className="background-overlay" />

        {/* Main Content Container */}
        <div className="w-full min-h-full max-w-[100rem] mx-auto p-12 flex flex-col gap-8">
          <TopBar/>
          <div>
            <Outlet/>
          </div>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
