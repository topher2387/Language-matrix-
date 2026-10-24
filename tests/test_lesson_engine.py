"""Unit tests for Language Matrix"""

import unittest
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language_matrix.lesson_engine import LessonEngine
from language_matrix.browser_gui import BrowserGUI
from language_matrix.lesson_schema import (
    LessonPlan, LessonSchema, LessonType,
    LessonContent, Exercise, SpokenPhonetic, PhonologicalExplanation
)


class TestLessonSchema(unittest.TestCase):
    """Test the lesson schema validation"""

    def setUp(self):
        self.schema = LessonSchema()

    def test_valid_lesson_plan(self):
        """Test validation of a valid lesson plan"""
        lesson_plan = LessonPlan(
            id="test_lesson",
            title="Test Lesson",
            type=LessonType.BILINGUAL,
            duration_minutes=10,
            content=[
                LessonContent(
                    english="I eat apples",
                    hangul="저는 사과를 먹습니다",
                    spoken_phonetic=SpokenPhonetic(
                        romanization="jeo-neun sa-gwa-reul meok-seum-ni-da",
                        pronunciation="jeh-neun sah-gwah-reul mohk-seum-nee-dah",
                    ),
                )
            ],
        )

        result = self.schema.validate(lesson_plan)
        self.assertTrue(result["valid"])

    def test_missing_id(self):
        """Test validation with missing lesson ID"""
        lesson_plan = LessonPlan(
            id="",
            title="Test Lesson",
            type=LessonType.BILINGUAL,
            duration_minutes=10,
            content=[],
        )

        result = self.schema.validate(lesson_plan)
        self.assertFalse(result["valid"])
        self.assertIn("Lesson ID is required", result["errors"])

    def test_missing_title(self):
        """Test validation with missing title"""
        lesson_plan = LessonPlan(
            id="test_lesson",
            title="",
            type=LessonType.BILINGUAL,
            duration_minutes=10,
            content=[],
        )

        result = self.schema.validate(lesson_plan)
        self.assertFalse(result["valid"])
        self.assertIn("Lesson title is required", result["errors"])

    def test_to_dict_conversion(self):
        """Test conversion of lesson plan to dictionary"""
        lesson_plan = LessonPlan(
            id="test_lesson",
            title="Test Lesson",
            type=LessonType.BILINGUAL,
            duration_minutes=10,
            content=[
                LessonContent(
                    english="I eat apples",
                    hangul="저는 사과를 먹습니다",
                    spoken_phonetic=SpokenPhonetic(
                        romanization="jeo-neun sa-gwa-reul meok-seum-ni-da",
                        pronunciation="jeh-neun sah-gwah-reul mohk-seum-nee-dah",
                    ),
                    phonological_explanation=PhonologicalExplanation(
                        explanation="Test explanation",
                        changes=[],
                        rules_applied=[],
                    ),
                )
            ],
            exercises=[
                Exercise(
                    type="multiple_choice",
                    question="What does '사과' mean?",
                    options=["Apple", "Car", "Book"],
                    correct_answer="Apple",
                    explanation="사과 means apple in Korean.",
                )
            ],
        )

        lesson_dict = lesson_plan.to_dict()

        self.assertEqual(lesson_dict["id"], "test_lesson")
        self.assertEqual(lesson_dict["title"], "Test Lesson")
        self.assertEqual(len(lesson_dict["content"]), 1)
        self.assertEqual(len(lesson_dict["exercises"]), 1)


