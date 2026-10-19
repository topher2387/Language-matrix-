import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const LM = require('../web/app.js');
const here = dirname(fileURLToPath(import.meta.url));
const lessonPath = join(here, '..', 'web', 'lesson.json');
const hostiles = '<img src=x onerror="alert(1)"><script>alert(2)</script>';

class FakeNode {
  constructor(tagName) {
    this.tagName = String(tagName).toLowerCase();
    this.children = [];
    this.attributes = {};
    this._text = null;
    this._listeners = {};
    this.disabled = false;
  }
  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }
  get textContent() {
    if (this._text !== null) { return this._text; }
    return this.children.map((child) => child.textContent).join('');
  }
  setAttribute(name, value) {
    this.attributes[String(name)] = String(value);
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
  }
  appendChild(child) {
    if (this._text !== null) { this._text = null; }
    this.children.push(child);
    return child;
  }
  addEventListener(type, handler) {
    (this._listeners[type] = this._listeners[type] || []).push(handler);
  }
  click() {
    (this._listeners.click || []).forEach((handler) => handler({ type: 'click' }));
  }
}

const fakeDocument = {
  createElement(tagName) { return new FakeNode(tagName); },
  addEventListener() {}
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function collect(node, out = []) {
  out.push(node);
  node.children.forEach((child) => collect(child, out));
  return out;
}

function findByClass(node, className) {
  return collect(node).filter((item) => {
    const attr = item.getAttribute('class');
    return attr !== null && attr.split(/\s+/).indexOf(className) !== -1;
  });
}

const lesson = JSON.parse(readFileSync(lessonPath, 'utf8'));
let checks = 0;

function ok(condition, message) {
  assert.ok(condition, message);
  checks += 1;
}

ok(LM.validateLesson(lesson).ok, 'bundled lesson must validate');

const surfacesLesson = clone(lesson);
surfacesLesson.widgets = [{ type: 'teaching_unit', ref_id: 'u1' }];
const surfaceRoot = new FakeNode('div');
const surfaceResult = LM.renderLesson(surfacesLesson, fakeDocument, surfaceRoot);
ok(surfaceResult.ok && surfaceResult.widgets === 1, 'teaching unit renders without a separate comparison widget');
for (const surface of ['english', 'literal', 'hangul', 'phonetics', 'phonology']) {
  const block = collect(surfaceRoot).find((node) => node.getAttribute('data-surface') === surface);
  ok(block && block.textContent.trim().length > 0, 'teaching unit shows surface: ' + surface);
}

const unknownWidget = clone(lesson);
unknownWidget.widgets = [{ type: 'html', ref_id: 'u1' }];
const unknownResult = LM.validateLesson(unknownWidget);
ok(!unknownResult.ok && unknownResult.errors.some((e) => e.includes('unknown widget type')), 'unknown widget type rejected');

const extraProperty = clone(lesson);
extraProperty.widgets = [{ type: 'teaching_unit', ref_id: 'u1', html: hostiles }];
const extraResult = LM.validateLesson(extraProperty);
ok(!extraResult.ok && extraResult.errors.some((e) => e.includes('unknown key')), 'widget extra property rejected');

const dangling = clone(lesson);
dangling.widgets = [{ type: 'comparison', ref_id: 'missing_unit' }];
const danglingResult = LM.validateLesson(dangling);
ok(!danglingResult.ok && danglingResult.errors.some((e) => e.includes('dangles')), 'dangling widget reference rejected');

const danglingExercise = clone(lesson);
danglingExercise.exercises[0].unit_id = 'ghost';
ok(LM.validateLesson(danglingExercise).errors.some((e) => e.includes('dangles')), 'dangling exercise unit reference rejected');

ok(!LM.validateLesson(null).ok, 'null lesson rejected');
ok(LM.validateLesson([]).errors.some((e) => e.includes('object')), 'array lesson rejected');

const badAnswer = clone(lesson);
badAnswer.exercises[0].correct_option = 5;
ok(LM.validateLesson(badAnswer).errors.some((e) => e.includes('correct_option')), 'out-of-range answer rejected');

const duplicate = clone(lesson);
duplicate.units.push(clone(duplicate.units[0]));
ok(LM.validateLesson(duplicate).errors.some((e) => e.includes('duplicated')), 'duplicate unit id rejected');

const listening = clone(lesson);
listening.exercises[0].kind = 'listening_choice';
ok(LM.validateLesson(listening).errors.some((e) => e.includes('listening exercise')), 'listening exercise without audio reference rejected');

const nullUnits = clone(lesson);
nullUnits.units = null;
nullUnits.exercises[0].kind = 'listening_choice';
let nullUnitsResult = null;
try {
  nullUnitsResult = LM.validateLesson(nullUnits);
} catch (error) {
  assert.fail('units:null with a listening exercise must not throw: ' + error.message);
}
ok(!nullUnitsResult.ok && nullUnitsResult.errors.some((e) => e.includes('units must be an array')), 'units:null with a listening exercise is rejected without throwing');

const nullUnitEntry = clone(lesson);
nullUnitEntry.units = [null];
nullUnitEntry.exercises[0].kind = 'listening_choice';
let nullUnitEntryResult = null;
try {
  nullUnitEntryResult = LM.validateLesson(nullUnitEntry);
} catch (error) {
  assert.fail('units:[null] with a listening exercise must not throw: ' + error.message);
}
ok(!nullUnitEntryResult.ok && nullUnitEntryResult.errors.some((e) => e.includes('must be an object')), 'units:[null] with a listening exercise is rejected without throwing');

const nullUnitEntryRoot = new FakeNode('div');
const nullUnitEntryRender = LM.renderLesson(nullUnitEntry, fakeDocument, nullUnitEntryRoot);
ok(!nullUnitEntryRender.ok && nullUnitEntryRender.widgets === 0 && nullUnitEntryRoot.textContent.includes('Lesson rejected'), 'malformed units with a listening exercise render a rejection panel');

const verifiedClaim = clone(lesson);
verifiedClaim.verification = { status: 'verified', reviewer: '   ', notes: 'x' };
ok(LM.validateLesson(verifiedClaim).errors.some((e) => e.includes('reviewer')), 'blank reviewer cannot claim reviewed/verified');

const hostileLesson = clone(lesson);
hostileLesson.title = hostiles;
hostileLesson.units[0].english = hostiles;
hostileLesson.exercises[0].options[0] = hostiles;
const hostileRoot = new FakeNode('div');
ok(LM.renderLesson(hostileLesson, fakeDocument, hostileRoot).ok, 'hostile text is still a valid untrusted string');
ok(hostileRoot.textContent.includes('<script>alert(2)</script>'), 'hostile text is rendered verbatim');
ok(collect(hostileRoot).every((node) => node.tagName !== 'script' && node.tagName !== 'img'), 'hostile text never becomes an element');

const renderRoot = new FakeNode('div');
const renderResult = LM.renderLesson(lesson, fakeDocument, renderRoot);
ok(renderResult.ok && renderResult.widgets === 4, 'all four widgets render');
ok(findByClass(renderRoot, 'lm-comparison').length === 1, 'comparison widget present');
ok(findByClass(renderRoot, 'lm-notes').length === 1, 'comparison notes present');

const optionButtons = collect(renderRoot).filter((node) => node.tagName === 'button' && node.getAttribute('class') === 'lm-option');
ok(optionButtons.length === 2, 'exercise renders each option as a button');
const feedback = findByClass(renderRoot, 'lm-feedback')[0];
optionButtons[0].click();
ok(feedback.textContent.startsWith('Correct') && feedback.getAttribute('data-correct') === 'true', 'correct choice gives local correct feedback');
optionButtons[1].click();
ok(feedback.textContent.startsWith('Not quite') && feedback.getAttribute('data-correct') === 'false', 'wrong choice gives local corrective feedback');

const audio = findByClass(renderRoot, 'lm-audio')[0];
ok(audio.getAttribute('data-audio-state') === 'unavailable', 'audio state is honestly unavailable');
ok(findByClass(renderRoot, 'lm-play')[0].disabled === true, 'play control is disabled while audio is unavailable');
ok(findByClass(renderRoot, 'lm-voice')[0].disabled === true, 'voice control reflects unavailable audio');
ok(findByClass(renderRoot, 'lm-speed').length === 1 && findByClass(renderRoot, 'lm-repeat').length === 1, 'speed and repeat controls are present');

const rejectedRoot = new FakeNode('div');
const rejectedResult = LM.renderLesson(unknownWidget, fakeDocument, rejectedRoot);
ok(!rejectedResult.ok && rejectedResult.widgets === 0 && rejectedRoot.textContent.includes('Lesson rejected'), 'invalid lesson shows rejection and renders no widgets');

const check = LM.checkAnswer({ options: ['a', 'b'], correct_option: 0 }, 9);
ok(check.feedback.includes('Choose one of the available answers'), 'out-of-range answer is handled locally');

console.log('browser-smoke: ' + checks + ' checks passed (offline, no packages downloaded)');
