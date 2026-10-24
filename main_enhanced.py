#!/usr/bin/env python3
"""Enhanced Language Matrix Application with Full-Featured Interface"""

import sys
import json
from typing import Dict, Any, List
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from language_matrix.enhanced_lesson_generator import EnhancedLessonGenerator, EnhancedLesson
from language_matrix.enhanced_browser_gui import EnhancedBrowserGUI, UserProgress
from language_matrix.teaching_methodology import TeachingMethodology, LearningSession
from language_matrix.learning_analytics import LearningAnalyticsTracker


class LanguageMatrixApp:
    """Main application for Language Matrix with enhanced features"""

    def __init__(self):
        self.lesson_generator = EnhancedLessonGenerator()
        self.browser_gui = EnhancedBrowserGUI()
        self.teaching_methodology = TeachingMethodology()
        self.analytics = LearningAnalyticsTracker("user_001")
        self.current_lesson = None
        self.current_session = None

        # Load existing lessons
        self.lessons = self.lesson_generator.load_lessons()

        # Load user progress
        self.user_progress = self._load_user_progress()

        # Load analytics
        self.analytics.load_from_file()

    def _load_user_progress(self) -> Dict[str, UserProgress]:
        """Load user progress from file"""
        try:
            with open("user_progress.json", 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                return {
                    lesson_id: UserProgress(**progress_data)
                    for lesson_id, progress_data in progress_data['user_progress'].items()
                }
        except FileNotFoundError:
            return {}

    def _save_user_progress(self):
        """Save user progress to file"""
        self.browser_gui.save_progress()

    def create_sample_lessons(self):
        """Create sample lessons for demonstration"""
        sample_lessons = []

        # Create beginner vocabulary lesson
        vocab_lesson = self.lesson_generator.create_beginner_vocabulary_lesson(
            "Korean Basics - Greetings",
            "beginner"
        )
        sample_lessons.append(vocab_lesson)

        # Create intermediate grammar lesson
        grammar_lesson = self.lesson_generator.create_intermediate_grammar_lesson(
            "Korean Grammar - Intermediate",
            "intermediate"
        )
        sample_lessons.append(grammar_lesson)

        # Create cultural context lesson
        culture_lesson = self.lesson_generator.create_cultural_context_lesson(
            "Korean Culture - Social Etiquette",
            "beginner"
        )
        sample_lessons.append(culture_lesson)

        # Save all lessons
        for lesson in sample_lessons:
            self.lesson_generator.save_lesson(lesson)

        # Update loaded lessons
        self.lessons = self.lesson_generator.load_lessons()

        return sample_lessons

    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("LANGUAGE MATRIX - Enhanced Learning Platform")
        print("="*60)
        print("\n📚 Main Menu")
        print("="*60)
        print("1. Browse Lessons")
        print("2. Start New Lesson")
        print("3. Continue Previous Lesson")
        print("4. View Progress Dashboard")
        print("5. Learning Analytics")
        print("6. Study Recommendations")
        print("7. Teaching Methodology")
        print("8. Exit")
        print("="*60)

    def browse_lessons(self):
        """Display and select from available lessons"""
        print("\n📚 Available Lessons")
        print("="*60)

        if not self.lessons:
            print("No lessons available. Creating sample lessons...")
            self.create_sample_lessons()

        for i, lesson in enumerate(self.lessons, 1):
            progress = self.user_progress.get(lesson['id'], UserProgress(
                lesson_id=lesson['id'],
                completion_status="not_started",
                last_accessed="",
                accuracy_rate=0.0,
                time_spent=0,
                exercises_completed=0,
                total_exercises=len(lesson.get('exercises', [])),
                streak=0,
                current_level=1
            ))

            status_icon = "✅" if progress.completion_status == "completed" else "🔄" if progress.completion_status == "in_progress" else "📝"
            print(f"\n{i}. {status_icon} {lesson['title']}")
            print(f"   Level: {lesson['level']} | Type: {lesson['type']}")
            print(f"   Duration: {lesson['duration_minutes']} minutes | Exercises: {len(lesson['exercises'])}")
            print(f"   Progress: {progress.accuracy_rate}% | Streak: {progress.streak} days")

        print("\n" + "="*60)

    def start_lesson(self, lesson_index: int):
        """Start a specific lesson"""
        if lesson_index < 1 or lesson_index > len(self.lessons):
            print("Invalid lesson selection")
            return

        lesson = self.lessons[lesson_index - 1]
        self.current_lesson = lesson

        # Load lesson into browser GUI
        self.browser_gui.load_lesson(lesson)

        # Create teaching session
        self.current_session = self.teaching_methodology.create_learning_session(
            lesson,
            self.user_progress.get(lesson['id'])
        )

        # Start analytics session
        self.analytics.start_session()

        print(f"\n✨ Starting: {lesson['title']}")
        print(f"📊 Strategy: {self.current_session.strategy.value}")
        print(f"🎯 Learning Style: {self.current_session.learning_style.value}")
        print(f"⏱️  Duration: {self.current_session.estimated_duration} minutes")
        print(f"🎯 Focus Areas: {', '.join(self.current_session.focus_areas)}")
        print("="*60)

        # Display initial content
        self.display_content()

    def display_content(self):
        """Display current lesson content"""
        content = self.browser_gui.display_content()

        print(f"\n📖 Content {content['progress']['current']}/{content['progress']['total']}")
        print("="*60)

        display_content = content['content']
        print(f"\n🇰🇷 {display_content['hangul']}")
        print(f"🔤 {display_content['romanization']}")
        print(f"📝 {display_content['english']}")

        if display_content['phonological_explanation']:
            explanation = display_content['phonological_explanation']
            print(f"\n💡 {explanation['explanation']}")
            if explanation['changes']:
                print(f"🔄 Changes: {', '.join(explanation['changes'])}")
            if explanation['rules_applied']:
                print(f"📊 Rules Applied: {', '.join(explanation['rules_applied'])}")

        print("\n" + "="*60)

    def display_exercises(self):
        """Display current exercises"""
        if not self.current_lesson or not self.current_lesson['exercises']:
            print("No exercises available")
            return

        exercise = self.current_lesson['exercises'][0]
        print(f"\n🎯 Exercise {len(self.current_lesson['exercises'])}")
        print("="*60)
        print(f"\n❓ {exercise['question']}")
        print("\nOptions:")
        for i, option in enumerate(exercise['options'], 1):
            print(f"{i}. {option}")
        print("="*60)

    def submit_answer(self, answer: str):
        """Submit answer to current exercise"""
        if not self.current_lesson:
            print("No lesson loaded")
            return

        result = self.browser_gui.submit_answer(0, answer)
        self.analytics.record_exercise(result['is_correct'], self.current_lesson.get('level', 'beginner'))

        if result['is_correct']:
            print(f"\n✅ {result['feedback']}")
        else:
            print(f"\n❌ {result['feedback']}")
            print(f"📝 Correct Answer: {result['correct_answer']}")

        if result['explanation']:
            print(f"💡 {result['explanation']}")

        print("="*60)

    def next_content(self):
        """Move to next content"""
        result = self.browser_gui.next_content()

        if result.get('lesson_completed'):
            print("\n🎉 Lesson Completed!")
            self.browser_gui.complete_lesson()
            self.analytics.record_lesson_completion(self.current_lesson['id'], 85)  # Assume 85% accuracy
            self.analytics.end_session()
            self._save_user_progress()
            self._save_analytics()
            return

        if 'error' in result and result['error'] == 'End of content':
            print("\n🎉 Lesson Completed!")
            self.browser_gui.complete_lesson()
            self.analytics.record_lesson_completion(self.current_lesson['id'], 85)
            self.analytics.end_session()
            self._save_user_progress()
            self._save_analytics()
            return

        self.display_content()

    def previous_content(self):
        """Move to previous content"""
        result = self.browser_gui.previous_content()

        if result.get('error') == 'Beginning of content':
            print("Already at the beginning of content")
            return

        self.display_content()

    def view_progress_dashboard(self):
        """Display comprehensive progress dashboard"""
        print("\n📊 Progress Dashboard")
        print("="*60)

        lesson_summary = self.browser_gui.get_lesson_summary()
        progress = lesson_summary['progress']

        print(f"\n📈 Lesson Progress")
        print(f"   Completion Status: {progress['completion_status'].replace('_', ' ').title()}")
        print(f"   Accuracy Rate: {progress['accuracy_rate']}%")
        print(f"   Time Spent: {progress['time_spent']} seconds")
        print(f"   Exercises Completed: {progress['exercises_completed']}/{progress['total_exercises']}")
        print(f"   Current Streak: {progress['streak']} days 🔥")
        print(f"   Current Level: {progress['current_level']}")

        print(f"\n🎯 Learning Goals")
        for goal, goal_data in lesson_summary['lesson'].get('learning_objectives', []).items():
            print(f"   • {goal}")

        print("="*60)

    def view_analytics(self):
        """Display learning analytics"""
        print("\n📈 Learning Analytics")
        print("="*60)

        report = self.analytics.get_comprehensive_report()

        print(f"\n📊 Summary")
        print(f"   Total Study Time: {report['summary']['total_study_time_hours']} hours")
        print(f"   Lessons Completed: {report['summary']['lessons_completed']}")
        print(f"   Accuracy Rate: {report['summary']['accuracy_rate']}")
        print(f"   Current Streak: {report['summary']['current_streak']}")
        print(f"   Weekly Study Hours: {report['summary']['weekly_study_hours']}")
        print(f"   Learning Velocity: {report['summary']['learning_velocity']}")
        print(f"   Retention Rate: {report['summary']['retention_rate']}")

        print(f"\n💡 Insights")
        for insight in report['insights']:
            print(f"   • {insight}")

        print(f"\n🎯 Recommendations")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"   {i}. {recommendation}")

        print("="*60)

    def view_study_recommendations(self):
        """Display study recommendations"""
        print("\n🎯 Study Recommendations")
        print("="*60)

        recommendations = self.teaching_methodology.get_study_recommendations({
            "learning_pace": "moderate",
            "learning_goals": ["fluency", "business"]
        })

        print(f"\n⏰ Study Schedule")
        print(f"   Optimal Study Time: {recommendations['daily_study_time']} minutes/day")
        print(f"   Recommended Frequency: {recommendations['session_frequency']}")
        print(f"   Recommended Time: {recommendations['recommended_time']}")

        print(f"\n📚 Suggested Activities")
        for i, activity in enumerate(recommendations['suggested_activities'], 1):
            print(f"   {i}. {activity}")

        print(f"\n🎯 Progress Milestones")
        for milestone in recommendations['progress_milestones']:
            print(f"   • {milestone}")

        print("="*60)

    def view_teaching_methodology(self):
        """Display teaching methodology information"""
        print("\n🎓 Teaching Methodology")
        print("="*60)

        print(f"\n📚 Learning Strategies")
        print(f"   Immersion - Full language context")
        print(f"   Scaffolding - Step-by-step learning")
        print(f"   Repetition - Spaced repetition systems")
        print(f"   Contextual - Real-world scenarios")
        print(f"   Interactive - Engaging exercises")
        print(f"   Reflection - Self-assessment")

        print(f"\n🎯 Learning Styles")
        print(f"   Visual - Learning through visuals")
        print(f"   Auditory - Learning through listening")
        print(f"   Kinesthetic - Learning through doing")
        print(f"   Reading - Learning through text")
        print(f"   Verbal - Learning through speaking")

        print(f"\n📊 Session Types")
        print(f"   Practice - Reinforcing learning")
        print(f"   Review - Consolidating knowledge")
        print(f"   Assessment - Testing understanding")
        print(f"   Extension - Going beyond basics")

        print("="*60)

    def generate_lesson(self):
        """Generate a new lesson"""
        print("\n✨ Lesson Generator")
        print("="*60)

        print("\n1. Beginner Vocabulary")
        print("2. Intermediate Grammar")
        print("3. Cultural Context")
        print("4. Custom Lesson")

        choice = input("\nSelect lesson type (1-4): ").strip()

        if choice == "1":
            title = input("Enter lesson title (default: Korean Basics): ") or "Korean Basics"
            lesson = self.lesson_generator.create_beginner_vocabulary_lesson(title, "beginner")
        elif choice == "2":
            title = input("Enter lesson title (default: Korean Grammar): ") or "Korean Grammar"
            lesson = self.lesson_generator.create_intermediate_grammar_lesson(title, "intermediate")
        elif choice == "3":
            title = input("Enter lesson title (default: Korean Culture): ") or "Korean Culture"
            lesson = self.lesson_generator.create_cultural_context_lesson(title, "beginner")
        elif choice == "4":
            print("Custom lesson generation coming soon!")
            return
        else:
            print("Invalid choice")
            return

        self.lesson_generator.save_lesson(lesson)
        self.lessons = self.lesson_generator.load_lessons()

        print(f"\n✅ Lesson created: {lesson['title']}")
        print(f"   Level: {lesson['level']}")
        print(f"   Type: {lesson['type']}")
        print(f"   Duration: {lesson['duration_minutes']} minutes")
        print(f"   Exercises: {len(lesson['exercises'])}")

        print("="*60)

    def display_html(self):
        """Display enhanced HTML interface"""
        if not self.current_lesson:
            print("No lesson loaded. Start a lesson first.")
            return

        html = self.browser_gui.get_html()
        print("\n" + "="*60)
        print("🌐 Enhanced Browser Interface")
        print("="*60)
        print("\nAn enhanced browser interface has been generated.")
        print("To view it, you can:")
        print("1. Save the HTML to a file and open in a browser")
        print("2. Or use the browser_gui.get_html() method")
        print("\nKey Features:")
        print("• Modern gradient design")
        print("• Progress tracking")
        print("• Interactive exercises")
        print("• Real-time feedback")
        print("• Responsive layout")
        print("="*60)

    def _save_analytics(self):
        """Save analytics to file"""
        self.analytics.save_to_file()

    def run(self):
        """Main application loop"""
        print("\n🚀 Language Matrix Enhanced Application")
        print("Starting with enhanced features...")
        print("="*60)

        # Create sample lessons if none exist
        if not self.lessons:
            self.create_sample_lessons()

        while True:
            self.display_menu()

            try:
                choice = input("\nSelect option (1-8): ").strip()

                if choice == "1":
                    self.browse_lessons()
                elif choice == "2":
                    self.browse_lessons()
                    lesson_index = int(input("Select lesson (1-{}): ".format(len(self.lessons)))) - 1
                    self.start_lesson(lesson_index)
                elif choice == "3":
                    # Continue previous lesson
                    completed_lessons = [l for l in self.lessons if self.user_progress.get(l['id'], {}).get('completion_status') == 'completed']
                    if completed_lessons:
                        print("\n✅ Completed Lessons:")
                        for i, lesson in enumerate(completed_lessons, 1):
                            print(f"{i}. {lesson['title']}")
                        choice = int(input("Select lesson to continue (1-{}): ".format(len(completed_lessons))))
                        self.start_lesson(choice)
                    else:
                        print("\nNo completed lessons to continue")
                elif choice == "4":
                    self.view_progress_dashboard()
                elif choice == "5":
                    self.view_analytics()
                elif choice == "6":
                    self.view_study_recommendations()
                elif choice == "7":
                    self.view_teaching_methodology()
                elif choice == "8":
                    print("\n🎉 Thank you for using Language Matrix!")
                    print("="*60)
                    break
                else:
                    print("\n❌ Invalid option. Please try again.")

            except ValueError:
                print("\n❌ Invalid input. Please enter a number.")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")


def main():
    """Main entry point"""
    try:
        app = LanguageMatrixApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("="*60)


if __name__ == "__main__":
    main()
