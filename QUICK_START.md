# Language Matrix - Quick Start Guide

## Getting Started

### Installation
No additional installation required. Python 3.8+ is needed.

### Basic Usage

#### 1. Run the Enhanced Application
```bash
python3 main_enhanced.py
```

This will launch the enhanced Language Matrix application with all new features.

#### 2. Generate Lessons
```bash
python3 -c "from language_matrix.enhanced_lesson_generator import EnhancedLessonGenerator; generator = EnhancedLessonGenerator(); generator.generate_all_lessons()"
```

#### 3. Run Enhanced Tests
```bash
python3 test_enhanced.py
```

#### 4. Run Original Tests
```bash
python3 -m pytest tests/ -v
```

## Feature Overview

### Enhanced Browser GUI
- **Content Display**: Shows Korean words, romanization, and English translations
- **Interactive Exercises**: Practice vocabulary with multiple-choice questions
- **Progress Tracking**: Real-time updates on your learning progress
- **Navigation**: Move between lesson content items
- **Dashboard**: View your overall progress and statistics

### Lesson Generator
- **Vocabulary Lessons**: Learn new Korean words and phrases
- **Grammar Lessons**: Understand Korean grammar structures
- **Cultural Lessons**: Learn about Korean culture and customs
- **Exercises**: Practice what you've learned
- **Save/Load**: Save lessons to JSON files for later use

### Teaching Methodology
- **Learning Sessions**: Structured learning sessions with teaching strategies
- **Study Recommendations**: Personalized recommendations based on your learning style
- **Assessments**: Evaluate your progress
- **Review Sessions**: Review previously learned material
- **Study Reminders**: Get reminded to practice

### Learning Analytics
- **Session Tracking**: Track your study sessions
- **Accuracy Monitoring**: Monitor your accuracy rates
- **Streak Tracking**: Build and maintain learning streaks
- **Learning Velocity**: Measure your learning speed
- **Comprehensive Reports**: View detailed analytics and insights

## Example Workflow

### 1. Generate Lessons
```python
from language_matrix.enhanced_lesson_generator import EnhancedLessonGenerator

generator = EnhancedLessonGenerator()
generator.generate_all_lessons()
```

### 2. Load a Lesson
```python
from language_matrix.enhanced_lesson_generator import EnhancedLessonGenerator

generator = EnhancedLessonGenerator()
lesson = generator.load_lesson("vocabulary_001")
```

### 3. Use the Enhanced GUI
```python
from language_matrix.enhanced_browser_gui import EnhancedBrowserGUI

gui = EnhancedBrowserGUI()
gui.load_lesson(lesson)

# Display content
content = gui.display_content()
print(content["content"]["english"])

# Submit answer
result = gui.submit_answer(0, "Hello")
print(f"Correct: {result['is_correct']}")

# Get progress
summary = gui.get_lesson_summary()
print(f"Accuracy: {summary['progress']['accuracy_rate']}%")
```

### 4. Track Analytics
```python
from language_matrix.learning_analytics import LearningAnalyticsTracker

tracker = LearningAnalyticsTracker("user123")

# Start session
tracker.start_session()

# Complete lesson
tracker.record_lesson_completion("lesson_001", accuracy_rate=0.8)

# End session
tracker.end_session()

# Get recommendations
recommendations = tracker.generate_recommendations()
print(recommendations)
```

## Lesson Structure

### Vocabulary Lesson
```json
{
  "id": "vocabulary_001",
  "title": "Basic Greetings",
  "level": "beginner",
  "type": "vocabulary",
  "duration_minutes": 15,
  "content": [
    {
      "id": "content_001",
      "english": "Hello",
      "hangul": "안녕하세요",
      "romanization": "an-nyeong-ha-se-yo",
      "explanation": "Standard greeting for formal situations"
    }
  ],
  "exercises": [
    {
      "type": "multiple_choice",
      "question": "What does '안녕하세요' mean?",
      "options": ["Goodbye", "Hello", "Thank you", "Sorry"],
      "correct_answer": "Hello"
    }
  ]
}
```

## Progress Tracking

### User Progress
- **Completion Status**: Lesson completion state (not_started, in_progress, completed)
- **Accuracy Rate**: Overall accuracy across exercises
- **Time Spent**: Total time spent on each lesson
- **Exercises Completed**: Number of exercises completed
- **Streak**: Current learning streak
- **Current Level**: Current proficiency level

### Analytics Data
- **Total Study Time**: Total time spent studying
- **Lessons Completed**: Number of completed lessons
- **Accuracy History**: Accuracy over time
- **Daily/Weekly Study Hours**: Study patterns
- **Learning Velocity**: Lessons learned per day
- **Retention Rate**: Knowledge retention percentage

## Tips for Success

1. **Consistent Practice**: Use the app daily to maintain streaks
2. **Review Regularly**: Use review sessions to reinforce learning
3. **Track Progress**: Monitor your analytics to identify areas for improvement
4. **Learn at Your Pace**: Adjust your learning speed based on your analytics
5. **Use Multiple Lesson Types**: Mix vocabulary, grammar, and culture lessons

## Troubleshooting

### Lessons Not Loading
- Check that the lesson file exists in the lessons directory
- Verify the JSON format is correct
- Ensure the lesson has all required fields

### Progress Not Saving
- Check file permissions
- Ensure the lessons directory exists
- Verify there's enough disk space

### Analytics Not Working
- Check that you're using the LearningAnalyticsTracker correctly
- Verify the analytics data structure matches expectations
- Ensure all required fields are populated

## Getting Help

For more information, see:
- `docs/ENHANCEMENT_PLAN.md` - Detailed enhancement plan
- `docs/PHASE1_ENHANCEMENTS.md` - Phase 1 feature documentation
- `language_matrix/` - Module documentation
- Test files - Usage examples

## Next Steps

1. Explore the enhanced features by running the main application
2. Generate some lessons to try out
3. Track your learning progress with analytics
4. Use teaching methodologies to optimize your learning
5. Review the enhancement roadmap for future features
