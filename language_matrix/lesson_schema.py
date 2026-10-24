"""Lesson schema definition for Language Matrix"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class LessonType(Enum):
    """Types of lessons supported"""
    BILINGUAL = "bilingual"
    GRAMMAR = "grammar"
    PHONOLOGY = "phonology"
    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    READING = "reading"


@dataclass
class PhonologicalExplanation:
    """Phonological explanation for Korean text"""
    explanation: str
    changes: List[str] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)


@dataclass
class SpokenPhonetic:
    """Spoken phonetic rendering"""
    romanization: str
    pronunciation: Optional[str] = None
    stress_pattern: Optional[str] = None


@dataclass
class LessonContent:
    """Content of a lesson item"""
    english: str
    hangul: str
    spoken_phonetic: SpokenPhonetic
    phonological_explanation: Optional[PhonologicalExplanation] = None
    grammar_notes: Optional[str] = None


@dataclass
class Exercise:
    """Exercise item within a lesson"""
    type: str
    question: str
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: Optional[str] = None


@dataclass
class LessonPlan:
    """Complete lesson plan structure"""
    id: str
    title: str
    type: LessonType
    duration_minutes: int
    content: List[LessonContent]
    exercises: List[Exercise] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert lesson plan to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "duration_minutes": self.duration_minutes,
            "content": [
                {
                    "english": item.english,
                    "hangul": item.hangul,
                    "spoken_phonetic": {
                        "romanization": item.spoken_phonetic.romanization,
                        "pronunciation": item.spoken_phonetic.pronunciation,
                        "stress_pattern": item.spoken_phonetic.stress_pattern,
                    },
                    "phonological_explanation": {
                        "explanation": item.phonological_explanation.explanation if item.phonological_explanation else None,
                        "changes": item.phonological_explanation.changes if item.phonological_explanation else [],
                        "rules_applied": item.phonological_explanation.rules_applied if item.phonological_explanation else [],
                    } if item.phonological_explanation else None,
                    "grammar_notes": item.grammar_notes,
                }
                for item in self.content
            ],
            "exercises": [
                {
                    "type": ex.type,
                    "question": ex.question,
                    "options": ex.options,
                    "correct_answer": ex.correct_answer,
                    "explanation": ex.explanation,
                }
                for ex in self.exercises
            ],
            "metadata": self.metadata,
            "verified": self.verified,
            "created_at": self.created_at,
        }


@dataclass
class LessonSchema:
    """Schema validator for lesson plans"""

    def validate(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate a lesson plan against the schema"""
        errors = []

        # Check required fields
        if not lesson_plan.id:
            errors.append("Lesson ID is required")

        if not lesson_plan.title:
            errors.append("Lesson title is required")

        if not lesson_plan.type:
            errors.append("Lesson type is required")

        if lesson_plan.duration_minutes <= 0:
            errors.append("Duration must be positive")

        if not lesson_plan.content:
            errors.append("Lesson must have at least one content item")

        # Validate content items
        for i, content_item in enumerate(lesson_plan.content):
            if not content_item.english:
                errors.append(f"Content item {i}: English text is required")

            if not content_item.hangul:
                errors.append(f"Content item {i}: Hangul text is required")

            if not content_item.spoken_phonetic.romanization:
                errors.append(f"Content item {i}: Spoken phonetic romanization is required")

            # Validate phonological explanation if present
            if content_item.phonological_explanation:
                if not content_item.phonological_explanation.explanation:
                    errors.append(f"Content item {i}: Phonological explanation is required when provided")

        # Validate exercises
        for i, exercise in enumerate(lesson_plan.exercises):
            if not exercise.type:
                errors.append(f"Exercise {i}: Type is required")

            if not exercise.question:
                errors.append(f"Exercise {i}: Question is required")

            if not exercise.correct_answer:
                errors.append(f"Exercise {i}: Correct answer is required")

            if exercise.type in ["multiple_choice", "matching"]:
                if not exercise.options:
                    errors.append(f"Exercise {i}: Options are required for multiple choice")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
        }
