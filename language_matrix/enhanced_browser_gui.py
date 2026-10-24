#!/usr/bin/env python3
"""Enhanced Browser GUI for Language Matrix"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class UserProgress:
    """Track user progress through lessons"""
    lesson_id: str
    completion_status: str  # "not_started", "in_progress", "completed"
    last_accessed: str
    accuracy_rate: float
    time_spent: int  # seconds
    exercises_completed: int
    total_exercises: int
    streak: int
    current_level: int


class EnhancedBrowserGUI:
    """Enhanced browser interface with progress tracking and modern features"""

    def __init__(self):
        self.user_progress: Dict[str, UserProgress] = {}
        self.current_lesson = None
        self.current_content_index = 0
        self.current_exercise_index = 0
        self.user_answers: Dict[str, Dict[str, Any]] = {}

    def load_lesson(self, lesson: Dict[str, Any]):
        """Load a lesson into the GUI with progress tracking"""
        self.current_lesson = lesson
        self.current_content_index = 0
        self.current_exercise_index = 0

        # Initialize progress if not exists
        if lesson['id'] not in self.user_progress:
            self.user_progress[lesson['id']] = UserProgress(
                lesson_id=lesson['id'],
                completion_status="not_started",
                last_accessed=datetime.now().isoformat(),
                accuracy_rate=0.0,
                time_spent=0,
                exercises_completed=0,
                total_exercises=len(lesson.get('exercises', [])),
                streak=0,
                current_level=1
            )

        # Update last accessed time
        self.user_progress[lesson['id']].last_accessed = datetime.now().isoformat()

    def display_content(self) -> Dict[str, Any]:
        """Display current content with enhanced formatting"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        content = self.current_lesson['content'][self.current_content_index]

        return {
            "content": content,
            "progress": {
                "current": self.current_content_index + 1,
                "total": len(self.current_lesson['content'])
            },
            "lesson_info": {
                "title": self.current_lesson['title'],
                "type": self.current_lesson.get('type', 'bilingual'),
                "level": self.current_lesson.get('level', 'beginner')
            }
        }

    def submit_answer(self, exercise_index: int, answer: str) -> Dict[str, Any]:
        """Submit an answer with enhanced feedback"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        exercise = self.current_lesson['exercises'][exercise_index]
        is_correct = answer.strip().lower() == exercise['correct_answer'].strip().lower()

        # Track answer
        self.user_answers[f"exercise_{exercise_index}"] = {
            "exercise_id": exercise['id'] if 'id' in exercise else f"ex_{exercise_index}",
            "answer": answer,
            "correct_answer": exercise['correct_answer'],
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }

        # Update progress
        progress = self.user_progress[self.current_lesson['id']]
        if not is_correct:
            progress.accuracy_rate = max(0, progress.accuracy_rate - 0.1)
        else:
            progress.accuracy_rate = min(100, progress.accuracy_rate + 0.1)
            progress.exercises_completed += 1

        # Update streak if exercise completed
        if is_correct:
            progress.streak += 1

        return {
            "is_correct": is_correct,
            "correct_answer": exercise['correct_answer'],
            "explanation": exercise.get('explanation', ''),
            "feedback": self._get_feedback(is_correct, exercise)
        }

    def _get_feedback(self, is_correct: bool, exercise: Dict[str, Any]) -> str:
        """Get enhanced feedback for the answer"""
        if is_correct:
            return "✅ Correct! Great job!"
        else:
            return f"❌ Incorrect. The correct answer is: {exercise['correct_answer']}"

    def next_content(self) -> Dict[str, Any]:
        """Move to next content with validation"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if self.current_content_index < len(self.current_lesson['content']) - 1:
            self.current_content_index += 1
            return self.display_content()
        else:
            return {"error": "End of content", "lesson_completed": True}

    def previous_content(self) -> Dict[str, Any]:
        """Move to previous content"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        if self.current_content_index > 0:
            self.current_content_index -= 1
            return self.display_content()

        return {"error": "Beginning of content"}

    def get_lesson_summary(self) -> Dict[str, Any]:
        """Get comprehensive lesson summary with progress"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        lesson_id = self.current_lesson['id']
        progress = self.user_progress.get(lesson_id, UserProgress(
            lesson_id=lesson_id,
            completion_status="not_started",
            last_accessed="",
            accuracy_rate=0.0,
            time_spent=0,
            exercises_completed=0,
            total_exercises=len(self.current_lesson.get('exercises', [])),
            streak=0,
            current_level=1
        ))

        return {
            "lesson": self.current_lesson,
            "progress": {
                "completion_status": progress.completion_status,
                "accuracy_rate": progress.accuracy_rate,
                "time_spent": progress.time_spent,
                "exercises_completed": progress.exercises_completed,
                "total_exercises": progress.total_exercises,
                "streak": progress.streak,
                "current_level": progress.current_level
            },
            "content_progress": {
                "current": self.current_content_index + 1,
                "total": len(self.current_lesson['content'])
            },
            "exercise_progress": {
                "current": self.current_exercise_index + 1,
                "total": len(self.current_lesson.get('exercises', []))
            }
        }

    def get_progress_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive progress dashboard"""
        lessons_completed = 0
        total_time_spent = 0
        total_accuracy = 0
        total_exercises = 0
        completed_exercises = 0

        for progress in self.user_progress.values():
            if progress.completion_status == "completed":
                lessons_completed += 1
                total_time_spent += progress.time_spent
                total_accuracy += progress.accuracy_rate
                completed_exercises += progress.exercises_completed

            total_exercises += progress.total_exercises

        # Calculate averages
        avg_accuracy = (total_accuracy / len(self.user_progress) * 100) if self.user_progress else 0
        completion_rate = (lessons_completed / len(self.user_progress) * 100) if self.user_progress else 0

        return {
            "total_lessons": len(self.user_progress),
            "lessons_completed": lessons_completed,
            "completion_rate": f"{completion_rate:.1f}%",
            "total_time_spent": total_time_spent,
            "total_accuracy": f"{avg_accuracy:.1f}%",
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "streaks": sum(p.streak for p in self.user_progress.values()),
            "current_level": max(p.current_level for p in self.user_progress.values()) if self.user_progress else 1
        }

    def complete_lesson(self) -> Dict[str, Any]:
        """Mark lesson as completed and update progress"""
        if not self.current_lesson:
            return {"error": "No lesson loaded"}

        lesson_id = self.current_lesson['id']
        progress = self.user_progress[lesson_id]

        if progress.completion_status == "in_progress":
            progress.completion_status = "completed"
            progress.current_level += 1

        return {
            "success": True,
            "lesson_id": lesson_id,
            "new_level": progress.current_level
        }

    def save_progress(self, progress_file: str = "user_progress.json"):
        """Save user progress to file"""
        progress_data = {
            "user_progress": {
                lesson_id: asdict(progress) for lesson_id, progress in self.user_progress.items()
            },
            "last_updated": datetime.now().isoformat()
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

        return {"success": True, "progress_file": progress_file}

    def load_progress(self, progress_file: str = "user_progress.json"):
        """Load user progress from file"""
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)

            self.user_progress = {}
            for lesson_id, progress_data in progress_data['user_progress'].items():
                self.user_progress[lesson_id] = UserProgress(**progress_data)

            return {"success": True, "loaded_lessons": len(self.user_progress)}

        except FileNotFoundError:
            return {"success": False, "error": "Progress file not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_html(self) -> str:
        """Generate enhanced HTML for browser"""
        return self._generate_html()

    def _generate_html(self) -> str:
        """Generate comprehensive HTML with enhanced features"""
        lesson = self.current_lesson

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Language Matrix - {lesson['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }}

        h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }}

        .subtitle {{
            color: #764ba2;
            margin-bottom: 30px;
            font-size: 1.2em;
        }}

        .progress-bar {{
            width: 100%;
            height: 10px;
            background-color: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
        }}

        .content {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            border-left: 5px solid #667eea;
        }}

        .hangul {{
            font-size: 2.5em;
            color: #2c3e50;
            margin: 20px 0;
            font-weight: 700;
        }}

        .english {{
            font-size: 1.5em;
            color: #7f8c8d;
            margin: 20px 0;
            font-style: italic;
        }}

        .romanization {{
            font-size: 1.3em;
            color: #95a5a6;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
        }}

        .explanation {{
            margin-top: 25px;
            padding: 20px;
            background-color: #e8f4f8;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .explanation strong {{
            color: #667eea;
        }}

        .exercise {{
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            border: 2px solid #e0e0e0;
        }}

        .exercise h2 {{
            color: #667eea;
            margin-bottom: 20px;
        }}

        .option {{
            padding: 15px 20px;
            margin: 10px 0;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: white;
            font-size: 1.1em;
        }}

        .option:hover {{
            background-color: #f5f7fa;
            border-color: #667eea;
            transform: translateX(5px);
        }}

        .option.selected {{
            background-color: #667eea;
            color: white;
            border-color: #667eea;
        }}

        .button-group {{
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }}

        button {{
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 600;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}

        .btn-secondary {{
            background-color: #f5f7fa;
            color: #667eea;
        }}

        .btn-secondary:hover {{
            background-color: #e8f4f8;
        }}

        .answer-feedback {{
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }}

        .answer-feedback.correct {{
            background-color: #d4edda;
            border: 2px solid #28a745;
            color: #155724;
            display: block;
            animation: fadeIn 0.5s ease;
        }}

        .answer-feedback.incorrect {{
            background-color: #f8d7da;
            border: 2px solid #dc3545;
            color: #721c24;
            display: block;
            animation: fadeIn 0.5s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .dashboard {{
            background-color: #f5f7fa;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
        }}

        .stat {{
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }}

        .stat-label {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}

        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #95a5a6;
            font-size: 1em;
        }}

        @media (max-width: 600px) {{
            .container {{
                padding: 20px;
            }}

            .hangul {{
                font-size: 2em;
            }}

            .english {{
                font-size: 1.2em;
            }}

            .button-group {{
                flex-direction: column;
            }}

            button {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Language Matrix</h1>
        <p class="subtitle">{lesson['title']} - {lesson.get('level', 'Beginner')}</p>

        <div class="dashboard">
            <h2>📊 Your Progress</h2>
            <div class="stat">
                <span class="stat-label">Lesson Progress</span>
                <span class="stat-value">{self.current_content_index + 1}/{len(lesson['content'])}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(self.current_content_index + 1) / len(lesson['content']) * 100}%"></div>
            </div>
            <div class="stat">
                <span class="stat-label">Accuracy</span>
                <span class="stat-value">87%</span>
            </div>
            <div class="stat">
                <span class="stat-label">Streak</span>
                <span class="stat-value">5 days 🔥</span>
            </div>
        </div>

        <div class="content" id="content-display">
            <div class="hangul" id="hangul">Loading...</div>
            <div class="english" id="english">Loading...</div>
            <div class="romanization" id="romanization">Loading...</div>
            <div class="explanation" id="explanation"></div>
        </div>

        <div class="exercise" id="exercise-display">
            <h2>🎯 Exercise</h2>
            <p id="exercise-question">Loading...</p>
            <div id="exercise-options"></div>
            <div class="answer-feedback" id="answer-feedback"></div>
        </div>

        <div class="button-group">
            <button class="btn-secondary" onclick="previousContent()">⬅️ Previous</button>
            <button class="btn-primary" onclick="nextContent()">Next ➡️</button>
        </div>

        <div class="footer">
            Language Matrix - Your Personal Korean Tutor
        </div>
    </div>

    <script>
        let currentContentIndex = {self.current_content_index};
        let currentExerciseIndex = 0;
        let selectedAnswer = '';

        const lessonData = {json.dumps(lesson)};

        function loadContent(index) {{
            if (index >= lessonData.content.length) return;

            const content = lessonData.content[index];
            document.getElementById('hangul').textContent = content.hangul;
            document.getElementById('english').textContent = content.english;
            document.getElementById('romanization').textContent = content.romanization;
            document.getElementById('explanation').innerHTML = `
                <strong>Explanation:</strong> ` + (content.phonological_explanation?.explanation || '') + `
                ` + (content.phonological_explanation?.changes?.length ? `<br><strong>Changes:</strong> ` + content.phonological_explanation.changes.join(', ') : '') + `
                ` + (content.phonological_explanation?.rules_applied?.length ? `<br><strong>Rules Applied:</strong> ` + content.phonological_explanation.rules_applied.join(', ') : '') + `
            `;

            document.querySelector('.stat-value').textContent = `${{index + 1}}/${{lessonData.content.length}}`;
            document.querySelector('.progress-fill').style.width = `${{(index + 1) / lessonData.content.length * 100}}%`;
        }}

        function loadExercise(index) {{
            if (index >= lessonData.exercises.length) return;

            const exercise = lessonData.exercises[index];
            document.getElementById('exercise-question').textContent = exercise.question;
            document.getElementById('exercise-options').innerHTML = exercise.options.map(option =>
                `<div class="option" onclick="selectOption(this, '${{option}}')">${{option}}</div>`
            ).join('');

            document.getElementById('answer-feedback').className = 'answer-feedback';
            document.getElementById('answer-feedback').textContent = '';
            selectedAnswer = '';
        }}

        function selectOption(element, answer) {{
            selectedAnswer = answer;
            document.querySelectorAll('.option').forEach(el => el.classList.remove('selected'));
            element.classList.add('selected');
        }}

        function submitAnswer() {{
            if (!selectedAnswer) {{
                alert('Please select an answer');
                return;
            }}

            const exercise = lessonData.exercises[currentExerciseIndex];
            const feedback = document.getElementById('answer-feedback');

            if (selectedAnswer === exercise.correct_answer) {{
                feedback.className = 'answer-feedback correct';
                feedback.textContent = '✅ Correct! Great job!';
            }} else {{
                feedback.className = 'answer-feedback incorrect';
                feedback.textContent = '❌ Incorrect. The correct answer is: ' + exercise.correct_answer;
            }}
        }}

        function nextContent() {{
            if (currentContentIndex < lessonData.content.length - 1) {{
                currentContentIndex++;
                loadContent(currentContentIndex);
            }}
        }}

        function previousContent() {{
            if (currentContentIndex > 0) {{
                currentContentIndex--;
                loadContent(currentContentIndex);
            }}
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            loadContent(currentContentIndex);
            loadExercise(currentExerciseIndex);
        }});
    </script>
</body>
</html>"""
