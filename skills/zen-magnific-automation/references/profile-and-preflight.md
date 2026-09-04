# Profile and preflight

## Requirements

- Zen Browser. The archived scripts previously used `C:\Program Files\Zen Browser\zen.exe`.
- A compatible geckodriver executable.
- Selenium in the repo `.venv`.
- A local Zen profile whose Magnific login has been completed interactively.

Do not store profiles, cookies, login databases, screenshots, or geckodriver logs inside the skill or Git-tracked paths.

## Reuse an existing profile

1. Ensure no Zen process is using the profile.
2. Restore or copy the profile into a gitignored `workspace/<project>/` path.
3. Verify `cookies.sqlite` and required key/login files exist without printing cookie values.
4. Point the adapted automation script to the restored profile and current geckodriver.
5. Run a read-only DOM or selection probe before any configuration or generation action.

Quarantine batches are temporary. Inspect `.housekeeper/quarantine/*/manifest.json` for a recoverable profile and its `purge_after` timestamp; do not assume a dated batch still exists.

## Create a fresh profile

1. Launch Zen normally with a new local profile under `workspace/<project>/`.
2. Let the user complete Magnific login and any verification interactively, then close Zen fully.
3. Create a lean copy with:

   ```powershell
   .\.venv\Scripts\python.exe `
     skills\zen-magnific-automation\scripts\prepare_lean_zen_profile.py `
     --source "<full-profile>" `
     --target "<lean-profile>"
   ```

4. Use the lean copy for headless automation. Keep the full profile as the local recovery source until the task is complete.

The helper refuses to overwrite a target and only permits destinations below the repository's git-ignored `workspace/` directory. It copies only `prefs.js` and container metadata, plus a SQLite backup of the cookie database; it deliberately does **not** copy `logins.json`, `key4.db`, certificate stores, or other saved-login material. It normalizes the requested Magnific cookies from the historical `^userContextId=2` container to the default context and removes cookies for all other domains. If the service uses a separate identity domain, include that domain in a separately prepared profile or complete login interactively in the dedicated profile.

## Preflight checklist

- Zen binary, geckodriver, profile, Space URL, and output directory resolve to the intended absolute paths.
- No Zen process holds the source profile open.
- The Space loads past the login wall.
- The current board contains the intended node; rediscover IDs if necessary.
- Current model, resolution, Unlimited status, and credit dialog behavior are observed from the UI.
- The user has authorized any generation-capable click immediately before it occurs.
