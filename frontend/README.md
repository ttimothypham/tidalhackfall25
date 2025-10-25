# Frontend (minimal React via CDN)

This frontend is a minimal React app that uses the React UMD builds from a CDN — there is no build tool or npm required.

How to run locally

1. Serve the `frontend/` folder using a static HTTP server (so fetch works correctly). From the repository root run:

   ```bash
   # serve on port 3000
   python3 -m http.server 3000 --directory frontend
   ```

2. Open http://localhost:3000 in your browser.

Notes
- The app expects the backend Flask API to be running at http://localhost:5000
- If you run the backend elsewhere, edit `frontend/app.js` and change `API_BASE`.
