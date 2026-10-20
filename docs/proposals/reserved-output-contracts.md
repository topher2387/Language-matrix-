# Reserved output contracts — draft proposal

**DRAFT — NOT REGISTERED.** This document is for the existing human schema-review gate. It creates no schema, activates no capability and grants no teaching/audio approval. Numeric bounds below are proposed implementation limits, not measured model capability.

## Shared envelope and trust

Propose `schema_version: "1.0"`, bounded IDs matching the existing contract ID pattern, and `verification` matching existing status/reviewer/notes conventions. Generated examples start `unverified`, reviewer null. Runtime pending/ready/failure is separate from content verification; ready never means linguistically reviewed. Unknown properties should be rejected by a future schema.

## audio-asset.v1

Proposed required fields:

| Field | Proposed type/bound | Meaning |
|---|---|---|
| schema_version | constant string 1.0 | Contract version |
| asset_id | existing ID pattern, max128 chars | Immutable local store key |
| voice_id | existing ID pattern, max128 chars | Stable voice identity, not a quality claim |
| content_hash | 64 lowercase hex chars | SHA256 of exact stored bytes |
| format | enum wav | Initial narrow format; expanding formats requires review |
| sample_rate_hz | integer 8000–96000 | Stored audio metadata |
| channels | integer 1–2 | Stored audio metadata |
| duration_seconds | finite number >0 and <=600 | Metadata checked against decoded content by store adapter |
| provenance | bounded object | Source text hash, local generator ID and generation UTC time |
| license_info | bounded object | License/consent evidence reference, or explicit unknown |
| verification | existing verification object | Independent content-review state |

The trusted local store must bind asset_id to content_hash atomically and verify decoded metadata before playback. Neither an ID nor model-declared metadata proves bytes exist. No arbitrary paths, executable content, base64 payload or remote playback URLs. Voice provenance/consent is separate from the generated asset license. Unknown licensing cannot be silently represented as permission to redistribute.

Illustrative shape only, no actual generated audio or license claimed:

```json
{"schema_version":"1.0","asset_id":"audio-example","voice_id":"voice-example","content_hash":"0000000000000000000000000000000000000000000000000000000000000000","format":"wav","sample_rate_hz":24000,"channels":1,"duration_seconds":1.0,"provenance":{"source_text_sha256":"0000000000000000000000000000000000000000000000000000000000000000","generator_id":"fixture-example","generated_at_utc":"2026-10-20T00:00:00Z"},"license_info":{"status":"unknown","evidence_id":null},"verification":{"status":"unverified","reviewer":null,"notes":"Illustrative metadata; no audio bytes or consent evidence supplied."}}
```

Negative cases: negative/nonfinite duration; unsupported format; malformed hash; missing voice/provenance; path/URL substituted for asset ID; asset ID resolves to different bytes. Schema validation handles shape; store/decoder checks handle existence, hash and metadata agreement.

## phonology-report.v1

Propose required `schema_version`, `report_id`, `source_text`, `source_language`, `target_language`, `analysis_units`, `provenance`, `verification`. Text limits follow existing lesson text bounds; proposed at most100 units, each with unique unit_id, source segment offsets, original segment, explanatory analysis and optional transcription with an explicit notation label. Offsets must refer to the source text under a documented Unicode indexing convention. Do not equate learner spelling with IPA. A report cannot upgrade lesson verification automatically.

Illustrative non-teaching shape:

```json
{"schema_version":"1.0","report_id":"report-example","source_text":"example","source_language":"en","target_language":"ko","analysis_units":[{"unit_id":"unit-example","start":0,"end":7,"segment":"example","analysis":"Placeholder only; no Korean pronunciation claim.","transcription":null}],"provenance":{"method_id":"fixture-example","evidence_ids":[]},"verification":{"status":"unverified","reviewer":null,"notes":"Shape illustration; not reviewed teaching material."}}
```

Negative cases: duplicate unit IDs, dangling/out-of-range offsets, segment mismatch, unsupported notation label, verification claim without reviewer provenance. No invented confidence/quality scores.

## Compatibility and decisions before activation

Existing lesson audio references contain asset_id, voice_id and verification; keep those references compact and resolve full metadata through a trusted store. Existing lesson units contain phonology text, not a report-reference field: adding report references would be a separate lesson contract change, not automatic compatibility.

Human review must decide: exact field names/bounds and Unicode indexing; immutable store mapping/hash and decoded-metadata checks; voice identity/consent/license evidence handling; format scope; trusted reviewer authority and source-evidence requirements; and whether lesson report references need a separate version. After review, add schemas/negative fixtures, independent tests and adapters in dependency order. Reserved runtime contracts remain blocked until explicitly registered after that gate. No P03/P04/P05 acceptance follows from this document.

Authorship: Qwen supplied the initial proposal; controller removed unsupported phonetic/license claims, invalid JSON comments and unproven compatibility, and made bounds/trust decisions explicit. Examples are illustrative and unregistered.
