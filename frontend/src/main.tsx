import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { startSocketBridge } from './services/socket/socketBridge.ts';
import { startScenarioBridge } from './services/scenario/ScenarioBridge.ts'

// Start real-time socket listeners and scenario sync before rendering
startSocketBridge();
startScenarioBridge();
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Enables client-side routing */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)