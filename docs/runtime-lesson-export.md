# Runtime Lesson Export Tool

This tool exports lesson-v1 JSON from existing generate_lesson fixture results through a trusted runtime environment.

## Usage

```bash
python3 tools/export_runtime_lesson.py [--lesson-id ID] [--no-grants] [--cancelled]
```

### Arguments

- `--lesson-id ID`: Specify a lesson ID from fixtures/lessons.json (optional, defaults to "nasalisation-1")
- `--no-grants`: Run without any granted permissions (will fail with permission error)
- `--cancelled`: Run with cancelled function that returns True immediately (will fail with cancellation error)

## Features

- **Trusted Runtime**: Uses a trusted HandlerSpec binding with proper permission checks
- **Fixture Validation**: Only accepts exact string IDs from fixtures/lessons.json
- **Dynamic Deadline**: Sets UTC deadline to NOW+5 minutes
- **Language Support**: Always uses "ko" language as specified
- **Cross-CWD Support**: Works from any working directory
- **Error Handling**: Returns JSON-only stdout on success, ValueError to stderr on failure

## Examples

Export default lesson:
```bash
python3 tools/export_runtime_lesson.py
```

Export specific lesson:
```bash
python3 tools/export_runtime_lesson.py --lesson-id liaison-1
```

Run without grants (will fail):
```bash
python3 tools/export_runtime_lesson.py --no-grants
```

Run with cancelled execution (will fail):
```bash
python3 tools/export_runtime_lesson.py --cancelled
```

## Notes

- The tool only accepts lesson IDs that exist in fixtures/lessons.json
- No automatic fixture overwrite or bundled operations
- All outputs are written to stdout as JSON
- No network access is allowed during execution
- Only local execution is supported (no remote capabilities)
- Generated lessons are validated against the lesson.v1 schema
- Outputs remain unverified fixtures; export confers no Korean, audio or teaching approval
- Audio files are not included in exported lessons

## Exit Codes

- `0`: Success
- `1`: Execution or validation error written to stderr
- `2`: Invalid CLI arguments (argparse diagnostic on stderr)
To save JSON manually without replacing the bundled fixture:

```bash
python3 tools/export_runtime_lesson.py --lesson-id liaison-1 > /tmp/lesson.json
```

From another working directory, pass the absolute path to the script. The runtime is cooperative and invokes trusted local handlers; it is not a process sandbox.
