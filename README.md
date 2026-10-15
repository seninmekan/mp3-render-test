# MP3 service - limited technical trial

**Experimental**: whether a cloud-hosted yt-dlp can access YouTube is not verified. Use ONLY content you own or are authorized to download. Check platform terms. Never expose the service publicly without additional anti-abuse controls.

## Render
1. Create a public or private GitHub repo and upload these files at the root.
2. Render > New > Web Service > select repository > Environment `Docker`.
3. Select **Free** instance if shown. DO NOT choose a paid plan.
4. Under Environment, add `API_TOKEN` with a long random secret (at least 32 chars). Do not publish the token in GitHub.
5. Deploy. Open the provided service URL and verify `/` returns a JSON status.

## Test locally (requires Docker)
`docker build -t mp3-test .`
`docker run --rm -p 10000:10000 -e API_TOKEN=CHANGE_ME mp3-test`

For a permitted, short test video:
`curl -X POST https://YOUR-APP.onrender.com/convert -H "Content-Type: application/json" -H "X-API-Token: YOUR_SECRET" -d '{"url":"https://www.youtube.com/watch?v=YOUR_VIDEO"}' -o test.mp3`

**Security/limits**: the API key must remain server-side. Do not embed it into a public `index.html` or expose a public POST proxy. This service is for private testing, NOT production. It lacks job queue, rate limiting, concurrency locking, user authentication, and usage quotas. A browser-based public frontend cannot safely call it with the secret directly; production needs a server-side authenticated relay / signed job flow and abuse controls. Cloud IP blocks, quotas, CORS, extraction changes, and hosting usage policies may prevent conversions. `MAX_MINUTES` defaults to 15; job timeout 180s.
