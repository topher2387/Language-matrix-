# Audio asset contract review decision (draft, unregistered)

This proposed metadata schema and sample are preparation for human review. They do not register audio-asset.v1, enable playback, establish media bytes, or accept P03.

Proposed bounds: WAV only, 8–96 kHz, one or two channels, duration >0 through600 seconds, 128-character asset/voice IDs, 64-character generator/evidence/reviewer IDs, SHA-256 lowercase hexadecimal. Unknown license requires null evidence; evidenced license requires an evidence ID. Unverified content requires null reviewer; reviewed/verified require reviewer ID. These are shape constraints, not trusted authority.

Before activation, decide whether these exact fields/bounds and the evidenced-license vocabulary are acceptable. Confirm how128-character IDs map to existing compact lesson references; no lesson-contract compatibility is inferred. The draft remains separate from active contracts.

Future trusted adapters must verify actual bytes/hash, decoded metadata, source-text binding, calendar-valid UTC timestamps, license/voice-consent evidence and trusted reviewer authority. Default jsonschema format checking may not enforce date-time without optional dependencies; lexical bounds here do not prove calendar validity. Strict JSON input must reject nonfinite numbers. No consumer should treat schema-valid metadata or a ready runtime result as permission to play/canonicalize content.

Authorship: Qwen wrote the initial draft; controller relocated it, corrected conflicting null/required/license/reviewer constraints, supplied the illustrative sample, strengthened timestamp lexical bounds and added independent negative tests. No actual audio or license is represented by placeholder hashes.
