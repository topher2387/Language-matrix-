# P01 lesson engine

`language_matrix.lessons` provides two provider-neutral functions:

- `generate_lesson(input=None, provider=None, *, trusted_reviewers=(), available_audio=None)` returns a validated `lesson-v1` dictionary.
- `validate_lesson(data, trusted_reviewers=(), *, available_audio=None)` returns a defensive copy or raises `ValueError`.

Without a provider, generation selects deterministically from `fixtures/lessons.json` and works offline. `input` may be a fixture `lesson_id`, a topic/case string, an integer index, or a selector object containing `lesson_id`, `case`, `topic`, `subject`, `index`. An unknown selector falls back to the first fixture. A provider is called with the original input and may return a dictionary or JSON text; its output still goes through the same structural and semantic validation.

## Validation

Structure is checked with the installed `jsonschema` draft 2020-12 validator from `docs/contracts/lesson-v1.schema.json`. No parallel schema validator is used. Semantic checks then enforce:

- unique unit IDs and unique exercise IDs;
- every exercise `unit_id` exists;
- `correct_option` is within the exercise's option array;
- `teaching_unit`, `comparison`, and `audio` widgets reference units, while `exercise` widgets reference exercises;
- listening exercises reference a unit with audio whose ID is reported available by trusted local metadata;
- every `reviewed` or `verified` lesson/audio claim names a reviewer in `trusted_reviewers`.

Audio availability is never inferred from a reference alone. Callers may pass `available_audio` as a collection of asset IDs, a mapping from asset ID to `True`/metadata with `"available": true`, or a predicate. If omitted, only audio with trusted reviewed/verified metadata is treated as available.

Plain lesson strings are preserved exactly and remain inert text; no HTML escaping or rendering is performed here. Unverified content is not upgraded by validation. The functions and fixtures are language-only data APIs with no view-model or renderer.

## Trust Authority

Trust authority (`trusted_reviewers` and `available_audio`) must be passed explicitly as keyword arguments, not from selector objects. Selector objects may contain `lesson_id`, `case`, `topic`, `subject`, `index`, but not trust-related keys.

## Fixtures and acceptance status

`fixtures/lessons.json` contains five compact lessons and 25 provisional Korean teaching units covering nasalisation, liaison, aspiration, tensification, and palatalisation, each with structure, register, translation, and dialect notes. Every lesson and audio entry is marked `unverified`; no independent Korean review is claimed.

Still outstanding before linguistic acceptance:

- an accessible local/open-model generation benchmark on held-out expert-reviewed cases, with licences, memory use, and measured zero-cost operation;
- independent human Korean review of pronunciation, grammar, register, translation, and any audio;
- real audio assets and their trusted local availability metadata.

No model was loaded and no benchmark was attempted as part of this packet.
