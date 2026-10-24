#!/usr/bin/env python3
"""Main entry point for Language Matrix"""

import sys
import os
from pathlib import Path
from language_matrix.lesson_engine import LessonEngine
from language_matrix.browser_gui import BrowserGUI
from language_matrix.lesson_schema import Exercise


def main():
    """Main function for Language Matrix"""
    print("Language Matrix - Korean Language Tutor")
    print("=" * 50)

    # Create the lesson engine
    engine = LessonEngine()

    # Create a sample lesson
    print("\nCreating sample lesson...")
    lesson = engine.create_bilingual_lesson("Formal Korean Lesson", 10)

    # Add some exercises
    exercise1 = Exercise(
        type="multiple_choice",
        question="What does '사과' mean?",
        options=["Apple", "Car", "Book"],
        correct_answer="Apple",
        explanation="사과 means apple in Korean.",
    )

    exercise2 = Exercise(
        type="multiple_choice",
        question="What does '먹습니다' mean?",
        options=["Eat", "Drink", "Sleep"],
        correct_answer="Eat",
        explanation="먹습니다 means eat in Korean.",
    )

    engine.add_exercise_to_lesson(lesson.id, exercise1)
    engine.add_exercise_to_lesson(lesson.id, exercise2)

    # Validate the lesson
    print("\nValidating lesson...")
    schema_result = engine.validate_lesson(lesson)
    korean_result = engine.validate_korean_accuracy(lesson)
    english_result = engine.validate_english_accuracy(lesson)

    print(f"Schema validation: {'PASS' if schema_result['valid'] else 'FAIL'}")
    print(f"Korean accuracy: {'PASS' if korean_result['valid'] else 'FAIL'}")
    print(f"English accuracy: {'PASS' if english_result['valid'] else 'FAIL'}")

    # Display lesson summary
    print("\nLesson Summary:")
    print(f"Title: {lesson.title}")
    print(f"Type: {lesson.type.value}")
    print(f"Duration: {lesson.duration_minutes} minutes")
    print(f"Content items: {len(lesson.content)}")
    print(f"Exercises: {len(lesson.exercises)}")

    # Create browser GUI
    print("\nStarting browser GUI...")
    gui = BrowserGUI()
    gui.load_lesson(lesson)

    # Display first content
    content = gui.display_content()
    print(f"\nContent {gui.current_content_index + 1}/{len(lesson.content)}:")
    print(f"English: {content['content']['english']}")
    print(f"Hangul: {content['content']['hangul']}")
    print(f"Romanization: {content['content']['romanization']}")

    # Save lesson to file
    print("\nSaving lesson to file...")
    lesson_path = "lessons/sample_lesson.json"
    Path(lesson_path).parent.mkdir(parents=True, exist_ok=True)
    success = engine.save_lesson(lesson, lesson_path)
    print(f"Lesson saved to {lesson_path}: {'SUCCESS' if success else 'FAILED'}")

    # Load lesson from file
    print("\nLoading lesson from file...")
    loaded_lesson = engine.load_lesson(lesson_path)
    print(f"Lesson loaded: {'SUCCESS' if loaded_lesson else 'FAILED'}")

    # Generate HTML for browser
    print("\nGenerating HTML for browser...")
    html = gui.get_html()
    html_path = "lessons/sample_lesson.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML saved to {html_path}")

    print("\n" + "=" * 50)
    print("Language Matrix is ready!")
    print("Open the HTML file in a browser to view the lesson.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
