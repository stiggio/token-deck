/**
 * The settings window has the preload bridge (window.tokenDeck), which can run updates, edit agent
 * settings and write to the deck. Only the app's own renderer may ever load in it or call it;
 * any other link opens in the user's browser.
 */

/** A local file URL's path, decoded; null for anything else, including a file on a network share. */
function localFilePath(url: string): string | null {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'file:' || (parsed.host && parsed.host !== 'localhost')) return null
    return decodeURIComponent(parsed.pathname)
  } catch {
    return null
  }
}

/**
 * Whether `url` is the app's own page, `appUrl`: the dev server in development (any path on it),
 * the bundled index.html otherwise (that exact file, with any #route).
 */
export function isAppUrl(url: string, appUrl: string, windows = process.platform === 'win32'): boolean {
  if (!url || !appUrl) return false
  if (appUrl.startsWith('file:')) {
    const page = localFilePath(url)
    const app = localFilePath(appUrl)
    if (!page || !app) return false
    return windows ? page.toLowerCase() === app.toLowerCase() : page === app
  }
  const base = appUrl.replace(/\/+$/, '')
  return url === base || url.startsWith(base + '/') || url.startsWith(base + '#') || url.startsWith(base + '?')
}

/** Links that may leave the app: https only, opened in the default browser. */
export function isExternalLink(url: string): boolean {
  return /^https:\/\/[^\s]+$/i.test(url)
}
