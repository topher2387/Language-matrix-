# CLI review repair

The library boundary now whitelists lesson and capability-request schema names, matching the CLI. Loaded schemas reject every non-fragment `$ref` before validator construction. Current registry contracts use internal refs; no existing network exploit is claimed. External/relative refs are deliberately unsupported by this offline validator.

Qwen authored production checks. Controller replaced weak/mock false-positive tests with direct library regressions: unknown/pathlike names reject before any file open; HTTP/HTTPS/file/relative/protocol-relative references reject before validator construction/check_schema; internal refs still accept valid values and reject wrong types. Controller cwd/schema-shadowing tests are preserved. Registry contracts unchanged.

Independent network-disabled snapshot command: `python3 -B -m unittest discover -s tests -v`; result 47 tests, exit0 on2026-10-20. Count reduced from49 after consolidating weak/redundant tests into meaningful parameterized cases. Local evidence: cli-final-tests.json in controller added-review directory. Full integration/free-review/live-browser follow-up and P03 acceptance remain pending.
