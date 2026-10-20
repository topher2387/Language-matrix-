# Lesson engine review repair

Qwen authored the production and API documentation repair; controller authored adversarial regression tests and independently inspected the diff. Selector data can no longer set trust authority, index coercion is rejected, malformed reviewer collections raise ValueError, and string/bytes audio metadata fails closed.

Independent offline snapshot command: `python3 -B -m unittest discover -s tests -v` using the existing Forge test capsule (network disabled). Result: 44 tests, exit 0, 2026-10-19. Before repair the added regressions failed; the intermediate snapshot passed 15/16 lesson tests with the substring case still failing; after correction the full suite passed. Local detailed output: `.dev-harness/added-review/heartbeat-full-tests.json` in the controller checkout. No Korean-language, audio quality, P03 runtime or full-program acceptance is implied. Browser review and remaining CLI observations are separate pending work.
