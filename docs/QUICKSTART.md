# Quick Start Guide

Get started with Language Matrix in 3 minutes!

## Prerequisites

- Python 3.8 or higher
- No external dependencies required!

## Installation

Simply clone and run:

```bash
git clone https://github.com/topher2387/Language-matrix-
cd Language-matrix-
python3 main.py
```

That's it! You're ready to learn Korean.

## What Happens When You Run main.py

1. **Creates a Lesson**: Generates a sample bilingual Korean lesson with 3 content items
2. **Validates Accuracy**: Checks both Korean and English for linguistic correctness
3. **Displays Content**: Shows the lesson in a browser interface
4. **Saves Files**: Creates `lessons/sample_lesson.json` and `lessons/sample_lesson.html`
5. **Generates HTML**: Creates a standalone HTML file you can open in any browser

## Viewing Your Lesson

1. Run `python3 main.py`
2. Open `lessons/sample_lesson.html` in your browser
3. Navigate through the content and exercises

## Creating Your Own Lessons

### Simple Lesson

```python
from language_matrix.lesson_engine import LessonEngine
from language_matrix.lesson_schema import LessonContent, SpokenPhonetic, PhonologicalExplanation

# Create engine
engine = LessonEngine()

# Create lesson
lesson = engine.create_bilingual_lesson("My First Lesson", 10)

# Add content
content = LessonContent(
    english="Hello",
    hangul="안녕하세요",
    spoken_phonetic=SpokenPhonetic(
        romanization="an-nyeong-ha-se-yo",
        pronunciation="ahn-nyong-hah-seh-yoh"
    ),
    phonological_explanation=PhonologicalExplanation(
        explanation="Hello is used in formal situations. An-nyeong is a casual greeting.",
        changes=[],
        rules_applied=["formal greeting"]
    )
)
# Add more content...

# Save lesson
engine.save_lesson(lesson, "my_lesson.json")
```

### Lesson with Exercises

```python
from language_matrix.lesson_engine import LessonEngine
from language_matrix.lesson_schema import Exercise

# Create engine
engine = LessonEngine()

# Create lesson
lesson = engine.create_bilingual_lesson("Test Lesson", 10)

# Add exercise
exercise = Exercise(
    type="multiple_choice",
    question="What does '안녕하세요' mean?",
    options=["Hello", "Goodbye", "Thank you"],
    correct_answer="Hello",
    explanation="'안녕하세요' means Hello in Korean."
)
engine.add_exercise_to_lesson(lesson.id, exercise)

# Save lesson
engine.save_lesson(lesson, "test_lesson.json")
```

## Running Tests

```bash
# All tests
python3 -m unittest discover -s tests -v

# Quick test
python3 test_quick.py
```

## Common Tasks

### Load an Existing Lesson

```python
from language_matrix.lesson_engine import LessonEngine

engine = LessonEngine()
lesson = engine.load_lesson("my_lesson.json")

print(f"Lesson: {lesson.title}")
print(f"Content items: {len(lesson.content)}")
print(f"Exercises: {len(lesson.exercises)}")
```

### Validate a Lesson

```python
from language_matrix.lesson_engine import LessonEngine

engine = LessonEngine()
lesson = engine.load_lesson("my_lesson.json")

# Schema validation
schema_result = engine.validate_lesson(lesson)
print(f"Schema valid: {schema_result['valid']}")

# Korean accuracy
korean_result = engine.validate_korean_accuracy(lesson)
print(f"Korean valid: {korean_result['valid']}")

# English accuracy
english_result = engine.validate_english_accuracy(lesson)
print(f"English valid: {english_result['valid']}")
```

### Use the Browser GUI

```python
from language_matrix.lesson_engine import LessonEngine
from language_matrix.browser_gui import BrowserGUI

# Load lesson
engine = LessonEngine()
lesson = engine.load_lesson("my_lesson.json")

# Create GUI
gui = BrowserGUI()
gui.load_lesson(lesson)

# Display content
content = gui.display_content()
print(f"English: {content['content']['english']}")
print(f"Hangul: {content['content']['hangul']}")

# Submit answer
result = gui.submit_answer(0, "Hello")
print(f"Correct: {result['is_correct']}")

# Generate HTML
html = gui.get_html()
with open('lesson.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

## Tips

1. **Start Simple**: Begin with basic lessons and add complexity gradually
2. **Validate Often**: Use validation to ensure language accuracy
3. **Save Progress**: Regularly save your lessons to JSON files
4. **Test Locally**: Run tests to verify your lessons work correctly
5. **Use HTML**: The generated HTML files work offline and can be shared

## Next Steps

- Read the full [README.md](README.md) for more details
- Check [ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical information
- Explore the [test files](tests/) for examples
- Customize lessons to fit your learning goals

## Need Help?

- Check the existing tests for examples
- Review the module docstrings
- Open an issue on GitHub