class TestLessonEngine(unittest.TestCase):
    """Test the lesson engine functionality"""

    def setUp(self):
        self.engine = LessonEngine()

    def test_create_lesson(self):
        """Test creating a new lesson"""
        lesson = self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Test Lesson",
            content=[
                LessonContent(
                    english="I eat apples",
                    hangul="저는 사과를 먹습니다",
                    spoken_phonetic=SpokenPhonetic(
                        romanization="jeo-neun sa-gwa-reul meok-seum-ni-da",
                        pronunciation="jeh-neun sah-gwah-reul mohk-seum-nee-dah",
                    ),
                )
            ],
            duration_minutes=10,
        )

        self.assertIsNotNone(lesson)
        self.assertEqual(lesson.title, "Test Lesson")
        self.assertEqual(lesson.duration_minutes, 10)

    def test_add_exercise(self):
        """Test adding an exercise to a lesson"""
        lesson = self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Test Lesson",
            content=[],
            duration_minutes=10,
        )

        exercise = Exercise(
            type="multiple_choice",
            question="What does '사과' mean?",
            options=["Apple", "Car"],
            correct_answer="Apple",
        )

        result = self.engine.add_exercise_to_lesson(lesson.id, exercise)
        self.assertTrue(result)

        loaded_lesson = self.engine.get_lesson(lesson.id)
        self.assertEqual(len(loaded_lesson.exercises), 1)

    def test_validate_lesson(self):
        """Test lesson validation"""
        lesson = self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Test Lesson",
            content=[
                LessonContent(
                    english="I eat apples",
                    hangul="저는 사과를 먹습니다",
                    spoken_phonetic=SpokenPhonetic(
                        romanization="jeo-neun sa-gwa-reul meok-seum-ni-da",
                        pronunciation="jeh-neun sah-gwah-reul mohk-seum-nee-dah",
                    ),
                )
            ],
            duration_minutes=10,
        )

        result = self.engine.validate_lesson(lesson)
        self.assertTrue(result["valid"])

    def test_create_bilingual_lesson(self):
        """Test creating a simple bilingual lesson"""
        lesson = self.engine.create_bilingual_lesson("Test Lesson", 10)

        self.assertIsNotNone(lesson)
        self.assertEqual(len(lesson.content), 3)
        self.assertEqual(lesson.type, LessonType.BILINGUAL)

    def test_get_lesson(self):
        """Test retrieving a lesson by ID"""
        lesson = self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Test Lesson",
            content=[],
            duration_minutes=10,
        )

        retrieved_lesson = self.engine.get_lesson(lesson.id)
        self.assertEqual(retrieved_lesson, lesson)

    def test_list_lessons(self):
        """Test listing lessons"""
        self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Lesson 1",
            content=[],
            duration_minutes=10,
        )

        self.engine.create_lesson(
            lesson_type=LessonType.GRAMMAR,
            title="Lesson 2",
            content=[],
            duration_minutes=15,
        )

        all_lessons = self.engine.list_lessons()
        self.assertEqual(len(all_lessons), 2)

    def test_list_lessons_by_type(self):
        """Test listing lessons filtered by type"""
        self.engine.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title="Bilingual Lesson",
            content=[],
            duration_minutes=10,
        )

        self.engine.create_lesson(
            lesson_type=LessonType.GRAMMAR,
            title="Grammar Lesson",
            content=[],
            duration_minutes=15,
        )

        bilingual_lessons = self.engine.list_lessons(LessonType.BILINGUAL)
        self.assertEqual(len(bilingual_lessons), 1)
        self.assertEqual(bilingual_lessons[0].title, "Bilingual Lesson")


class TestLessonValidator(unittest.TestCase):
    """Test the lesson validator"""

    def setUp(self):
        self.engine = LessonEngine()
        self.lesson = self.engine.create_bilingual_lesson("Test Lesson", 10)

    def test_validate_korean_accuracy(self):
        """Test Korean language accuracy validation"""
        result = self.engine.validate_korean_accuracy(self.lesson)

        # Should be valid since we created it with proper Korean
        self.assertTrue(result["valid"])

    def test_validate_english_accuracy(self):
        """Test English language accuracy validation"""
        result = self.engine.validate_english_accuracy(self.lesson)

        # Should be valid since we created it with proper English
        self.assertTrue(result["valid"])


class TestBrowserGUI(unittest.TestCase):
    """Test the browser GUI functionality"""

    def setUp(self):
        self.engine = LessonEngine()
        self.lesson = self.engine.create_bilingual_lesson("Test Lesson", 10)
        self.gui = BrowserGUI()

    def test_load_lesson(self):
        """Test loading a lesson into the GUI"""
        self.gui.load_lesson(self.lesson)

        self.assertIsNotNone(self.gui.current_lesson)
        self.assertEqual(self.gui.current_lesson.id, self.lesson.id)

    def test_display_content(self):
        """Test displaying content"""
        self.gui.load_lesson(self.lesson)

        content = self.gui.display_content()

        self.assertIsNotNone(content["content"])
        self.assertEqual(content["progress"]["total"], 3)

    def test_submit_answer(self):
        """Test submitting an exercise answer"""
        self.gui.load_lesson(self.lesson)

        result = self.gui.submit_answer(0, "Apple")

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["correct_answer"], "Apple")

    def test_submit_wrong_answer(self):
        """Test submitting a wrong answer"""
        self.gui.load_lesson(self.lesson)

        result = self.gui.submit_answer(0, "Car")

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["correct_answer"], "Apple")

    def test_next_content(self):
        """Test moving to the next content"""
        self.gui.load_lesson(self.lesson)

        result = self.gui.next_content()

        self.assertIsNotNone(result["content"])
        self.assertEqual(self.gui.current_content_index, 1)

    def test_get_lesson_summary(self):
        """Test getting lesson summary"""
        self.gui.load_lesson(self.lesson)

        summary = self.gui.get_lesson_summary()

        self.assertIsNotNone(summary["lesson"])
        self.assertEqual(summary["lesson"]["title"], "Test Lesson")
        self.assertEqual(len(summary["user_answers"]), 0)

    def test_get_html_renders_phonological_explanation(self):
        """HTML generation accepts the explanation string returned by display_content."""
        self.gui.load_lesson(self.lesson)

        html = self.gui.get_html()

        self.assertIn("object marker", html)


if __name__ == "__main__":
    unittest.main()
