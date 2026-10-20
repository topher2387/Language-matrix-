# Mock Audio Runtime Test Plan
## DRAFT - Waiting Human Approval

This test plan outlines the mock testing scenarios for the audio runtime capability.

### Test Scenarios

1. **Provider Status Tests**
   - Pending status validation
   - Ready status validation  
   - Failure status handling

2. **Access Control Tests**
   - Denied grants validation
   - Precancelled requests
   - Deadline expiration handling

3. **Metadata Validation Tests**
   - Malformed metadata detection
   - Invalid asset_id patterns
   - Incorrect sample_rate_hz values
   - Invalid channel counts

4. **Content Verification Tests**
   - Forged reviewer claims
   - Invalid license information
   - No actual bytes scenario

5. **Multi-Speaker Request Tests**
   - Single asset output (as per draft)
   - Multi-speaker interpretation using existing {language,text} input
   - Note: Multi-speaker aggregation requires exact bounded design/review

### Implementation Notes
- Proposal-only validation is already complete. Active capability/mock-provider tests start only after explicit schema-registration approval; passing them does not replace human/content approval.
- No actual activation or production changes
- Only mock provider testing scenarios
- Single asset output is the current draft limitation
### Expected evidence after schema approval
- Denied grants, pre-cancellation or already-expired deadline: zero provider attempts and no output.
- Valid mock response: pending then ready, one attempt, schema-valid detached metadata; content remains unverified and no playback/bytes are claimed.
- Provider exception or malformed output: pending then failure with no released output; retries obey fixed attempt/deadline limits.
- In-flight cancellation/deadline: cooperative refusal of late output; do not claim preemptive process termination.
- Forged reviewer/license IDs: schema presence alone cannot authorize them. Separate trusted lookup must fail closed; actual teaching/playback remains blocked until store/consent/reviewer checks exist.
- Multi-speaker acceptance needs an explicit bounded coordinator design. Multiple single-asset responses are not automatically a dialogue contract or full issue #4 acceptance.

Controller review: source/test changes are not authorized by this draft; it is preparation only. The schema decision concerns exact commit5740000 and remains pending.
