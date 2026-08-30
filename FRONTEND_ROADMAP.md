# 🚀 FRONTEND ROADMAP: The Cyber-Diagnostic Interface

Welcome to the team, recruit. You're building the face of Pathfinder. We aren't making a "dashboard"—we're building a **Cyber-Diagnostic Terminal**. Think *Minority Report* meets *Cyberpunk 2077*.

## 🛠️ The Tech Stack
- **Framework:** Vite + React (Fast, modern, lean).
- **Styling:** Tailwind CSS (Utility-first for rapid iteration).
- **3D Engine:** React-Three-Fiber (R3F) + Three.js.
- **Animation:** Framer Motion (For those silky-smooth layout transitions).

## 🧠 The 'Cyber-Diagnostic' UI
The center of the app is the **Neural Core**. This is a 3D object that visually represents the user's career state.

### 1. The Neural Core (3D Visuals)
- **The Core:** A floating, iridescent sphere (Icosahedron) in the center of the screen.
- **Reactive Scaling:** 
    - **IQ Scale:** The sphere's size and rotation speed should scale with the `innovation_quotient`.
    - **Rarity Bloom:** Use a **Bloom Effect** (Post-processing). High `tech_rarity` = intense neon glow; low rarity = dim amber.
    - **Complexity Shaders:** Apply a GLSL noise shader to the surface. Higher `complexity` = more erratic, "electric" surface movements.
- **Glassmorphism:** Surround the core with floating, semi-transparent panels using `backdrop-blur-md` and thin white borders.

### 2. The Connectivity Layer (`usePathfinder.js`)
Don't pollute your components. Create a custom hook to manage the API state.

```javascript
// usePathfinder.js logic
export const usePathfinder = () => {
  const [state, setState] = useState({ loading: false, data: null, error: null });

  const predict = async (params) => {
    if (import.meta.env.VITE_MOCK_MODE === 'true') {
      return { data: MOCK_RESPONSE }; // Build UI without needing the backend!
    }
    // Implementation: fetch('/predict', { method: 'POST', ... })
  };

  return { ...state, predict };
};
```

## 🎨 Visual Direction
- **Palette:** Deep Space Black (`#050505`), Neon Cyan (`#00f3ff`), and Warning Amber (`#ffaa00`).
- **Typography:** A mix of a clean Sans-Serif (Inter) and a Mono-spaced font for "data readouts" (JetBrains Mono).
- **Interactions:** 
    - When `prediction_delta` loads, the 3D Core should "pulse" and expand to the `target_iq` size.
    - Use Framer Motion `AnimatePresence` for the roadmap phases to slide in from the right.

## 🚀 Deployment & Setup
1. **Env Vars:** Create a `.env` file in the root.
   - `VITE_API_URL=http://localhost:8000` (or your production URL).
   - `VITE_MOCK_MODE=true` (Set to false once the backend is live).
2. **Build:** `npm run build` $\rightarrow$ Deploy to Vercel/Netlify.

**Your goal:** Make the user feel like they're being analyzed by a super-intelligence. Go break things. ⚡️