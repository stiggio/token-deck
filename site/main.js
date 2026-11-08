// Token Deck download page. No framework, no network calls: the page works without this file.
;(function () {
  'use strict'

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // ---- Copy buttons ----------------------------------------------------------------------------
  var live = document.getElementById('live')
  function announce(text) {
    if (!live) return
    live.textContent = ''
    window.setTimeout(function () { live.textContent = text }, 30)
  }
  function fallbackCopy(text) {
    var area = document.createElement('textarea')
    area.value = text
    area.setAttribute('readonly', '')
    area.style.position = 'fixed'
    area.style.opacity = '0'
    document.body.appendChild(area)
    area.select()
    var ok = false
    try { ok = document.execCommand('copy') } catch (e) { ok = false }
    document.body.removeChild(area)
    return ok
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'), function (button) {
    var source = document.getElementById(button.getAttribute('data-copy'))
    if (!source) return
    var timer = 0
    button.addEventListener('click', function () {
      var text = source.textContent.trim()
      var done = function () {
        button.setAttribute('data-copied', '')
        announce('Copied to the clipboard')
        window.clearTimeout(timer)
        timer = window.setTimeout(function () { button.removeAttribute('data-copied') }, 2000)
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () { if (fallbackCopy(text)) done() })
      } else if (fallbackCopy(text)) done()
    })
  })

  // ---- Which computer is this? -----------------------------------------------------------------
  // Hints only: every download stays visible, because Safari and Firefox expose no architecture.
  var install = document.querySelector('.install')
  var data = navigator.userAgentData
  var platform = (data && data.platform) || navigator.platform || ''
  var ua = navigator.userAgent || ''
  var os = /mac/i.test(platform) && !/iphone|ipad/i.test(ua) && navigator.maxTouchPoints < 2 ? 'mac'
    : /win/i.test(platform) ? 'windows' : ''
  if (install && os) {
    install.setAttribute('data-os', os)
    var row = install.querySelector('[data-os-row="' + os + '"]')
    if (row) row.setAttribute('data-current', '')
  }
  // On a phone, a tablet or Linux, say where the app runs before the visitor scrolls to the downloads.
  var away = document.querySelector('.away')
  if (away && !os) away.hidden = false
  if (os === 'mac' && data && data.getHighEntropyValues) {
    data.getHighEntropyValues(['architecture']).then(function (values) {
      var id = values.architecture === 'arm' ? 'dmg-arm' : values.architecture === 'x86' ? 'dmg-intel' : ''
      var link = id && document.getElementById(id)
      if (link) link.setAttribute('data-recommended', '')
    }).catch(function () {})
  }

  // ---- The hero deck ---------------------------------------------------------------------------
  // Opens on the welcome screen every deck shows before the app runs, then lights the keys into
  // Sessions. The metal buttons (drawn and listed under the drawing) switch screens, like the deck.
  var hero = document.querySelector('.hero-device')
  if (!hero) return
  var buttons = hero.querySelectorAll('[data-show]')
  var names = { agents: 'Agents', sessions: 'Sessions', models: 'Models & Usage' }
  function show(screen) {
    hero.setAttribute('data-screen', screen)
    Array.prototype.forEach.call(buttons, function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-show') === screen))
    })
    var svg = hero.querySelector('svg.deck')
    if (svg && names[screen]) svg.setAttribute('aria-label', svg.getAttribute('data-label-' + screen) || names[screen])
  }
  var touched = false
  Array.prototype.forEach.call(hero.querySelectorAll('[data-show], [data-mode-button]'), function (el) {
    el.addEventListener('click', function () {
      touched = true
      show(el.getAttribute('data-show') || el.getAttribute('data-mode-button'))
    })
  })
  show(hero.getAttribute('data-screen') || 'sessions')
  if (hero.getAttribute('data-screen') === 'welcome') {
    window.setTimeout(function () { if (!touched) show('sessions') }, reduceMotion ? 0 : 1400)
  }
})()
