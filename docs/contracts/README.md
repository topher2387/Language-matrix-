# P00 contract boundary (v1.0)

The JSON Schemas are the authoritative structural interface for P01/P02/P03. Validate with JSON Schema draft 2020-12 before caching or rendering. All objects reject unknown keys, arrays/text are bounded, and schema versions are exact. `sample-lesson.json` and `sample-capability-request.json` are offline development fixtures. Their content is **unverified**: passing structural tests is no evidence of Korean accuracy, dialect authenticity, voice quality, or permission to execute.

Run `python -m unittest discover -s tests -v`. The local validator is pinned in `requirements-dev.txt`; no generation or paid service is needed.

## Lesson interpretation

Every unit requires natural English (`english`), a literal English gloss (`literal_english`), Hangul, approximate spoken phonetics, phonology explanation, structure/particle comparison, register, subtitle/translation note, dialect note and an array of audio references. Empty audio arrays honestly represent unavailable media. `verification` belongs to the lesson and each audio reference, and always records status, reviewer (nullable), and notes. Reviewed/verified structural claims require a nonempty, non-whitespace reviewer name; this does not authenticate that reviewer. `verified` must be awarded by trusted review workflow, never inferred from model output or schema validity. Unknown review provenance must fail semantic validation before a verified claim is shown.

P01 semantic checks must enforce unique unit/exercise IDs, existing exercise/unit references, answer indices smaller than option count, widget references matching their type, available audio for listening exercises, and trusted verification provenance. JSON Schema does not enforce cross-object references or these review decisions. Deterministic fixture coverage is distinct from independent Korean review. Labels must preserve that distinction.

Audio entries contain asset IDs and voice IDs, not URLs or paths. Resolve via a trusted asset-store lookup that verifies licence, checksum, review status and media type before serving. Until P05, absent assets render a clear unavailable state.

## Capability interpretation

Requests describe a task; validation does not execute it. `capability` is the task name; `rationale` records the educational purpose; `input` is bounded text, Korean language, optional voice ID/seed. `output_schema` names a registry-owned output contract, never executable schema supplied by the model. `permissions` declares requested operations, not granted authority. `deadline_utc` is an absolute UTC timestamp; P03 must parse a real calendar date and refuse expired requests. Policy caps requests at zero dollars, no network, 1–3 attempts and 1–300 seconds. Cancellation/deadline checks belong in runtime, not just schema.

P03 must map lesson.generate→lesson.v1, phonology.check→phonology-report.v1, tts.synthesize→audio-asset.v1, asr.transcribe→transcript.v1, image.generate→image-asset.v1; reject mismatches, unregistered handlers, unavailable providers and ungranted permissions. Non-lesson output schemas are reserved names until their packet defines validated output. ASR media references and multi-speaker grouping need an explicit reviewed additive schema revision before accepting those request shapes; do not smuggle paths/base64/URLs into text.

Local-only is the deliberately narrow initial policy. Optional free hosted capacity requires an explicit reviewed schema/policy update with verified provider terms/quotas/privacy; it is not an implicit fallback. No shell, code, credentials, endpoints, billing activation or commits are request capabilities. Plain lesson strings are untrusted text, never HTML; a literal `<script>` inside a sentence must remain inert through `textContent` rendering. Schema rejection of code keys is not an HTML sanitizer.

## Compatibility

Keep v1.0 consumers strict. Any structural expansion requires coordinated schemas, fixtures, engine, GUI and runtime changes plus tests. Human schema review is required before architectural changes merge. No runtime import, symlink or write into Lichen is permitted. See harness-inspection.md for observed external interfaces and constraints.
