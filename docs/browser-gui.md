# P02 browser GUI (packet #3)

Standalone, local-first browser tutor for the P00 `lesson.v1` contract. No frameworks, no
build step, no package downloads and no network URLs. Everything under `web/` is static.

## Files

| File | Role |
| --- | --- |
| `web/index.html` | Accessible shell: skip link, CSP meta, `<main id="lesson">`, manifest and script/style links. |
| `web/app.js` | Validation + finite widget renderer. Exports pure functions for tests and boots the DOM in the browser. |
| `web/styles.css` | Responsive layout: surfaces stay simultaneously visible and stack on narrow screens. |
| `web/sw.js` | Service worker caching the app shell and `lesson.json` for offline reload. |
| `web/lesson.json` | Bundled **unverified** P00 sample lesson (honestly labelled; no audio). |
| `web/manifest.json` | Web app manifest (`standalone`, scope `./`). Icons are intentionally omitted to avoid adding files outside this packet. |
| `tests/test_web.py` | Offline boundary tests (schema, references, static security checks, optional Node smoke). |
| `tests/browser-smoke.mjs` | Optional Node smoke test of the real validation/render code using a tiny built-in fake DOM. |

## Widget registry

The renderer implements exactly the four registry types and rejects anything else:

- `teaching_unit` → always emits **five** labelled `data-surface` blocks — `english`, `literal`
  (literal English gloss), `hangul`, `phonetics` (spoken phonetics) and `phonology` — plus the
  verification label. This covers the assignment's four teaching surfaces with the literal gloss
  as an additional fifth block, and all five stay simultaneously visible even when no separate
  comparison widget is present.
- `comparison` → structure/particles, register, translation note and dialect note as text.
- `exercise` → reading/listening options; answer checking is local and feedback is announced via
  `role="status"` + `aria-live="polite"`.
- `audio` → the unit's referenced asset/voice IDs, voice/speed/repeat controls and an explicit
  **unavailable** state. No audio is claimed or played.

A widget is exactly `{type, ref_id}`. Unknown types, extra properties, dangling references and
malformed lesson data fail validation and nothing is rendered (a rejection panel is shown).

## Input handling and security

- Every untrusted lesson string is placed with `textContent`. A literal `<script>` in a sentence
  stays inert text. `app.js` contains no `innerHTML`, `eval`, `document.write` or generated HTML.
- `index.html` carries a restrictive CSP (`default-src 'self'`, no inline script/style, no
  `object-src`, no `base-uri`, `connect-src 'self'`) and has no inline event handlers.
- The renderer re-validates structural **and** semantic rules the P00 schema cannot express:
  unique unit/exercise IDs, exercise→unit references, `correct_option` inside the option range,
  widget→reference type matching, and listening exercises needing an available audio reference.
- `reviewed`/`verified` claims require a non-whitespace reviewer, and the GUI labels verified
  content as a *claim* that is not independently authenticated here.

## Audio honesty

P05 (trusted asset store) is not a dependency of this packet, so no asset can be verified or
played. The audio widget always renders `data-audio-state="unavailable"`, disables voice/speed/
repeat/play controls and lists referenced IDs only. This is deliberate: presence of an asset
reference is never treated as playable or verified audio.

## Serve locally

From the repository root:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000/web/> (or serve `web/` directly as the document root). A file
server is required because the app fetches `./lesson.json`; opening `index.html` via `file://`
will show a load error instead.

## Offline behaviour

After the first successful load the service worker precaches `index.html`, `app.js`, `styles.css`,
`lesson.json`, `manifest.json` and the scope root. On the next visit (including offline) requests
are served cache-first, and navigations fall back to the cached `index.html`. Reload with the
network disabled to confirm cached lessons still work.

## Tests

```sh
python3 -B -m unittest discover -s tests -v
```

`tests/test_web.py` runs offline. It validates `web/lesson.json` against the P00 schema, checks
reference/security invariants across the static assets and, when `node` is available, runs
`tests/browser-smoke.mjs`. The smoke test exercises the real `validateLesson`/`renderLesson` code
against a minimal in-file fake DOM: unknown widgets, dangling refs, malformed units/listening
exercises, out-of-range answers, hostile text inertness, all five surface blocks, local answer
feedback and the unavailable audio state. It uses
only Node built-in modules and downloads nothing. If `node` is absent the smoke test is skipped
and the static checks remain authoritative.

## Limitations / blockers

- The bundled lesson is an unverified development fixture. Passing validation is not evidence of
  Korean accuracy, review, or audio quality.
- No audio is available or verified; no verified Korean content is faked.
- P01 engine output, P05 asset store and P03 runtime are not assumed. If a real asset resolver or
  a schema expansion is required, this packet stops and reports rather than expanding the schema.
- Requires an HTTP origin for `fetch` and service-worker registration; `file://` is unsupported.
- Manifest icons are omitted (they would require files outside the owned set).
