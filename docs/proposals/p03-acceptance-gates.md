# P03 acceptance gates (DRAFT - not approval)

## Status

- `lesson.v1` runtime/export/browser tests: 130 passed
- Schema hardening integrated suite: 145 passed at current snapshot (MiMo bounded patch review approved; full P03 remains unaccepted)
- Issue #4 multi-speaker mocked pending/ready/failure: blocked by human approval of reserved audio contract
- Full milestone verified Korean audio: absent
- P04/P05: held until accepted P03

## Current state

Quota correction: token cap is 10M/day; the 20% reserve reduces request admission, not the token cap. Large worker envelopes were deferred; smaller read-only MiMo reviews were admitted through the existing ledger without resets, refunds or policy changes. Availability must be checked before every admission.

## Next human decision required

Review existing `docs/proposals/reserved-output-contracts.md` in PR #23 commit 398d56e; explicitly approve/revise audio asset/phonology contracts before activation.

## Notes

- No production/test/schema edits or approval claims
- All work remains within the bounds of the existing contract
- The runtime is not a sandbox and cannot preempt non-cooperating handlers
- Only `lesson.v1` has a present fixed output contract; reserved contracts are blocked
