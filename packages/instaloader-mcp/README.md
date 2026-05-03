# Instaloader MCP

Local FastMCP server for Instagram research using Instaloader.

## Tools

- `get_profile` - profile metadata by username
- `get_recent_posts` - recent public post metadata for a username
- `get_post` - post metadata by shortcode
- `download_recent_posts` - download recent posts into `workspace/instagram/`

## Optional Login Session

For endpoints that require an authenticated Instagram session, create an Instaloader session outside MCP and set:

```bash
export INSTALOADER_SESSION_USERNAME=your_username
export INSTALOADER_SESSION_FILE=/path/to/session-your_username
```

If `INSTALOADER_SESSION_FILE` is omitted, Instaloader uses its default session location.
If `INSTALOADER_SESSION_USERNAME` is omitted, the server falls back to `INSTALOADER_USERNAME`.
When no session file exists, `INSTALOADER_USERNAME` and `INSTALOADER_PASSWORD` can be used to create one.
