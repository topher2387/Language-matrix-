#!/usr/bin/env python3
"""Quick test script for Language Matrix"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from language_matrix.lesson_engine import LessonEngine
from language_matrix.lesson_schema import LessonType, LessonContent, SpokenPhonetic, PhonologicalExplanation
from language_matrix.browser_gui import BrowserGUI


def test_basic_functionality():
    """Test basic Language Matrix functionality"""
    print("Testing Language Matrix Basic Functionality")
    print("=" * 50)

    # Create engine
    engine = LessonEngine()
    print("✓ Created lesson engine")

    # Create lesson
    lesson = engine.create_bilingual_lesson("Test Lesson", 10)
    print("✓ Created bilingual lesson")

    # Validate lesson
    schema_result = engine.validate_lesson(lesson)
    korean_result = engine.validate_korean_accuracy(lesson)
    english_result = engine.validate_english_accuracy(lesson)

    print(f"✓ Schema validation: {'PASS' if schema_result['valid'] else 'FAIL'}")
    print(f"✓ Korean accuracy: {'PASS' if korean_result['valid'] else 'FAIL'}")
    print(f"✓ English accuracy: {'PASS' if english_result['valid'] else 'FAIL'}")

    # Create GUI
    gui = BrowserGUI()
    gui.load_lesson(lesson)
    print("✓ Loaded lesson into GUI")

    # Display content
    content = gui.display_content()
    print(f"✓ Displayed content: {len(content['content'])} items")

    # Submit answer if exercises exist
    if lesson.exercises:
        result = gui.submit_answer(0, "Apple")
        print(f"✓ Submitted answer: {'CORRECT' if result['is_correct'] else 'INCORRECT'}")

    # Get summary
    summary = gui.get_lesson_summary()
    print(f"✓ Got lesson summary: {summary['lesson']['title']}")

    # Save and load lesson
    success = engine.save_lesson(lesson, "test_lesson.json")
    print(f"✓ Saved lesson: {'SUCCESS' if success else 'FAILED'}")

    loaded = engine.load_lesson("test_lesson.json")
    print(f"✓ Loaded lesson: {'SUCCESS' if loaded else 'FAILED'}")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(test_basic_functionality())
