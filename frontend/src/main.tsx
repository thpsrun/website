import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Provider as JotaiProvider } from 'jotai'
import './index.css'
import App from './App.tsx'
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router";
import { MainPage } from './components/main-page.tsx'
import { GameOverview } from './components/game-overview.tsx'

// Create a client for React Query
const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    children: [
      { index: true, Component: MainPage },
      { path: "game", Component: GameOverview }
    ]
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <JotaiProvider>
        <RouterProvider router={router} />
      </JotaiProvider>
    </QueryClientProvider>
  </StrictMode>,
)
