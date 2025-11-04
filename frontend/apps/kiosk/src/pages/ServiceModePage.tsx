// ServiceModePage.tsx
//
// Purpose:
// Dedicated page for Kiosk Service Mode. Renders fullscreen media (if available) and a hard input-blocking overlay.
// Other app processes continue under the hood (SSE, contexts, timers). The overlay denies all user input.
//
// Behavior:
// - Uses ServiceModeStore to get isActive and pictureName
// - Displays ServiceModeMediaDisplay for the given picture (or fallback text if null/not cached)
// - Mounts ServiceModeOverlay to block ALL inputs while active

import { FunctionComponent } from 'react'
import { useServiceModeStore } from '../stores/ServiceModeStore'
import ServiceModeMediaDisplay from '../components/ServiceModeMediaDisplay'
import ServiceModeOverlay from '../components/ServiceModeOverlay'

const ServiceModePage: FunctionComponent = () => {
  const { isActive, pictureName } = useServiceModeStore()

  return (
    <div className="w-full h-[100vh] bg-black relative overflow-hidden">
      {/* Media content or fallback text */}
      <ServiceModeMediaDisplay pictureName={pictureName} className="absolute inset-0" />

      {/* Hard input blocking overlay */}
      <ServiceModeOverlay isVisible={isActive} />
    </div>
  )
}

export default ServiceModePage