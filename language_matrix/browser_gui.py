"""Browser GUI for Language Matrix"""

from typing import Optional, Dict, Any
from html import escape
from .lesson_schema import LessonPlan


class BrowserGUI:
    """Browser-based GUI for displaying Korean lessons"""

    def __init__(self):
        self.current_lesson: Optional[LessonPlan] = None
        self.current_content_index = 0
        self.exercise_index = 0
        self.user_answers: Dict[str, str] = {}

    def load_lesson(self, lesson_plan: LessonPlan) -> None:
        """Load a lesson into the GUI"""
        self.current_lesson = lesson_plan
        self.current_content_index = 0
        self.exercise_index = 0
        self.user_answers = {}

    def display_content(self, content_index: int = None) -> Dict[str, Any]:
        """Display content at a specific index"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if content_index is None:
            content_index = self.current_content_index

        if content_index >= len(self.current_lesson.content):
            return {"error": "No more content"}

        content_item = self.current_lesson.content[content_index]

        return {
            "content": {
                "english": content_item.english,
                "hangul": content_item.hangul,
                "romanization": content_item.spoken_phonetic.romanization,
                "pronunciation": content_item.spoken_phonetic.pronunciation,
                "stress_pattern": content_item.spoken_phonetic.stress_pattern,
                "phonological_explanation": content_item.phonological_explanation.explanation if content_item.phonological_explanation else None,
                "grammar_notes": content_item.grammar_notes,
            },
            "progress": {
                "total": len(self.current_lesson.content),
                "current": content_index + 1,
            },
        }

    def display_exercise(self, exercise_index: int = None) -> Dict[str, Any]:
        """Display an exercise at a specific index"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if not self.current_lesson.exercises:
            return {"error": "No exercises available"}

        if exercise_index is None:
            exercise_index = self.exercise_index

        if exercise_index >= len(self.current_lesson.exercises):
            return {"error": "No more exercises"}

        exercise = self.current_lesson.exercises[exercise_index]

        return {
            "exercise": {
                "type": exercise.type,
                "question": exercise.question,
                "options": exercise.options,
                "correct_answer": exercise.correct_answer,
                "explanation": exercise.explanation,
            },
            "progress": {
                "total": len(self.current_lesson.exercises),
                "current": exercise_index + 1,
            },
        }

    def submit_answer(self, exercise_index: int, answer: str) -> Dict[str, Any]:
        """Submit an answer for an exercise"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if exercise_index >= len(self.current_lesson.exercises):
            return {"error": "Exercise index out of bounds"}

        exercise = self.current_lesson.exercises[exercise_index]

        is_correct = answer.strip().lower() == exercise.correct_answer.strip().lower()

        self.user_answers[f"exercise_{exercise_index}"] = {
            "answer": answer,
            "correct": is_correct,
        }

        return {
            "is_correct": is_correct,
            "correct_answer": exercise.correct_answer,
            "explanation": exercise.explanation,
        }

    def next_content(self) -> Dict[str, Any]:
        """Move to the next content item"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if self.current_content_index < len(self.current_lesson.content) - 1:
            self.current_content_index += 1
            return self.display_content(self.current_content_index)

        return {"error": "No more content"}

    def previous_content(self) -> Dict[str, Any]:
        """Move to the previous content item"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if self.current_content_index > 0:
            self.current_content_index -= 1
            return self.display_content(self.current_content_index)

        return {"error": "Already at first content"}

    def next_exercise(self) -> Dict[str, Any]:
        """Move to the next exercise"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if self.exercise_index < len(self.current_lesson.exercises) - 1:
            self.exercise_index += 1
            return self.display_exercise(self.exercise_index)

        return {"error": "No more exercises"}

    def get_lesson_summary(self) -> Dict[str, Any]:
        """Get a summary of the current lesson"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        return {
            "lesson": {
                "id": self.current_lesson.id,
                "title": self.current_lesson.title,
                "type": self.current_lesson.type.value,
                "duration_minutes": self.current_lesson.duration_minutes,
                "content_count": len(self.current_lesson.content),
                "exercise_count": len(self.current_lesson.exercises),
                "verified": self.current_lesson.verified,
            },
            "progress": {
                "content_completed": self.current_content_index + 1,
                "content_total": len(self.current_lesson.content),
                "exercises_completed": sum(
                    1 for i in range(self.exercise_index)
                    if f"exercise_{i}" in self.user_answers
                ),
                "exercises_total": len(self.current_lesson.exercises),
            },
            "user_answers": self.user_answers,
        }

    def reset_progress(self) -> None:
        """Reset the lesson progress"""
        if self.current_lesson:
            self.current_content_index = 0
            self.exercise_index = 0
            self.user_answers = {}

    def get_html(self) -> str:
        """Generate HTML for the lesson"""
        if not self.current_lesson:
            return "<h1>No lesson loaded</h1>"

        lesson = self.current_lesson
        content = self.display_content()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{lesson.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        .content {{
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .hangul {{
            font-size: 2em;
            color: #333;
            margin: 10px 0;
        }}
        .english {{
            font-size: 1.2em;
            color: #666;
            margin: 10px 0;
        }}
        .romanization {{
            font-size: 1.1em;
            color: #888;
            margin: 10px 0;
            font-style: italic;
        }}
        .explanation {{
            margin-top: 20px;
            padding: 15px;
            background-color: #e9e9e9;
            border-left: 4px solid #4CAF50;
        }}
        .exercise {{
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .option {{
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        }}
        .option:hover {{
            background-color: #f0f0f0;
        }}
        .correct {{
            background-color: #d4edda;
            border-color: #28a745;
        }}
        .incorrect {{
            background-color: #f8d7da;
            border-color: #dc3545;
        }}
    </style>
</head>
<body>
    <h1>{lesson.title}</h1>
    <p>Type: {lesson.type.value} | Duration: {lesson.duration_minutes} minutes</p>

    <div class="content">
        <div class="hangul">{content['content']['hangul']}</div>
        <div class="english">{content['content']['english']}</div>
        <div class="romanization">{content['content']['romanization']}</div>
        {self._get_explanation_html(content['content'])}
    </div>

    <div class="exercise">
        <h2>Exercise</h2>
        <p>{self._get_exercise_html()}</p>
    </div>

    <button onclick="nextContent()">Next Content</button>
    <button onclick="previousContent()">Previous Content</button>

    <script>
        function nextContent() {{
            window.location.href = '?next_content';
        }}
        function previousContent() {{
            window.location.href = '?previous_content';
        }}
    </script>
</body>
</html>
"""

        return html

    def _get_explanation_html(self, content_item: Dict[str, Any]) -> str:
        """Get HTML for phonological explanation"""
        explanation = content_item.get("phonological_explanation")
        if isinstance(explanation, str) and explanation:
            return ('<div class="explanation"><strong>Explanation:</strong> '
                    f'{escape(explanation)}</div>')
        if isinstance(explanation, dict):
            text = explanation.get("explanation", "")
            html = f'<div class="explanation"><strong>Explanation:</strong> {escape(str(text))}</div>'

            if explanation.get("changes"):
                changes = ", ".join(str(change) for change in explanation["changes"])
                html += f'<div class="explanation"><strong>Changes:</strong> {escape(changes)}</div>'

            if explanation.get("rules_applied"):
                rules = ", ".join(str(rule) for rule in explanation["rules_applied"])
                html += f'<div class="explanation"><strong>Rules Applied:</strong> {escape(rules)}</div>'

            return html

        return ""

    def _get_exercise_html(self) -> str:
        """Get HTML for current exercise"""
        if not self.current_lesson or not self.current_lesson.exercises:
            return "No exercises available"

        exercise = self.display_exercise()["exercise"]

        html = f'<p><strong>Question:</strong> {exercise["question"]}</p>'

        for option in exercise.get("options", []):
            html += f'<div class="option" onclick="selectOption(this, \'{option}\')">{option}</div>'

        html += f'<p><strong>Correct Answer:</strong> {exercise["correct_answer"]}</p>'

        if exercise.get("explanation"):
            html += f'<p><strong>Explanation:</strong> {exercise["explanation"]}</p>'

        html += '''
        <button onclick="submitAnswer()">Submit Answer</button>
        <script>
            let selectedAnswer = "";
            function selectOption(element, answer) {{
                selectedAnswer = answer;
                document.querySelectorAll(".option").forEach(el => el.classList.remove("correct", "incorrect"));
                element.classList.add("selected");
            }}
            function submitAnswer() {{
                window.location.href = '?submit=' + selectedAnswer;
            }}
        </script>
        '''

        return html
