# Language Matrix

A standalone Korean language tutor built with Python, designed to be local-first and completely offline. No cloud APIs, no paid services, no external dependencies required.

## Features

- **Bilingual Korean-English Lessons**: Learn Korean with English translations and explanations
- **Browser-Based GUI**: Interactive web interface for lesson delivery
- **Enhanced UI/UX**: Modern interface with gradients, progress tracking, and visual feedback
- **Progress Tracking**: Real-time monitoring of learning progress, accuracy, and streaks
- **Teaching Methodology**: Structured learning sessions with optimal strategies and study recommendations
- **Learning Analytics**: Comprehensive tracking of study time, lessons completed, and learning velocity
- **Interactive Exercises**: Multiple-choice questions with immediate feedback and validation
- **Linguistic Accuracy**: Built-in validation for Korean and English language accuracy
- **Flexible Lesson Management**: Create, save, load, and manage lessons locally
- **Offline-First Design**: Works completely offline without any internet connection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/topher2387/Language-matrix-
cd Language-matrix-
```

2. No installation required! The project uses only Python standard library.

3. Run the example:
```bash
python3 main.py
```

## Usage

### Basic Usage

1. Run the main script:
```bash
python3 main.py
```

This will:
- Create a sample bilingual lesson
- Validate the lesson for Korean and English accuracy
- Display lesson content in the browser GUI
- Save the lesson to a JSON file
- Generate an HTML file for browser viewing

### Enhanced Application (Phase 1)

Run the enhanced application with all new features:
```bash
python3 main_enhanced.py
```

This includes:
- Enhanced browser GUI with modern interface
- Progress tracking and dashboard
- Teaching methodology integration
- Learning analytics
- Interactive exercises

### Lesson Engine

```python
from language_matrix.lesson_engine import LessonEngine

# Create a lesson engine
engine = LessonEngine()

# Create a bilingual lesson
lesson = engine.create_bilingual_lesson("My First Lesson", 10)

# Validate the lesson
schema_result = engine.validate_lesson(lesson)
korean_result = engine.validate_korean_accuracy(lesson)
english_result = engine.validate_english_accuracy(lesson)

# Add exercises
exercise = Exercise(
    type="multiple_choice",
    question="What does '사과' mean?",
    options=["Apple", "Car", "Book"],
    correct_answer="Apple",
    explanation="사과 means apple in Korean.",
)
engine.add_exercise_to_lesson(lesson.id, exercise)

# Save and load lessons
engine.save_lesson(lesson, "lesson.json")
loaded_lesson = engine.load_lesson("lesson.json")
```

### Browser GUI

```python
from language_matrix.browser_gui import BrowserGUI

# Create and load a lesson
gui = BrowserGUI()
gui.load_lesson(lesson)

# Display content
content = gui.display_content()
print(f"English: {content['content']['english']}")
print(f"Hangul: {content['content']['hangul']}")

# Submit answers
result = gui.submit_answer(exercise_index, "Apple")
print(f"Correct: {result['is_correct']}")

# Get lesson summary
summary = gui.get_lesson_summary()
print(f"Lesson: {summary['lesson']['title']}")

# Generate HTML for browser
html = gui.get_html()
with open('lesson.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

## Lesson Structure

Lessons are organized into:

- **Content Items**: Bilingual Korean-English pairs with phonetic guides and linguistic explanations
- **Exercises**: Interactive questions to test understanding
- **Validation**: Built-in checks for language accuracy

## File Structure

```
Language-matrix-/
├── language_matrix/          # Main package
│   ├── __init__.py
│   ├── lesson_schema.py      # Lesson data structures
│   ├── lesson_validator.py   # Language accuracy validation
│   ├── lesson_engine.py      # Lesson management
│   └── browser_gui.py        # Browser interface
├── lessons/                  # Stored lessons
├── tests/                    # Unit tests
├── templates/                # HTML templates
├── main.py                   # Entry point
├── requirements.txt          # Dependencies (empty - uses stdlib)
└── README.md                 # This file
```

## Testing

Run the unit tests:
```bash
python3 -m unittest discover -s tests -v
```

Run the quick test:
```bash
python3 test_quick.py
```

### Enhanced Tests (Phase 1)

Run the comprehensive enhanced test suite:
```bash
python3 test_enhanced.py
```

This will test:
- Enhanced lesson generator
- Enhanced browser GUI
- Teaching methodology
- Learning analytics
- Progress tracking

## Development

### Creating Custom Lessons

1. Use the lesson engine to create or load lessons
2. Add content items with Korean, English, and explanations
3. Add exercises to test understanding
4. Validate the lesson for accuracy
5. Save to JSON file for later use

### Lesson Schema

Lessons follow a structured schema with:
- **id**: Unique identifier
- **title**: Lesson name
- **type**: Lesson type (BILINGUAL, FORMAL, etc.)
- **duration_minutes**: Estimated time
- **content**: List of content items
- **exercises**: List of exercises

## Phase 1 Enhancements

Phase 1 enhancements have been successfully implemented, adding:

### Enhanced Browser GUI
- Modern, responsive HTML interface with gradients
- Real-time progress tracking and visual feedback
- Interactive exercises with immediate feedback
- Content navigation (next/previous)
- Answer submission and validation
- Lesson summary and progress dashboard
- Progress saving and loading

### Teaching Methodology
- Learning session creation with teaching strategies
- Optimal strategy determination based on lesson type
- Learning style selection (visual, auditory, kinesthetic)
- Study recommendations and goals tracking
- Assessment creation and performance evaluation
- Review session generation
- Study reminders and schedule management

### Learning Analytics
- Comprehensive session tracking
- Lesson completion monitoring
- Exercise tracking and accuracy measurement
- Streak tracking and maintenance
- Learning velocity calculations
- Retention rate analysis
- Goals progress tracking
- Personalized recommendations generation
- Comprehensive report generation
- Chart data for visualization
- Study schedule recommendations

### Documentation
- `docs/ENHANCEMENT_PLAN.md` - Detailed enhancement roadmap
- `docs/PHASE1_ENHANCEMENTS.md` - Phase 1 feature documentation
- `QUICK_START.md` - Quick start guide for new users

For more details, see the Phase 1 enhancements documentation.

## License

This project is designed for educational purposes and is completely free to use.

## Credits

Built as part of the Language Matrix project to address Korean language learning needs.

## Contributing

Issues and contributions are welcome on GitHub.

## Repository execution and review workflow

The repository remains a staged work queue. This app prototype does not
complete or replace the remaining product packets.

1. Read the [implementation charter](docs/IMPLEMENTATION_PLAN.md) and the
   [execution packets](https://github.com/topher2387/Language-matrix-/issues).
2. The P00 contract and worker-harness inspection is tracked in
   [PR #10](https://github.com/topher2387/Language-matrix-/pull/10).
3. P01 lesson-engine and P02 browser-GUI work are the next usable-product
   milestones. P03 capability requests, P04 worker adapter, P05 asset library,
   then P06 voices, P07 illustrations, and P08 integrated demo follow their
   recorded dependencies.

Execution rules:

- Keep worker assignments bounded and record objective, dependencies, owned
  files, validation command, deliverable, and stop conditions.
- Use separate branches and pull requests for distinct packets. Do not merge
  automatically; require passing tests and review.
- Prefer free local/open models. Do not activate billing or bypass approval
  gates.
- Preserve English, Hangul, spoken phonetics, and phonological explanations in
  lessons. Cached lessons must work offline; v1 does not collect student
  telemetry or adapt curriculum from it.
- Close work only with a merged pull request, tests, and actual operation
  evidence. Report blocked work directly.
