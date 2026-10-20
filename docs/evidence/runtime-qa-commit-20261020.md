# Runtime QA and proposal checkpoint

Free DeepSeek authored five complementary behavioral unittest methods in an isolated b286e8b snapshot, with fresh zero pricing and existing quota admission. Controller reviewed the actual test source and copied only its owned test file. Result metadata is recorded in free-runtime-qa-20261020.json; tests were independently executed, not inferred from worker prose.

Independent network-disabled source snapshot: `python3 -B -m unittest discover -s tests -v` — 61 tests passed, exit0. Cases cover malformed trusted config/grants without invocation, cancellation during retry/after output and invalid UTC clocks. Detailed local evidence: runtime-qa-final-tests.json. Proposal documentation JSON examples both parse, and git diff --check passes.

Qwen authored the draft contract proposal; controller corrected unsupported Korean/license assertions, invalid JSON and compatibility claims. It remains unregistered, with no schemas/registry changes. No new Korean/audio/UI acceptance or full P03 approval is claimed. No Lichen changes or paid fallback.
