# Controller audit, 2026-10-20 UTC

Reviewed recent Language Matrix PR work (#25, #23, #22) and current Qwen patch. Corrected malformed permission authority and deadline helper handling, stale validation expectations, missing reserved-contract assertion, and misleading integration examples. Request validation now rejects malformed structure before semantic access, binds capability/output and refuses unavailable contracts. Supervisor grants default empty and must be an explicit validated collection. Examples are blocked validation previews, never fake execution.

Independent offline source snapshot checks: integrated lesson/browser/CLI baseline 47 Python tests passed; browser Node suite 59 checks passed; P03 branch 34 tests passed; combined latest integration branch plus P03 files 74 tests passed (exit 0). New malformed-authority/deadline regressions first reproduced 4 failing subtests and 8 error subtests; helper correction made them pass. Existing integration failures reproduced expired dates/unavailable schemas; revised examples retain refusal and expose blocked state. No network/packages downloaded in tests. git diff --check passes.

These results establish validation/helper/example repairs, not full P03 acceptance. Handler invocation, independently enforced authority at execution, lifecycle/cancellation/retries/timeouts and actual result validation remain the next job. P04/P05 remain blocked. No merges, Korean quality or playable-audio acceptance claimed. Lichen was read only and not modified.

Source SHA256 before evidence commit:

```json
{
  "language_matrix/capabilities.py": "c10af2fa1be0d0f35eda812a9e76c6e493016678e2ce028d9e04758727fa0f1c",
  "tests/test_capabilities.py": "80e27b238803d50b4a9ca0adab942f07396fc059f6e75bda403f79ad7777deff",
  "integration_example.py": "7ba8facfe208eaaecade91b079208fbdad9d891674c8a0557abcdaf9e824cacc",
  "tests/test_integration.py": "91a5c831aabc6738ac3ea2e18204c325bbe50d65307f0f0aceaa27a046c86a24",
  "docs/capability-runtime.md": "ca2af0a56a6e5812739c93a3bb6c4cf83d5229c530bfb77bc0e73f5462ce3447"
}
```
