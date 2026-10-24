#!/usr/bin/env python3
"""Enhanced Lesson Generator for Language Matrix"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EnhancedLesson:
    """Enhanced lesson structure with comprehensive content"""
    id: str
    title: str
    level: str  # beginner, intermediate, advanced
    type: str  # vocabulary, grammar, cultural, business, etc.
    duration_minutes: int
    content: List[Dict[str, Any]]
    exercises: List[Dict[str, Any]]
    learning_objectives: List[str]
    prerequisites: List[str]
    key_points: List[str]


class EnhancedLessonGenerator:
    """Generate comprehensive, structured Korean lessons"""

    # Vocabulary patterns for different levels
    VOCABULARY_PATTERNS = {
        "beginner": {
            "greetings": [
                {"korean": "안녕하세요", "english": "Hello (formal)", "context": "Formal greeting"},
                {"korean": "반갑습니다", "english": "Nice to meet you", "context": "Formal introduction"},
                {"korean": "감사합니다", "english": "Thank you", "context": "Formal gratitude"},
                {"korean": "죄송합니다", "english": "I'm sorry", "context": "Formal apology"},
            ],
            "basics": [
                {"korean": "사과", "english": "Apple", "context": "Common fruit"},
                {"korean": "밥", "english": "Rice", "context": "Staple food"},
                {"korean": "친구", "english": "Friend", "context": "Social relationship"},
                {"korean": "책", "english": "Book", "context": "Reading material"},
            ],
            "numbers": [
                {"korean": "하나", "english": "One", "context": "Number"},
                {"korean": "둘", "english": "Two", "context": "Number"},
                {"korean": "셋", "english": "Three", "context": "Number"},
                {"korean": "넷", "english": "Four", "context": "Number"},
            ]
        },
        "intermediate": {
            "phrases": [
                {"korean": "오늘 날씨가 좋습니다", "english": "The weather is good today", "context": "Weather description"},
                {"korean": "많이 배웠습니다", "english": "I learned a lot", "context": "Learning reflection"},
                {"korean": "시간이 필요합니다", "english": "I need time", "context": "Requesting time"},
                {"korean": "도움이 필요합니다", "english": "I need help", "context": "Requesting help"},
            ],
            "opinions": [
                {"korean": "생각합니다", "english": "I think", "context": "Opinion expression"},
                {"korean": "중요합니다", "english": "It's important", "context": "Emphasizing importance"},
                {"korean": "좋습니다", "english": "It's good", "context": "Expressing preference"},
                {"korean": "필요합니다", "english": "It's necessary", "context": "Expressing necessity"},
            ]
        },
        "advanced": {
            "professional": [
                {"korean": "프로젝트를 진행합니다", "english": "I am proceeding with the project", "context": "Business context"},
                {"korean": "협력이 필요합니다", "english": "Collaboration is needed", "context": "Business collaboration"},
                {"korean": "목표를 달성합니다", "english": "I achieve my goals", "context": "Business achievement"},
                {"korean": "전략을 수립합니다", "english": "I establish strategies", "context": "Business planning"},
            ],
            "complex": [
                {"korean": "어떻게 해결할 수 있을까요?", "english": "How can we solve this?", "context": "Problem solving"},
                {"korean": "이것은 중요한 문제입니다", "english": "This is an important issue", "context": "Issue discussion"},
                {"korean": "우리는 함께 일해야 합니다", "english": "We need to work together", "context": "Teamwork"},
            ]
        }
    }

    # Grammar patterns with explanations
    GRAMMAR_PATTERNS = {
        "beginner": [
            {
                "pattern": "Noun + 을/를",
                "explanation": "Object marker -을/를 attaches to nouns ending in consonants (으) and vowels (를)",
                "example": "사과를 먹습니다 (I eat apples)",
                "rule": "Object marking"
            },
            {
                "pattern": "Noun + 이/가",
                "explanation": "Subject marker -이/가 marks the subject of a sentence",
                "example": "저는 학생입니다 (I am a student)",
                "rule": "Subject marking"
            }
        ],
        "intermediate": [
            {
                "pattern": "Verb stem + 아/어",
                "explanation": "Connects verb stems to conjugations",
                "example": "가서 (go and...)",
                "rule": "Verb conjugation"
            },
            {
                "pattern": "Noun + 이야",
                "explanation": "Noun + 이야 indicates a topic or subject",
                "example": "사과 이야기 (about apples)",
                "rule": "Topic marking"
            }
        ],
        "advanced": [
            {
                "pattern": "Formal ending -습니다",
                "explanation": "Formal-polite ending used in standard Korean",
                "example": "먹습니다 (eat - formal)",
                "rule": "Formal ending"
            },
            {
                "pattern": "Honorific -세요",
                "explanation": "Honorific ending -세요 indicates respect",
                "example": "가세요 (go - honorific)",
                "rule": "Honorific usage"
            }
        ]
    }

    # Cultural context notes
    CULTURAL_CONTEXTS = {
        "beginner": [
            "Korean culture values respect and politeness in speech",
            "Formal endings are important in professional settings",
            "Greetings show respect and establish relationships"
        ],
        "intermediate": [
            "Understanding context helps choose appropriate language",
            "Korean speakers often use indirect communication",
            "Non-verbal cues are important in Korean communication"
        ],
        "advanced": [
            "Business culture emphasizes relationships and trust",
            "Hierarchy in Korean society affects communication",
            "Understanding cultural nuances is crucial for success"
        ]
    }

    def create_beginner_vocabulary_lesson(self, title: str = "Korean Basics - Vocabulary", level: str = "beginner") -> EnhancedLesson:
        """Create a beginner vocabulary lesson"""
        vocabulary = self.VOCABULARY_PATTERNS.get(level, {}).get("basics", [])

        content = []
        exercises = []

        for i, vocab in enumerate(vocabulary[:6]):
            content.append({
                "english": vocab["english"],
                "hangul": vocab["korean"],
                "romanization": self._romanize(vocab["korean"]),
                "pronunciation": self._phonetic(vocab["korean"]),
                "phonological_explanation": {
                    "explanation": vocab["context"],
                    "changes": [],
                    "rules_applied": ["vocabulary"]
                }
            })

            # Create exercise
            exercises.append({
                "type": "multiple_choice",
                "question": f"What does '{vocab['korean']}' mean?",
                "options": self._create_options(vocab["english"], ["apple", "car", "book"]),
                "correct_answer": vocab["english"],
                "explanation": f"{vocab['korean']} means '{vocab['english']}' in Korean.",
                "id": f"vocab_{i}"
            })

        return EnhancedLesson(
            id=f"lesson_{datetime.now().timestamp()}",
            title=title,
            level=level,
            type="vocabulary",
            duration_minutes=15,
            content=content,
            exercises=exercises,
            learning_objectives=[
                "Learn basic Korean vocabulary",
                "Understand pronunciation",
                "Practice vocabulary recognition"
            ],
            prerequisites=["None"],
            key_points=[
                "Vocabulary is the foundation of language learning",
                "Practice regularly to improve retention",
                "Context helps with understanding"
            ]
        )

    def create_intermediate_grammar_lesson(self, title: str = "Korean Grammar - Intermediate", level: str = "intermediate") -> EnhancedLesson:
        """Create an intermediate grammar lesson"""
        grammar_patterns = self.GRAMMAR_PATTERNS.get(level, [])

        content = []
        exercises = []

        for i, pattern in enumerate(grammar_patterns[:4]):
            content.append({
                "english": f"Understanding {pattern['pattern']}",
                "hangul": pattern["example"].split()[0] if " " in pattern["example"] else "",
                "romanization": self._romanize(pattern["example"]),
                "pronunciation": self._phonetic(pattern["example"]),
                "phonological_explanation": {
                    "explanation": pattern["explanation"],
                    "changes": [],
                    "rules_applied": [pattern["rule"]]
                }
            })

            # Create exercise
            exercises.append({
                "type": "multiple_choice",
                "question": f"What grammar rule does '{pattern['example']}' demonstrate?",
                "options": [pattern["rule"], "Subject marking", "Object marking", "Time expression"],
                "correct_answer": pattern["rule"],
                "explanation": pattern["explanation"],
                "id": f"grammar_{i}"
            })

        return EnhancedLesson(
            id=f"lesson_{datetime.now().timestamp()}",
            title=title,
            level=level,
            type="grammar",
            duration_minutes=20,
            content=content,
            exercises=exercises,
            learning_objectives=[
                "Understand intermediate grammar patterns",
                "Apply grammar rules in context",
                "Recognize grammatical structures"
            ],
            prerequisites=["Basic Korean vocabulary"],
            key_points=[
                "Grammar rules provide structure to language",
                "Practice makes perfect",
                "Context is crucial for understanding"
            ]
        )

    def create_cultural_context_lesson(self, title: str = "Korean Culture - Context", level: str = "beginner") -> EnhancedLesson:
        """Create a cultural context lesson"""
        contexts = self.CULTURAL_CONTEXTS.get(level, [])

        content = []
        exercises = []

        for i, context in enumerate(contexts[:3]):
            content.append({
                "english": context,
                "hangul": "한국 문화",  # Korean translation placeholder
                "romanization": "han-guk mun-hwa",
                "pronunciation": "han-gook moon-hwa",
                "phonological_explanation": {
                    "explanation": context,
                    "changes": [],
                    "rules_applied": ["cultural context"]
                }
            })

            # Create exercise
            exercises.append({
                "type": "multiple_choice",
                "question": "Why is respect important in Korean culture?",
                "options": [
                    "It shows politeness",
                    "It's a tradition",
                    "It's mandatory",
                    "It's unnecessary"
                ],
                "correct_answer": "It shows politeness",
                "explanation": context,
                "id": f"culture_{i}"
            })

        return EnhancedLesson(
            id=f"lesson_{datetime.now().timestamp()}",
            title=title,
            level=level,
            type="cultural",
            duration_minutes=15,
            content=content,
            exercises=exercises,
            learning_objectives=[
                "Understand Korean cultural context",
                "Appreciate cultural differences",
                "Apply cultural knowledge in communication"
            ],
            prerequisites=["Basic Korean vocabulary"],
            key_points=[
                "Cultural understanding enhances language learning",
                "Respect is fundamental in Korean society",
                "Context shapes communication styles"
            ]
        )

    def create_comprehensive_lesson(self, title: str, level: str, lesson_type: str = "vocabulary") -> EnhancedLesson:
        """Create a comprehensive lesson with multiple content types"""
        if lesson_type == "vocabulary":
            return self.create_beginner_vocabulary_lesson(title, level)
        elif lesson_type == "grammar":
            return self.create_intermediate_grammar_lesson(title, level)
        elif lesson_type == "cultural":
            return self.create_cultural_context_lesson(title, level)
        else:
            return self.create_beginner_vocabulary_lesson(title, level)

    def _romanize(self, hangul: str) -> str:
        """Romanize Korean text (simplified)"""
        romanizations = {
            "안녕하세요": "an-nyeong-ha-se-yo",
            "사과": "sa-gwa",
            "밥": "bae",
            "친구": "chin-gu",
            "책": "chaek",
            "하나": "ha-na",
            "둘": "dul",
            "셋": "set",
            "넷": "net",
            "오늘 날씨가 좋습니다": "eo-neul nal-si-ga jo-seum-ni-da",
            "많이 배웠습니다": "man-i bae-ut-seum-ni-da",
            "시간이 필요합니다": "si-ga-ni pil-yo-ham-ni-da",
            "도움이 필요합니다": "do-wu-mi pil-yo-ham-ni-da",
            "생각합니다": "saeng-gak-ham-ni-da",
            "중요합니다": "juung-yo-ham-ni-da",
            "좋습니다": "jo-seum-ni-da",
            "필요합니다": "pil-yo-ham-ni-da",
            "프로젝트를 진행합니다": "peu-ro-jeek-teu-reul jin-haeng-ham-ni-da",
            "협력이 필요합니다": "hyeop-rak-i pil-yo-ham-ni-da",
            "목표를 달성합니다": "mok-go-reul dal-seong-ham-ni-da",
            "전략을 수립합니다": "jeon-rak-eul su-rip-ham-ni-da",
            "어떻게 해결할 수 있을까요?": "eo-tteoh-kae hae-gyeol-hal su it-eul-kka-yo?",
            "이것은 중요한 문제입니다": "i-geo-seun juung-yo-han mun-je-im-ni-da",
            "우리는 함께 일해야 합니다": "u-ri-neun ham-ge il-hae-ya ham-ni-da",
        }
        return romanizations.get(hangul, hangul)

    def _phonetic(self, hangul: str) -> str:
        """Provide phonetic pronunciation (simplified)"""
        phonetics = {
            "안녕하세요": "ahn-nyong-hah-seh-yoh",
            "사과": "sah-gwah",
            "밥": "bah",
            "친구": "chin-goo",
            "책": "chayk",
            "하나": "hah-nah",
            "둘": "dool",
            "셋": "set",
            "넷": "net",
        }
        return phonetics.get(hangul, hangul)

    def _create_options(self, correct_answer: str, distractors: List[str]) -> List[str]:
        """Create multiple choice options with correct answer"""
        options = [correct_answer] + distractors
        import random
        random.shuffle(options)
        return options

    def generate_lesson(self, lesson_data: Dict[str, Any]) -> EnhancedLesson:
        """Generate lesson from lesson data"""
        return EnhancedLesson(**lesson_data)

    def save_lesson(self, lesson: EnhancedLesson, filepath: str = "lessons/enhanced_lessons.json"):
        """Save lesson to JSON file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Load existing lessons
        existing_lessons = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                    if isinstance(data, list):
                        existing_lessons = data
                    elif isinstance(data, dict):
                        existing_lessons = [data]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass

        # Add new lesson
        existing_lessons.append(asdict(lesson))

        # Save all lessons
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_lessons, f, indent=2, ensure_ascii=False)

        return {"success": True, "filepath": filepath}

    def load_lessons(self, filepath: str = "lessons/enhanced_lessons.json") -> List[EnhancedLesson]:
        """Load all lessons from JSON file"""
        lessons = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    lesson_data = json.loads(content)
                    lessons = [EnhancedLesson(**lesson) for lesson in lesson_data]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        return lessons
