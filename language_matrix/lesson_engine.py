"""Lesson engine for Language Matrix"""

from typing import Dict, Any, List, Optional
from .lesson_schema import LessonPlan, LessonSchema, LessonType, LessonContent, Exercise, SpokenPhonetic, PhonologicalExplanation
from .lesson_validator import LessonValidator


class LessonEngine:
    """Engine for generating and managing Korean language lessons"""

    def __init__(self):
        self.schema_validator = LessonSchema()
        self.lessons: Dict[str, LessonPlan] = {}
        self.validator = LessonValidator()

    def create_lesson(
        self,
        lesson_type: LessonType,
        title: str,
        content: List[LessonContent],
        duration_minutes: int,
        **metadata
    ) -> LessonPlan:
        """Create a new lesson plan"""
        lesson_id = f"lesson_{len(self.lessons) + 1}"

        lesson_plan = LessonPlan(
            id=lesson_id,
            title=title,
            type=lesson_type,
            duration_minutes=duration_minutes,
            content=content,
            metadata=metadata,
            created_at=str(self._get_current_time()),
        )

        self.lessons[lesson_id] = lesson_plan
        return lesson_plan

    def add_exercise_to_lesson(
        self,
        lesson_id: str,
        exercise: Exercise
    ) -> bool:
        """Add an exercise to an existing lesson"""
        if lesson_id not in self.lessons:
            return False

        lesson = self.lessons[lesson_id]
        lesson.exercises.append(exercise)
        return True

    def validate_lesson(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate a lesson plan against the schema"""
        return self.schema_validator.validate(lesson_plan)

    def validate_korean_accuracy(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate Korean linguistic accuracy"""
        return self.validator.validate_korean_accuracy(lesson_plan)

    def validate_english_accuracy(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate English accuracy"""
        return self.validator.validate_english_accuracy(lesson_plan)

    def get_lesson(self, lesson_id: str) -> Optional[LessonPlan]:
        """Get a lesson by ID"""
        return self.lessons.get(lesson_id)

    def list_lessons(self, lesson_type: Optional[LessonType] = None) -> List[LessonPlan]:
        """List all lessons, optionally filtered by type"""
        if lesson_type:
            return [lesson for lesson in self.lessons.values() if lesson.type == lesson_type]
        return list(self.lessons.values())

    def verify_lesson(self, lesson_plan: LessonPlan) -> bool:
        """Mark a lesson as verified and perform final validation"""
        # Validate against schema
        schema_result = self.validate_lesson(lesson_plan)
        if not schema_result["valid"]:
            return False

        # Validate Korean accuracy
        korean_result = self.validate_korean_accuracy(lesson_plan)
        if not korean_result["valid"]:
            return False

        # Validate English accuracy
        english_result = self.validate_english_accuracy(lesson_plan)
        if not english_result["valid"]:
            return False

        # Mark as verified
        lesson_plan.verified = True
        return True

    def _get_current_time(self) -> str:
        """Get current time as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_lesson(self, lesson_plan: LessonPlan, filepath: str) -> bool:
        """Save a lesson plan to a file"""
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(lesson_plan.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving lesson: {e}")
            return False

    def load_lesson(self, filepath: str) -> Optional[LessonPlan]:
        """Load a lesson plan from a file"""
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                lesson_data = json.load(f)

            # Convert back to LessonPlan object
            lesson_plan = LessonPlan(
                id=lesson_data["id"],
                title=lesson_data["title"],
                type=LessonType(lesson_data["type"]),
                duration_minutes=lesson_data["duration_minutes"],
                content=[
                    LessonContent(
                        english=item["english"],
                        hangul=item["hangul"],
                        spoken_phonetic=SpokenPhonetic(
                            romanization=item["spoken_phonetic"]["romanization"],
                            pronunciation=item["spoken_phonetic"].get("pronunciation"),
                            stress_pattern=item["spoken_phonetic"].get("stress_pattern"),
                        ),
                        phonological_explanation=PhonologicalExplanation(
                            explanation=item["phonological_explanation"]["explanation"] if item["phonological_explanation"] else None,
                            changes=item["phonological_explanation"].get("changes", []) if item["phonological_explanation"] else [],
                            rules_applied=item["phonological_explanation"].get("rules_applied", []) if item["phonological_explanation"] else [],
                        ) if item["phonological_explanation"] else None,
                        grammar_notes=item.get("grammar_notes"),
                    )
                    for item in lesson_data["content"]
                ],
                exercises=[
                    Exercise(
                        type=ex["type"],
                        question=ex["question"],
                        options=ex["options"],
                        correct_answer=ex["correct_answer"],
                        explanation=ex.get("explanation"),
                    )
                    for ex in lesson_data.get("exercises", [])
                ],
                metadata=lesson_data.get("metadata", {}),
                verified=lesson_data.get("verified", False),
                created_at=lesson_data.get("created_at"),
            )

            self.lessons[lesson_plan.id] = lesson_plan
            return lesson_plan
        except Exception as e:
            print(f"Error loading lesson: {e}")
            return None

    def create_bilingual_lesson(self, title: str, duration_minutes: int = 10) -> LessonPlan:
        """Create a simple bilingual Korean lesson for testing"""
        content = [
            LessonContent(
                english="I eat apples",
                hangul="저는 사과를 먹습니다",
                spoken_phonetic=SpokenPhonetic(
                    romanization="jeo-neun sa-gwa-reul meok-seum-ni-da",
                    pronunciation="jeh-neun sah-gwah-reul mohk-seum-nee-dah",
                ),
                phonological_explanation=PhonologicalExplanation(
                    explanation="The verb ending -습니다 is a formal-polite form used in standard Korean. The object marker -를 is attached to the noun 사과 (apple) when it follows a consonant.",
                    changes=[],
                    rules_applied=["formal-polite ending", "object marking"],
                ),
            ),
            LessonContent(
                english="You should study hard",
                hangul="열심히 공부하세요",
                spoken_phonetic=SpokenPhonetic(
                    romanization="yeol-sim-hi gong-bu-ha-se-yo",
                    pronunciation="yehl-sheem-hee gong-boo-hah-seh-yoh",
                ),
                phonological_explanation=PhonologicalExplanation(
                    explanation="The imperative ending -하세요 is used to give advice or suggestions in a polite manner. The verb stem 공부 is followed by the polite ending -하세요.",
                    changes=[],
                    rules_applied=["advice suggestion", "polite ending"],
                ),
            ),
            LessonContent(
                english="I am hungry",
                hangul="배고프습니다",
                spoken_phonetic=SpokenPhonetic(
                    romanization="bae-go-peum-ni-da",
                    pronunciation="bah-geh-pheum-nee-dah",
                ),
                phonological_explanation=PhonologicalExplanation(
                    explanation="The adjective 배고프 (hungry) takes the formal-polite ending -습니다. The stem-final consonant 'ㅂ' changes to 'ㅁ' when followed by a vowel ending.",
                    changes=["ㅂ → ㅁ"],
                    rules_applied=["consonant assimilation", "formal ending"],
                ),
            ),
        ]

        lesson = self.create_lesson(
            lesson_type=LessonType.BILINGUAL,
            title=title,
            duration_minutes=duration_minutes,
            content=content,
        )

        # Add exercises for testing
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

        self.add_exercise_to_lesson(lesson.id, exercise1)
        self.add_exercise_to_lesson(lesson.id, exercise2)

        return lesson
