# Language Matrix - Project Architecture

## Overview

Language Matrix is a modular Korean language tutor built with Python's standard library. The architecture is designed to be:

- **Simple**: Easy to understand and modify
- **Standalone**: No external dependencies
- **Testable**: Comprehensive unit tests
- **Extensible**: Easy to add new features

## Module Structure

### 1. language_matrix/__init__.py
- Main package initialization
- Exports core functionality
- Entry point for the package

### 2. language_matrix/lesson_schema.py
Defines the data structures for lessons:
- **LessonPlan**: Main lesson container
- **LessonSchema**: Schema validation
- **LessonType**: Lesson type enum
- **LessonContent**: Content item structure
- **Exercise**: Exercise structure
- **SpokenPhonetic**: Phonetic information
- **PhonologicalExplanation**: Linguistic explanations

### 3. language_matrix/lesson_validator.py
Validates language accuracy:
- **LessonValidator**: Main validation class
- **validate_lesson()**: Schema validation
- **validate_korean_accuracy()**: Korean language checks
- **validate_english_accuracy()**: English language checks
- Helper methods for specific validations

### 4. language_matrix/lesson_engine.py
Manages lesson lifecycle:
- **LessonEngine**: Main engine class
- **create_lesson()**: Create new lessons
- **add_exercise_to_lesson()**: Add exercises
- **validate_lesson()**: Validate lessons
- **save_lesson()**: Persist lessons to JSON
- **load_lesson()**: Load lessons from JSON
- **create_bilingual_lesson()**: Quick bilingual lesson creation
- **get_lesson()**: Retrieve lessons by ID
- **list_lessons()**: List all lessons

### 5. language_matrix/browser_gui.py
Browser-based user interface:
- **BrowserGUI**: Main GUI class
- **load_lesson()**: Load lesson into GUI
- **display_content()**: Show current content
- **submit_answer()**: Check exercise answers
- **get_html()**: Generate HTML for browser
- **get_lesson_summary()**: Get lesson overview
- Navigation methods (next/previous content)

## Data Flow

### Lesson Creation
```
User → LessonEngine → LessonSchema → LessonPlan
                                      |
                                      v
                          LessonValidator → Validation Results
                                      |
                                      v
                          save_lesson() → JSON File
```

### Lesson Usage
```
JSON File → load_lesson() → LessonPlan
                           |
                           v
                    BrowserGUI → HTML Output → Browser
```

## Validation Pipeline

1. **Schema Validation**
   - Checks required fields
   - Validates data types
   - Ensures structure compliance

2. **Korean Validation**
   - Grammar accuracy
   - Honorific usage
   - Particle marking
   - Verb endings

3. **English Validation**
   - Grammar accuracy
   - Clarity and completeness
   - Educational appropriateness

## Testing Strategy

Each module has comprehensive unit tests:

- **TestLessonSchema**: Schema validation tests
- **TestLessonValidator**: Language accuracy tests
- **TestLessonEngine**: Lesson management tests
- **TestBrowserGUI**: Browser interface tests
- **TestContracts**: Integration tests

## Extensibility Points

1. **New Lesson Types**: Add to LessonType enum
2. **New Validators**: Extend LessonValidator
3. **New Exercise Types**: Extend Exercise schema
4. **Custom GUI**: Extend BrowserGUI
5. **Storage Backends**: Modify save/load methods

## Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Type Safety**: Use Python type hints
3. **Error Handling**: Comprehensive error handling and user feedback
4. **Documentation**: Docstrings for all public methods
5. **Testing**: 100% test coverage for critical paths
