# iPhone Dashboard

Repo Foundry can run like a clean phone app for directing agents and watching progress.

## Start Phone-Reachable Services

Terminal 1:

```powershell
cd C:\Users\Garrett\Desktop\AUTOREPO
.\scripts\rf.ps1 run-mobile
```

Terminal 2:

```powershell
cd C:\Users\Garrett\Desktop\AUTOREPO\dashboard\frontend
pnpm run dev:mobile
```

Open from the iPhone using the PC's LAN or Tailscale IP:

```text
http://<PEREGRIN-IP>:5274
```

The frontend will call the API on the same hostname at port `8765`.

## Add to Home Screen

In Safari:

1. Open `http://<PEREGRIN-IP>:5274`.
2. Tap Share.
3. Tap Add to Home Screen.

The dashboard includes PWA metadata, an app icon, iOS web-app tags, and mobile-first ordering so the most important phone actions appear first:

- Direct the Agents
- Autonomous Completion
- Human Direction Queue
- Agent progress, logs, and artifacts

## Network Notes

- Windows Firewall may need to allow ports `5274` and `8765`.
- If you use Tailscale, prefer the Tailscale IP so the dashboard works away from the LAN.
- Keep `GH_TOKEN`/`GITHUB_TOKEN` on the PC or GitHub Actions side. Do not put tokens on the phone.
