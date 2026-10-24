#!/usr/bin/env python3
"""Learning Analytics for Language Matrix"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class LearningAnalytics:
    """Comprehensive learning analytics data"""
    user_id: str
    total_study_time: int  # seconds
    lessons_completed: int
    total_exercises: int
    exercises_completed: int
    accuracy_rate: float
    current_streak: int
    longest_streak: int
    average_session_duration: int
    sessions_completed: int
    daily_study_hours: Dict[str, float]
    weekly_study_hours: Dict[str, float]
    learning_velocity: float
    retention_rate: float
    mastery_levels: Dict[str, int]  # lesson_id -> mastery level
    skill_assessment: Dict[str, Dict[str, Any]]
    goals_progress: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    last_updated: str


class LearningAnalyticsTracker:
    """Comprehensive learning analytics tracking system"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.analytics = LearningAnalytics(
            user_id=user_id,
            total_study_time=0,
            lessons_completed=0,
            total_exercises=0,
            exercises_completed=0,
            accuracy_rate=0.0,
            current_streak=0,
            longest_streak=0,
            average_session_duration=0,
            sessions_completed=0,
            daily_study_hours={},
            weekly_study_hours={},
            learning_velocity=0.0,
            retention_rate=0.0,
            mastery_levels={},
            skill_assessment={},
            goals_progress={},
            recommendations=[],
            last_updated=datetime.now().isoformat()
        )
        self.session_start_time = None
        self.current_session_exercises = 0

    def start_session(self):
        """Start a new learning session"""
        self.session_start_time = datetime.now()

    def end_session(self):
        """End current learning session and update analytics"""
        if self.session_start_time:
            session_duration = int((datetime.now() - self.session_start_time).total_seconds())
            self.analytics.total_study_time += session_duration
            self.analytics.sessions_completed += 1
            self.analytics.average_session_duration = int(
                self.analytics.total_study_time / self.analytics.sessions_completed
            )

            # Update daily and weekly study hours
            today = datetime.now().strftime("%Y-%m-%d")
            week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")

            self.analytics.daily_study_hours[today] = (
                self.analytics.daily_study_hours.get(today, 0) + session_duration / 3600
            )

            self.analytics.weekly_study_hours[week_start] = (
                self.analytics.weekly_study_hours.get(week_start, 0) + session_duration / 3600
            )

            # Update streak
            self._update_streak()
            self.session_start_time = None

    def record_lesson_completion(self, lesson_id: str, accuracy: float):
        """Record lesson completion with accuracy"""
        self.analytics.lessons_completed += 1
        self.analytics.total_exercises += 10  # Assume 10 exercises per lesson
        self.analytics.exercises_completed += 10

        # Update mastery level
        current_mastery = self.analytics.mastery_levels.get(lesson_id, 0)
        new_mastery = int(min(100, current_mastery + (accuracy / 100) * 20))
        self.analytics.mastery_levels[lesson_id] = new_mastery

        # Update accuracy rate
        self._update_accuracy_rate(accuracy)

    def record_exercise(self, is_correct: bool, difficulty: str):
        """Record individual exercise completion"""
        if is_correct:
            self.analytics.exercises_completed += 1

            # Update skill assessment
            if difficulty not in self.analytics.skill_assessment:
                self.analytics.skill_assessment[difficulty] = {"correct": 0, "total": 0}

            self.analytics.skill_assessment[difficulty]["correct"] += 1
            self.analytics.skill_assessment[difficulty]["total"] += 1

        self.analytics.total_exercises += 1

    def update_accuracy_rate(self, new_accuracy: float):
        """Update overall accuracy rate with weighted average"""
        current_count = self.analytics.exercises_completed - self.current_session_exercises
        if current_count == 0:
            current_count = 1

        old_accuracy = self.analytics.accuracy_rate
        self.analytics.accuracy_rate = (
            (old_accuracy * current_count + new_accuracy * 1) / (current_count + 1)
        )

    def _update_accuracy_rate(self, lesson_accuracy: float):
        """Update accuracy rate from lesson completion"""
        current_lessons = self.analytics.lessons_completed
        if current_lessons == 0:
            self.analytics.accuracy_rate = lesson_accuracy
        else:
            self.analytics.accuracy_rate = (
                (self.analytics.accuracy_rate * (current_lessons - 1) + lesson_accuracy) / current_lessons
            )

    def _update_streak(self):
        """Update learning streak"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if today in self.analytics.daily_study_hours:
            if yesterday in self.analytics.daily_study_hours:
                self.analytics.current_streak += 1
            else:
                self.analytics.current_streak = 1
        else:
            self.analytics.current_streak = 0

        if self.analytics.current_streak > self.analytics.longest_streak:
            self.analytics.longest_streak = self.analytics.current_streak

    def calculate_learning_velocity(self):
        """Calculate learning velocity (lessons per day)"""
        if not self.analytics.daily_study_hours:
            return 0.0

        total_hours = sum(self.analytics.daily_study_hours.values())
        days_active = len(self.analytics.daily_study_hours)
        return (self.analytics.lessons_completed / days_active) if days_active > 0 else 0.0

    def calculate_retention_rate(self):
        """Calculate retention rate based on mastery levels"""
        if not self.analytics.mastery_levels:
            return 0.0

        total_mastery = sum(self.analytics.mastery_levels.values())
        return (total_mastery / (len(self.analytics.mastery_levels) * 100)) * 100

    def update_goals_progress(self, goal_name: str, progress: float, status: str):
        """Update progress on learning goals"""
        if goal_name not in self.analytics.goals_progress:
            self.analytics.goals_progress[goal_name] = {
                "progress": 0.0,
                "status": "not_started",
                "target_date": ""
            }

        self.analytics.goals_progress[goal_name]["progress"] = min(100, progress)
        self.analytics.goals_progress[goal_name]["status"] = status

    def generate_recommendations(self) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []

        # Study time recommendations
        if self.analytics.average_session_duration < 10:
            recommendations.append("Try longer study sessions for better retention")
        if self.analytics.average_session_duration > 60:
            recommendations.append("Consider shorter, more frequent sessions")

        # Streak recommendations
        if self.analytics.current_streak < 3:
            recommendations.append("Build a consistent daily study routine")
        elif self.analytics.current_streak > 7:
            recommendations.append("Great streak! Keep it up!")

        # Accuracy recommendations
        if self.analytics.accuracy_rate < 60:
            recommendations.append("Focus on reviewing foundational concepts")
        elif self.analytics.accuracy_rate > 80:
            recommendations.append("Try more challenging content")

        # Mastery recommendations
        if self.analytics.mastery_levels:
            low_mastery = [lesson for lesson, mastery in self.analytics.mastery_levels.items() if mastery < 50]
            if low_mastery:
                recommendations.append(f"Review lessons with low mastery: {', '.join(low_mastery[:3])}")

        # Skill recommendations
        for skill, data in self.analytics.skill_assessment.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            if accuracy < 50:
                recommendations.append(f"Focus on improving {skill} skills")

        # Velocity recommendations
        velocity = self.calculate_learning_velocity()
        if velocity < 0.5:
            recommendations.append("Increase your study frequency")
        elif velocity > 1.0:
            recommendations.append("Consider setting more ambitious goals")

        return recommendations[:5]

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning analytics report"""
        self.analytics.learning_velocity = self.calculate_learning_velocity()
        self.analytics.retention_rate = self.calculate_retention_rate()
        self.analytics.recommendations = self.generate_recommendations()

        # Calculate weekly study hours
        weekly_hours = 0
        for week, hours in self.analytics.weekly_study_hours.items():
            weekly_hours += hours

        # Calculate daily average
        daily_avg = 0
        if self.analytics.daily_study_hours:
            daily_avg = sum(self.analytics.daily_study_hours.values()) / len(self.analytics.daily_study_hours)

        return {
            "user_id": self.user_id,
            "summary": {
                "total_study_time_hours": round(self.analytics.total_study_time / 3600, 2),
                "lessons_completed": self.analytics.lessons_completed,
                "accuracy_rate": f"{self.analytics.accuracy_rate:.1f}%",
                "current_streak": f"{self.analytics.current_streak} days",
                "longest_streak": f"{self.analytics.longest_streak} days",
                "weekly_study_hours": round(weekly_hours, 2),
                "daily_average_hours": round(daily_avg, 2),
                "learning_velocity": f"{self.analytics.learning_velocity:.2f} lessons/day",
                "retention_rate": f"{self.analytics.retention_rate:.1f}%"
            },
            "breakdown": {
                "daily_study_hours": self.analytics.daily_study_hours,
                "weekly_study_hours": self.analytics.weekly_study_hours,
                "mastery_levels": self.analytics.mastery_levels,
                "skill_assessment": self.analytics.skill_assessment,
                "goals_progress": self.analytics.goals_progress
            },
            "insights": self._generate_insights(),
            "recommendations": self.analytics.recommendations,
            "last_updated": self.analytics.last_updated
        }

    def _generate_insights(self) -> List[str]:
        """Generate learning insights based on analytics"""
        insights = []

        # Study consistency
        if len(self.analytics.daily_study_hours) >= 3:
            insights.append("Great! You're building consistent study habits")

        # Progress tracking
        if self.analytics.lessons_completed >= 5:
            insights.append(f"You've completed {self.analytics.lessons_completed} lessons - impressive progress!")

        # Retention analysis
        if self.analytics.retention_rate > 70:
            insights.append("Excellent retention rate! You're building strong knowledge foundations")

        # Streak analysis
        if self.analytics.current_streak >= 7:
            insights.append("Your 7-day streak shows excellent commitment to learning")

        return insights

    def save_to_file(self, filepath: str = "analytics/user_analytics.json"):
        """Save analytics to JSON file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_comprehensive_report(), f, indent=2, ensure_ascii=False)

        return {"success": True, "filepath": filepath}

    def load_from_file(self, filepath: str = "analytics/user_analytics.json"):
        """Load analytics from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert summary data to match LearningAnalytics expected fields
            summary = data["summary"]
            analytics_data = {
                "user_id": self.user_id,
                "total_study_time": int(float(summary.get("total_study_time_hours", 0)) * 3600),
                "lessons_completed": summary.get("lessons_completed", 0),
                "total_exercises": 0,
                "exercises_completed": 0,
                "accuracy_rate": float(summary.get("accuracy_rate", 0).replace('%', '')) / 100 if isinstance(summary.get("accuracy_rate"), str) else summary.get("accuracy_rate", 0),
                "current_streak": int(summary.get("current_streak", 0).replace(' days', '').replace(' day', '')),
                "longest_streak": int(summary.get("longest_streak", 0).replace(' days', '').replace(' day', '')),
                "average_session_duration": 0,
                "sessions_completed": 0,
                "daily_study_hours": data["breakdown"]["daily_study_hours"],
                "weekly_study_hours": data["breakdown"]["weekly_study_hours"],
                "learning_velocity": float(summary.get("learning_velocity", 0).replace(' lessons/day', '')),
                "retention_rate": float(summary.get("retention_rate", 0).replace('%', '')) / 100 if isinstance(summary.get("retention_rate"), str) else summary.get("retention_rate", 0),
                "mastery_levels": data["breakdown"]["mastery_levels"],
                "skill_assessment": data["breakdown"]["skill_assessment"],
                "goals_progress": data["breakdown"]["goals_progress"],
                "recommendations": data["recommendations"],
                "last_updated": data["last_updated"]
            }

            self.analytics = LearningAnalytics(**analytics_data)
            self.analytics.daily_study_hours = data["breakdown"]["daily_study_hours"]
            self.analytics.weekly_study_hours = data["breakdown"]["weekly_study_hours"]
            self.analytics.mastery_levels = data["breakdown"]["mastery_levels"]
            self.analytics.skill_assessment = data["breakdown"]["skill_assessment"]
            self.analytics.goals_progress = data["breakdown"]["goals_progress"]
            self.analytics.recommendations = data["recommendations"]
            self.analytics.last_updated = data["last_updated"]

            return {"success": True}

        except FileNotFoundError:
            return {"success": False, "error": "Analytics file not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_progress_chart_data(self) -> Dict[str, Any]:
        """Get data for progress chart visualization"""
        return {
            "daily_study": list(self.analytics.daily_study_hours.values()),
            "weekly_study": list(self.analytics.weekly_study_hours.values()),
            "mastery_levels": self.analytics.mastery_levels,
            "accuracy_history": self._calculate_accuracy_history()
        }

    def _calculate_accuracy_history(self) -> List[float]:
        """Calculate accuracy history over time"""
        history = []
        for lesson_id, mastery in self.analytics.mastery_levels.items():
            if mastery > 0:
                history.append(mastery)
        return history

    def get_study_schedule_recommendations(self) -> Dict[str, Any]:
        """Get personalized study schedule recommendations"""
        recommendations = {
            "optimal_study_time": 30,
            "recommended_days": ["Monday", "Wednesday", "Friday"],
            "recommended_time": "morning",
            "study_duration": 25,
            "break_duration": 5
        }

        # Adjust recommendations based on analytics
        if self.analytics.current_streak > 7:
            recommendations["study_duration"] = 30
            recommendations["break_duration"] = 10

        if self.analytics.learning_velocity < 0.3:
            recommendations["recommended_days"] = ["Every day"]

        return recommendations
