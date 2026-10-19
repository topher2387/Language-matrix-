# Finite widget registry draft

| Type | `ref_id` resolves to | Renderer behavior |
| --- | --- | --- |
| teaching_unit | units[].unit_id | Co-display English, literal gloss, Hangul, spoken cue, phonology and verification label. |
| comparison | units[].unit_id | Render structure, register, translation and dialect notes as text. |
| exercise | exercises[].exercise_id | Render reading/listening options, check answer locally, announce feedback accessibly. |
| audio | units[].unit_id | Render the unit's trusted audio assets, voice selection, speed, repeat and explicit unavailable status. |

A widget is exactly `{type, ref_id}`. Unsupported types or extra properties fail validation. Never accept generated HTML, JavaScript, CSS, event handlers, network URLs, shell commands or plugins. Use fixed accessible elements and `textContent`; frontend CSP complements that rule. A teaching_unit renderer must always provide all four teaching surfaces, even when a separate comparison widget is absent. Responsive layout may stack them while keeping them simultaneously visible.

Audio should resolve asset IDs through a trusted local endpoint and verify media before playback. Never claim playable or verified audio from the presence of a reference alone. Tests must cover missing references/assets, unknown types, hostile text, option feedback and offline reload. The schema only validates structure; the consuming engine/GUI must validate reference integrity.
