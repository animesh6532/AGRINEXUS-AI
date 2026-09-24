# AgriNexus-AI Frontend

AgriNexus-AI is a high-precision Agricultural Intelligence Platform built with React, TypeScript, Vite, and Tailwind CSS.

## Location Architecture & Environment Setup

### 1. Mapbox Token Setup
Create `.env.local` inside the `frontend` directory:
```env
VITE_MAPBOX_TOKEN=your_mapbox_public_token_here
```
If `VITE_MAPBOX_TOKEN` is not provided, the application gracefully falls back to OpenStreetMap tile rendering and Nominatim geocoding services without crashing.

### 2. Browser Geolocation API & HTTPS Requirement
- **Local Development**: Testing device geolocation via `navigator.geolocation` works on `localhost` (http://localhost:5173).
- **Deployed Production**: Web browsers require a **Secure Context (HTTPS)** to access the `navigator.geolocation` API. Insecure HTTP production deployments will block device location access, and the UI will prompt the user to search for their field location manually.

### 3. Location Architecture
- **Single Source of Truth**: Managed by `LocationContext.tsx` (`agrinexus.location.v1` in `localStorage`).
- **No Hardcoded Defaults**: Fake fallbacks like `"Punjab, India"` or hardcoded coordinates (`19.076, 72.8777`) have been strictly removed. Unset state displays `"Set Location"`.
- **Search & Retrieve Flow**: Mapbox Search Box API uses a 2-step `/suggest` + `/retrieve` session flow with a 300ms debounce and AbortController request cancellation.
- **Selection vs Confirmation**: Searching or clicking the map sets a `pendingLocation`. Topbar, Dashboard, Weather, and ML pages update only after explicit confirmation via `[ Use This Location ]`.

