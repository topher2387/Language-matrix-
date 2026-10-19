"""P02 web GUI boundary checks: validation, reference integrity and offline assets."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
CONTRACTS = ROOT / 'docs' / 'contracts'

REQUIRED_FILES = (
    'index.html',
    'app.js',
    'styles.css',
    'sw.js',
    'lesson.json',
    'manifest.json',
)


class WebAssetsTest(unittest.TestCase):
    def read(self, name):
        return (WEB / name).read_text(encoding='utf-8')

    def test_owned_assets_exist(self):
        for name in REQUIRED_FILES:
            with self.subTest(name=name):
                self.assertTrue((WEB / name).is_file(), f'web/{name} must exist')

    def test_bundled_lesson_matches_p00_schema(self):
        schema = json.loads((CONTRACTS / 'lesson-v1.schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        lesson = json.loads(self.read('lesson.json'))
        errors = list(Draft202012Validator(schema).iter_errors(lesson))
        self.assertEqual([], errors, 'web/lesson.json must validate against the P00 lesson schema')

    def test_bundled_lesson_is_honestly_unverified(self):
        lesson = json.loads(self.read('lesson.json'))
        self.assertEqual('unverified', lesson['verification']['status'])
        self.assertIsNone(lesson['verification']['reviewer'])
        self.assertIn('unverified', lesson['verification']['notes'].lower())
        self.assertTrue(lesson['units'], 'lesson must contain units')
        for unit in lesson['units']:
            self.assertEqual([], unit['audio_assets'], 'no audio may be faked as available')

    def test_bundled_lesson_renders_all_registered_widget_types(self):
        lesson = json.loads(self.read('lesson.json'))
        types = [widget['type'] for widget in lesson['widgets']]
        self.assertIn('teaching_unit', types)
        self.assertIn('comparison', types)
        self.assertIn('exercise', types)
        self.assertIn('audio', types)

    def test_manifest_is_local_and_complete(self):
        manifest = json.loads(self.read('manifest.json'))
        for field in ('name', 'short_name', 'start_url', 'display', 'scope'):
            self.assertIn(field, manifest)
        self.assertEqual('standalone', manifest['display'])
        for value in manifest.values():
            if isinstance(value, str):
                self.assertNotRegex(value, r'^https?://', 'manifest must not reference network URLs')

    def test_index_references_local_assets_and_csp(self):
        html = self.read('index.html')
        self.assertIn('<html lang="en">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn('rel="manifest" href="manifest.json"', html)
        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js" defer', html)
        self.assertIn('Content-Security-Policy', html)
        self.assertIn("default-src 'self'", html)
        self.assertIn('id="lesson"', html)
        self.assertNotRegex(html, r'\son[a-z]+\s*=', 'no inline event handlers are permitted')
        self.assertNotIn('http://', html)
        self.assertNotIn('https://', html)

    def test_app_js_uses_text_content_and_no_network_or_html_sinks(self):
        js = self.read('app.js')
        self.assertIn('textContent', js)
        for forbidden in ('innerHTML', 'outerHTML', 'insertAdjacentHTML', 'document.write', 'eval(', 'new Function'):
            self.assertNotIn(forbidden, js, f'app.js must not use {forbidden}')
        self.assertNotIn('http://', js)
        self.assertNotIn('https://', js)
        self.assertIn("fetch('./lesson.json'", js)
        self.assertIn('validateLesson', js)

    def test_listening_lookup_guards_malformed_units(self):
        js = self.read('app.js')
        self.assertIn('Array.isArray(data.units)', js)
        self.assertNotIn(
            'data.units.filter',
            js,
            'listening validation must not dereference units before checking it is an array',
        )

    def test_service_worker_precaches_lesson_and_shell(self):
        sw = self.read('sw.js')
        self.assertIn('caches.open', sw)
        self.assertIn('addAll', sw)
        self.assertIn('./lesson.json', sw)
        self.assertIn('./index.html', sw)
        self.assertIn("request.method !== 'GET'", sw)
        self.assertIn('self.location.origin', sw)
        self.assertNotIn('http://', sw)
        self.assertNotIn('https://', sw)

    def test_no_web_asset_references_network_urls(self):
        for name in REQUIRED_FILES:
            with self.subTest(name=name):
                content = self.read(name)
                self.assertNotIn('http://', content)
                self.assertNotIn('https://', content)

    def test_optional_node_browser_smoke(self):
        node = shutil.which('node')
        if node is None:
            self.skipTest('node is not installed; static checks remain authoritative')
        smoke = ROOT / 'tests' / 'browser-smoke.mjs'
        self.assertTrue(smoke.is_file(), 'tests/browser-smoke.mjs must exist')
        completed = subprocess.run(
            [node, str(smoke)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(0, completed.returncode, 'browser smoke failed:\n' + completed.stdout + completed.stderr)
        self.assertIn('checks passed', completed.stdout)


if __name__ == '__main__':
    unittest.main()
