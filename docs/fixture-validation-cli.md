# Offline Fixture Validation CLI

This tool provides offline validation of Language Matrix contract fixtures against their JSON schemas.

## Usage

```bash
python3 tools/validate_fixture.py SCHEMA FILE
```

Where:
- `SCHEMA` is either `lesson` or `capability-request`
- `FILE` is the path to the fixture JSON file to validate

## Exit Codes

- `0`: Valid fixture (structurally correct)
- `1`: Invalid fixture (fails schema validation)
- `2`: CLI usage error, malformed JSON, or unreadable file

## Examples

Validate a lesson fixture:
```bash
python3 tools/validate_fixture.py lesson docs/contracts/sample-lesson.json
```

Validate a capability request fixture:
```bash
python3 tools/validate_fixture.py capability-request docs/contracts/sample-capability-request.json
```

## Validation Scope

This tool validates only the structural integrity of fixtures against their JSON schemas. It does not:

- Evaluate Korean language quality or accuracy
- Check runtime permissions or capabilities
- Verify that fixture content is appropriate for educational use
- Validate that audio assets are available or accessible

The validation ensures that fixtures conform to the expected structure and data types defined in the contracts, but does not assess semantic correctness or educational value.

## Implementation Details

- Uses JSON Schema Draft 2020-12 validator
- Resolves schemas relative to repository root
- Works independently of current working directory
- No network access or remote references
- All validation happens offline