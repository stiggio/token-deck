/**
 * The settings window has the preload bridge (window.tokenDeck), which can run updates, edit agent
 * settings and write to the deck. Only the app's own renderer may ever load in it or call it;
 * any other link opens in the user's browser.
 */

/** Whether a URL is the app's own renderer: the dev server in development, the bundled page otherwise. */
export function isAppUrl(url: string, devUrl?: string): boolean {
  if (!url) return false
  if (devUrl) {
    const base = devUrl.replace(/\/+$/, '')
    if (url === base || url.startsWith(base + '/') || url.startsWith(base + '#') || url.startsWith(base + '?')) return true
  }
  if (!url.startsWith('file:')) return false
  const pathOnly = url.split('#')[0]!.split('?')[0]!
  return pathOnly.endsWith('/renderer/index.html')
}

/** Links that may leave the app: https only, opened in the default browser. */
export function isExternalLink(url: string): boolean {
  return /^https:\/\/[^\s]+$/i.test(url)
}
