'use strict';
(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.LM = api;
  }
  if (root && typeof root.document !== 'undefined' && root.document && typeof root.document.addEventListener === 'function') {
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', function () { api.start(root); });
    } else {
      api.start(root);
    }
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var LESSON_SCHEMA_VERSION = '1.0';
  var WIDGET_TYPES = ['teaching_unit', 'comparison', 'exercise', 'audio'];
  var EXERCISE_KINDS = ['reading_choice', 'listening_choice'];
  var VERIFICATION_STATUSES = ['unverified', 'reviewed', 'verified'];
  var ID_PATTERN = /^[a-z][a-z0-9_-]{0,63}$/;
  var MAX_TEXT = 2000;

  var LESSON_KEYS = ['schema_version', 'lesson_id', 'title', 'source_language', 'target_language', 'verification', 'units', 'exercises', 'widgets'];
  var UNIT_KEYS = ['unit_id', 'english', 'hangul', 'spoken_phonetics', 'phonology', 'structure', 'register', 'translation_note', 'dialect_note', 'audio_assets', 'literal_english'];
  var AUDIO_KEYS = ['asset_id', 'voice_id', 'verification'];
  var EXERCISE_KEYS = ['exercise_id', 'kind', 'prompt', 'unit_id', 'options', 'correct_option'];
  var WIDGET_KEYS = ['type', 'ref_id'];
  var VERIFICATION_KEYS = ['status', 'reviewer', 'notes'];

  function isObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  function isString(value, min, max) {
    if (typeof value !== 'string') { return false; }
    if (value.length < min) { return false; }
    if (typeof max === 'number' && value.length > max) { return false; }
    return true;
  }

  function isNonBlank(value) {
    return typeof value === 'string' && /\S/.test(value);
  }

  function isId(value) {
    return typeof value === 'string' && ID_PATTERN.test(value);
  }

  function extraKeys(object, allowed) {
    return Object.keys(object).filter(function (key) { return allowed.indexOf(key) === -1; });
  }

  function validateVerification(value, label, errors) {
    if (!isObject(value)) {
      errors.push(label + ' must be an object');
      return;
    }
    extraKeys(value, VERIFICATION_KEYS).forEach(function (key) {
      errors.push(label + ' has unknown key: ' + key);
    });
    VERIFICATION_KEYS.forEach(function (key) {
      if (!(key in value)) { errors.push(label + ' is missing key: ' + key); }
    });
    if (VERIFICATION_STATUSES.indexOf(value.status) === -1) {
      errors.push(label + '.status must be one of ' + VERIFICATION_STATUSES.join(', '));
    }
    if (!(value.reviewer === null || isString(value.reviewer, 0, 200))) {
      errors.push(label + '.reviewer must be null or a string of at most 200 characters');
    }
    if (!isString(value.notes, 1, MAX_TEXT)) {
      errors.push(label + '.notes must be a non-empty string of at most ' + MAX_TEXT + ' characters');
    }
    if ((value.status === 'reviewed' || value.status === 'verified') && !isNonBlank(value.reviewer)) {
      errors.push(label + ' cannot be ' + value.status + ' without a non-whitespace reviewer name');
    }
  }

  function validateLesson(data) {
    var errors = [];
    if (!isObject(data)) {
      return { ok: false, errors: ['lesson must be a JSON object'] };
    }
    extraKeys(data, LESSON_KEYS).forEach(function (key) {
      errors.push('lesson has unknown key: ' + key);
    });
    LESSON_KEYS.forEach(function (key) {
      if (!(key in data)) { errors.push('lesson is missing key: ' + key); }
    });
    if (data.schema_version !== LESSON_SCHEMA_VERSION) {
      errors.push('lesson.schema_version must be "' + LESSON_SCHEMA_VERSION + '"');
    }
    if (!isId(data.lesson_id)) {
      errors.push('lesson.lesson_id must match ' + ID_PATTERN);
    }
    if (!isString(data.title, 1, 200)) {
      errors.push('lesson.title must be a non-empty string of at most 200 characters');
    }
    if (data.source_language !== 'en') { errors.push('lesson.source_language must be "en"'); }
    if (data.target_language !== 'ko') { errors.push('lesson.target_language must be "ko"'); }
    validateVerification(data.verification, 'lesson.verification', errors);

    var unitIds = [];
    if (!Array.isArray(data.units)) {
      errors.push('lesson.units must be an array');
    } else {
      if (data.units.length < 1 || data.units.length > 50) {
        errors.push('lesson.units must contain between 1 and 50 items');
      }
      data.units.forEach(function (unit, index) {
        var label = 'units[' + index + ']';
        if (!isObject(unit)) { errors.push(label + ' must be an object'); return; }
        extraKeys(unit, UNIT_KEYS).forEach(function (key) { errors.push(label + ' has unknown key: ' + key); });
        UNIT_KEYS.forEach(function (key) {
          if (!(key in unit)) { errors.push(label + ' is missing key: ' + key); }
        });
        if (!isId(unit.unit_id)) { errors.push(label + '.unit_id must match ' + ID_PATTERN); }
        ['english', 'hangul', 'spoken_phonetics', 'phonology', 'structure', 'register', 'translation_note', 'dialect_note', 'literal_english'].forEach(function (field) {
          if (!isString(unit[field], 1, MAX_TEXT)) {
            errors.push(label + '.' + field + ' must be a non-empty string of at most ' + MAX_TEXT + ' characters');
          }
        });
        if (isId(unit.unit_id)) {
          if (unitIds.indexOf(unit.unit_id) !== -1) {
            errors.push(label + '.unit_id is duplicated: ' + unit.unit_id);
          } else {
            unitIds.push(unit.unit_id);
          }
        }
        if (!Array.isArray(unit.audio_assets)) {
          errors.push(label + '.audio_assets must be an array');
        } else {
          if (unit.audio_assets.length > 10) { errors.push(label + '.audio_assets may contain at most 10 items'); }
          unit.audio_assets.forEach(function (asset, assetIndex) {
            var assetLabel = label + '.audio_assets[' + assetIndex + ']';
            if (!isObject(asset)) { errors.push(assetLabel + ' must be an object'); return; }
            extraKeys(asset, AUDIO_KEYS).forEach(function (key) { errors.push(assetLabel + ' has unknown key: ' + key); });
            AUDIO_KEYS.forEach(function (key) {
              if (!(key in asset)) { errors.push(assetLabel + ' is missing key: ' + key); }
            });
            if (!isId(asset.asset_id)) { errors.push(assetLabel + '.asset_id must match ' + ID_PATTERN); }
            if (!isId(asset.voice_id)) { errors.push(assetLabel + '.voice_id must match ' + ID_PATTERN); }
            validateVerification(asset.verification, assetLabel + '.verification', errors);
          });
        }
      });
    }

    var exerciseIds = [];
    if (!Array.isArray(data.exercises)) {
      errors.push('lesson.exercises must be an array');
    } else {
      if (data.exercises.length < 1 || data.exercises.length > 50) {
        errors.push('lesson.exercises must contain between 1 and 50 items');
      }
      data.exercises.forEach(function (exercise, index) {
        var label = 'exercises[' + index + ']';
        if (!isObject(exercise)) { errors.push(label + ' must be an object'); return; }
        extraKeys(exercise, EXERCISE_KEYS).forEach(function (key) { errors.push(label + ' has unknown key: ' + key); });
        EXERCISE_KEYS.forEach(function (key) {
          if (!(key in exercise)) { errors.push(label + ' is missing key: ' + key); }
        });
        if (!isId(exercise.exercise_id)) { errors.push(label + '.exercise_id must match ' + ID_PATTERN); }
        if (EXERCISE_KINDS.indexOf(exercise.kind) === -1) {
          errors.push(label + '.kind must be one of ' + EXERCISE_KINDS.join(', '));
        }
        if (!isString(exercise.prompt, 1, MAX_TEXT)) {
          errors.push(label + '.prompt must be a non-empty string of at most ' + MAX_TEXT + ' characters');
        }
        if (!isId(exercise.unit_id)) { errors.push(label + '.unit_id must match ' + ID_PATTERN); }
        if (unitIds.indexOf(exercise.unit_id) === -1) {
          errors.push(label + '.unit_id dangles: no unit with unit_id ' + exercise.unit_id);
        }
        if (isId(exercise.exercise_id)) {
          if (exerciseIds.indexOf(exercise.exercise_id) !== -1) {
            errors.push(label + '.exercise_id is duplicated: ' + exercise.exercise_id);
          } else {
            exerciseIds.push(exercise.exercise_id);
          }
        }
        if (!Array.isArray(exercise.options)) {
          errors.push(label + '.options must be an array');
        } else {
          if (exercise.options.length < 2 || exercise.options.length > 6) {
            errors.push(label + '.options must contain between 2 and 6 items');
          }
          exercise.options.forEach(function (option, optionIndex) {
            if (!isString(option, 1, 500)) {
              errors.push(label + '.options[' + optionIndex + '] must be a non-empty string of at most 500 characters');
            }
          });
          if (!Number.isInteger(exercise.correct_option) || exercise.correct_option < 0) {
            errors.push(label + '.correct_option must be a non-negative integer');
          } else if (exercise.correct_option >= exercise.options.length) {
            errors.push(label + '.correct_option is outside the options range');
          }
        }
        if (exercise.kind === 'listening_choice') {
          var owner = null;
          if (Array.isArray(data.units)) {
            data.units.forEach(function (unit) {
              if (isObject(unit) && unit.unit_id === exercise.unit_id) { owner = unit; }
            });
          }
          if (!owner || !Array.isArray(owner.audio_assets) || owner.audio_assets.length === 0) {
            errors.push(label + ' is a listening exercise but its unit provides no available audio reference');
          }
        }
      });
    }

    if (!Array.isArray(data.widgets)) {
      errors.push('lesson.widgets must be an array');
    } else {
      if (data.widgets.length < 1 || data.widgets.length > 200) {
        errors.push('lesson.widgets must contain between 1 and 200 items');
      }
      data.widgets.forEach(function (widget, index) {
        var label = 'widgets[' + index + ']';
        if (!isObject(widget)) { errors.push(label + ' must be an object'); return; }
        extraKeys(widget, WIDGET_KEYS).forEach(function (key) { errors.push(label + ' has unknown key: ' + key); });
        WIDGET_KEYS.forEach(function (key) {
          if (!(key in widget)) { errors.push(label + ' is missing key: ' + key); }
        });
        if (WIDGET_TYPES.indexOf(widget.type) === -1) {
          errors.push(label + ' has unknown widget type: ' + widget.type);
          return;
        }
        if (!isId(widget.ref_id)) { errors.push(label + '.ref_id must match ' + ID_PATTERN); return; }
        if (widget.type === 'exercise') {
          if (exerciseIds.indexOf(widget.ref_id) === -1) {
            errors.push(label + ' dangles: no exercise with exercise_id ' + widget.ref_id);
          }
        } else if (unitIds.indexOf(widget.ref_id) === -1) {
          errors.push(label + ' dangles: no unit with unit_id ' + widget.ref_id);
        }
      });
    }

    return { ok: errors.length === 0, errors: errors };
  }

  function findUnit(lesson, unitId) {
    for (var i = 0; i < lesson.units.length; i += 1) {
      if (lesson.units[i].unit_id === unitId) { return lesson.units[i]; }
    }
    return null;
  }

  function findExercise(lesson, exerciseId) {
    for (var i = 0; i < lesson.exercises.length; i += 1) {
      if (lesson.exercises[i].exercise_id === exerciseId) { return lesson.exercises[i]; }
    }
    return null;
  }

  function verificationLabel(verification) {
    if (!isObject(verification)) { return 'Verification: unknown'; }
    if (verification.status === 'verified') {
      return 'Verification: verified (claimed by reviewer ' + verification.reviewer + '; independent review not authenticated here)';
    }
    if (verification.status === 'reviewed') {
      return 'Verification: reviewed (claimed by ' + verification.reviewer + '; not independently verified)';
    }
    return 'Verification: unverified content';
  }

  function buildWidgetView(lesson, widget) {
    if (!isObject(widget) || WIDGET_TYPES.indexOf(widget.type) === -1) {
      return { error: 'unknown widget type' };
    }
    if (widget.type === 'exercise') {
      var exercise = findExercise(lesson, widget.ref_id);
      if (!exercise) { return { error: 'dangling exercise reference: ' + widget.ref_id }; }
      return {
        kind: 'exercise',
        exercise_id: exercise.exercise_id,
        unit_id: exercise.unit_id,
        prompt: exercise.prompt,
        options: exercise.options.slice(),
        correct_option: exercise.correct_option
      };
    }
    var unit = findUnit(lesson, widget.ref_id);
    if (!unit) { return { error: 'dangling unit reference: ' + widget.ref_id }; }
    if (widget.type === 'teaching_unit') {
      return {
        kind: 'teaching_unit',
        unit_id: unit.unit_id,
        surfaces: {
          english: unit.english,
          literal: unit.literal_english,
          hangul: unit.hangul,
          phonetics: unit.spoken_phonetics,
          phonology: unit.phonology
        },
        verification: lesson.verification
      };
    }
    if (widget.type === 'comparison') {
      return {
        kind: 'comparison',
        unit_id: unit.unit_id,
        structure: unit.structure,
        register: unit.register,
        translation_note: unit.translation_note,
        dialect_note: unit.dialect_note
      };
    }
    return {
      kind: 'audio',
      unit_id: unit.unit_id,
      assets: unit.audio_assets.map(function (asset) {
        return {
          asset_id: asset.asset_id,
          voice_id: asset.voice_id,
          status: asset.verification.status,
          reviewer: asset.verification.reviewer
        };
      }),
      available: false,
      reason: 'Audio unavailable: no trusted local asset store (P05) is connected, so referenced assets cannot be verified or played.'
    };
  }

  function checkAnswer(exercise, choiceIndex) {
    if (!isObject(exercise) || !Array.isArray(exercise.options) || !Number.isInteger(exercise.correct_option)) {
      return { correct: false, feedback: 'This exercise is malformed and cannot be checked.' };
    }
    if (!Number.isInteger(choiceIndex) || choiceIndex < 0 || choiceIndex >= exercise.options.length) {
      return { correct: false, feedback: 'Choose one of the available answers.' };
    }
    if (choiceIndex === exercise.correct_option) {
      return { correct: true, feedback: 'Correct. Well done.' };
    }
    return { correct: false, feedback: 'Not quite. The correct answer is: ' + exercise.options[exercise.correct_option] };
  }

  function el(doc, tag, className, text) {
    var node = doc.createElement(tag);
    if (className) { node.setAttribute('class', className); }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function labeledSelect(doc, label, className, options, disabled, selected) {
    var wrap = el(doc, 'span', 'lm-control');
    wrap.appendChild(el(doc, 'span', 'lm-control-label', label));
    var select = el(doc, 'select', className);
    if (disabled) { select.disabled = true; select.setAttribute('disabled', 'disabled'); }
    options.forEach(function (pair) {
      var option = el(doc, 'option', null, pair[1]);
      option.setAttribute('value', pair[0]);
      if (selected === pair[0]) { option.setAttribute('selected', 'selected'); }
      select.appendChild(option);
    });
    wrap.appendChild(select);
    return wrap;
  }

  function renderTeachingUnit(view, doc) {
    var section = el(doc, 'section', 'lm-widget lm-teaching-unit');
    section.setAttribute('data-widget', 'teaching_unit');
    section.appendChild(el(doc, 'h2', null, 'Teaching unit'));
    var surfaces = [
      ['english', 'English meaning', view.surfaces.english],
      ['literal', 'Literal English gloss', view.surfaces.literal],
      ['hangul', 'Hangul', view.surfaces.hangul],
      ['phonetics', 'Spoken phonetics (learner aid)', view.surfaces.phonetics],
      ['phonology', 'Phonology explanation', view.surfaces.phonology]
    ];
    var grid = el(doc, 'div', 'lm-surfaces');
    surfaces.forEach(function (row) {
      var block = el(doc, 'div', 'lm-surface');
      block.setAttribute('data-surface', row[0]);
      block.appendChild(el(doc, 'h3', null, row[1]));
      block.appendChild(el(doc, 'p', null, row[2]));
      grid.appendChild(block);
    });
    section.appendChild(grid);
    section.appendChild(el(doc, 'p', 'lm-verification', verificationLabel(view.verification)));
    return section;
  }

  function renderComparison(view, doc) {
    var section = el(doc, 'section', 'lm-widget lm-comparison');
    section.setAttribute('data-widget', 'comparison');
    section.appendChild(el(doc, 'h2', null, 'Comparison notes'));
    var notes = [
      ['structure', 'Structure and particles', view.structure],
      ['register', 'Register', view.register],
      ['translation', 'Translation note', view.translation_note],
      ['dialect', 'Dialect note', view.dialect_note]
    ];
    var list = el(doc, 'dl', 'lm-notes');
    notes.forEach(function (row) {
      var dt = el(doc, 'dt', null, row[1]);
      dt.setAttribute('data-note', row[0]);
      var dd = el(doc, 'dd', null, row[2]);
      list.appendChild(dt);
      list.appendChild(dd);
    });
    section.appendChild(list);
    return section;
  }

  function renderExercise(view, doc) {
    var section = el(doc, 'section', 'lm-widget lm-exercise');
    section.setAttribute('data-widget', 'exercise');
    section.appendChild(el(doc, 'h2', null, 'Exercise'));
    section.appendChild(el(doc, 'p', 'lm-prompt', view.prompt));
    var feedback = el(doc, 'p', 'lm-feedback', 'Choose an answer.');
    feedback.setAttribute('role', 'status');
    feedback.setAttribute('aria-live', 'polite');
    feedback.setAttribute('data-correct', '');
    var list = el(doc, 'ul', 'lm-options');
    view.options.forEach(function (option, index) {
      var item = el(doc, 'li', null, null);
      var button = el(doc, 'button', 'lm-option', option);
      button.setAttribute('type', 'button');
      button.addEventListener('click', function () {
        var result = checkAnswer(view, index);
        feedback.textContent = result.feedback;
        feedback.setAttribute('data-correct', result.correct ? 'true' : 'false');
      });
      item.appendChild(button);
      list.appendChild(item);
    });
    section.appendChild(list);
    section.appendChild(feedback);
    return section;
  }

  function renderAudio(view, doc) {
    var section = el(doc, 'section', 'lm-widget lm-audio');
    section.setAttribute('data-widget', 'audio');
    section.setAttribute('data-audio-state', 'unavailable');
    section.appendChild(el(doc, 'h2', null, 'Audio'));
    section.appendChild(el(doc, 'p', 'lm-audio-status', view.reason));
    if (view.assets.length) {
      var list = el(doc, 'ul', 'lm-audio-assets');
      view.assets.forEach(function (asset) {
        list.appendChild(el(doc, 'li', null, 'Referenced asset ' + asset.asset_id + ' from voice ' + asset.voice_id + ' (' + asset.status + ', not verified for playback)'));
      });
      section.appendChild(list);
    } else {
      section.appendChild(el(doc, 'p', null, 'This unit references no audio assets.'));
    }
    var voiceOptions = view.assets.length
      ? view.assets.map(function (asset) { return [asset.voice_id, 'Voice ' + asset.voice_id + ' (unavailable)']; })
      : [['', 'No verified voice available']];
    var controls = el(doc, 'div', 'lm-audio-controls');
    controls.appendChild(labeledSelect(doc, 'Voice', 'lm-voice', voiceOptions, true));
    controls.appendChild(labeledSelect(doc, 'Speed', 'lm-speed', [['0.5', '0.5x'], ['0.75', '0.75x'], ['1', '1x'], ['1.25', '1.25x'], ['1.5', '1.5x']], true, '1'));
    controls.appendChild(labeledSelect(doc, 'Repeat', 'lm-repeat', [['1', 'Once'], ['2', 'Twice'], ['3', 'Three times']], true, '1'));
    var play = el(doc, 'button', 'lm-play', 'Play (unavailable)');
    play.setAttribute('type', 'button');
    play.disabled = true;
    controls.appendChild(play);
    section.appendChild(controls);
    return section;
  }

  function renderWidgetView(view, doc) {
    if (view.kind === 'teaching_unit') { return renderTeachingUnit(view, doc); }
    if (view.kind === 'comparison') { return renderComparison(view, doc); }
    if (view.kind === 'exercise') { return renderExercise(view, doc); }
    if (view.kind === 'audio') { return renderAudio(view, doc); }
    var section = el(doc, 'section', 'lm-widget lm-error');
    section.appendChild(el(doc, 'p', null, 'Unsupported widget view.'));
    return section;
  }

  function renderLesson(lesson, doc, root) {
    var result = validateLesson(lesson);
    root.textContent = '';
    if (!result.ok) {
      var errorBox = el(doc, 'section', 'lm-error');
      errorBox.setAttribute('role', 'alert');
      errorBox.appendChild(el(doc, 'h2', null, 'Lesson rejected'));
      errorBox.appendChild(el(doc, 'p', null, 'This lesson did not pass validation, so nothing was rendered.'));
      var list = el(doc, 'ul', null, null);
      result.errors.slice(0, 20).forEach(function (message) {
        list.appendChild(el(doc, 'li', null, message));
      });
      errorBox.appendChild(list);
      root.appendChild(errorBox);
      return { ok: false, errors: result.errors, widgets: 0 };
    }
    var header = el(doc, 'section', 'lm-lesson-header');
    header.appendChild(el(doc, 'h1', null, lesson.title));
    header.appendChild(el(doc, 'p', 'lm-verification', verificationLabel(lesson.verification)));
    root.appendChild(header);
    var rendered = 0;
    lesson.widgets.forEach(function (widget, index) {
      var view = buildWidgetView(lesson, widget);
      if (view.error) {
        var rejected = el(doc, 'section', 'lm-error');
        rejected.setAttribute('role', 'alert');
        rejected.appendChild(el(doc, 'p', null, 'Widget ' + index + ' rejected: ' + view.error));
        root.appendChild(rejected);
        return;
      }
      root.appendChild(renderWidgetView(view, doc));
      rendered += 1;
    });
    return { ok: true, errors: [], widgets: rendered };
  }

  function start(root) {
    var doc = root.document;
    var target = doc.getElementById('lesson');
    if (!target) { return; }
    function showError(message) {
      target.textContent = '';
      var box = el(doc, 'section', 'lm-error');
      box.setAttribute('role', 'alert');
      box.appendChild(el(doc, 'h2', null, 'Unable to load lesson'));
      box.appendChild(el(doc, 'p', null, message));
      target.appendChild(box);
    }
    if (root.navigator && 'serviceWorker' in root.navigator) {
      try {
        root.navigator.serviceWorker.register('./sw.js').catch(function () {});
      } catch (error) {
        void error;
      }
    }
    if (typeof root.fetch !== 'function') {
      showError('This browser cannot fetch the local lesson file.');
      return;
    }
    root.fetch('./lesson.json', { cache: 'no-cache' }).then(function (response) {
      if (!response.ok) { throw new Error('HTTP ' + response.status); }
      return response.json();
    }).then(function (lesson) {
      renderLesson(lesson, doc, target);
    }).catch(function (error) {
      var detail = error && error.message ? error.message : 'unknown error';
      showError('Could not load ./lesson.json (' + detail + '). Serve the web folder over HTTP so the lesson can be fetched and cached.');
    });
  }

  return {
    LESSON_SCHEMA_VERSION: LESSON_SCHEMA_VERSION,
    WIDGET_TYPES: WIDGET_TYPES,
    EXERCISE_KINDS: EXERCISE_KINDS,
    validateLesson: validateLesson,
    buildWidgetView: buildWidgetView,
    checkAnswer: checkAnswer,
    verificationLabel: verificationLabel,
    renderLesson: renderLesson,
    renderWidgetView: renderWidgetView,
    start: start
  };
});
