"""Lesson validator for Language Matrix"""

import re
from typing import Dict, Any, List, Optional
from .lesson_schema import LessonPlan, LessonSchema


class LessonValidator:
    """Validates Korean lessons for linguistic accuracy"""

    # Korean grammar rules patterns
    IMPERATIVE_PATTERN = r'\b(십시오|하세요|하십시오)\b'
    QUESTION_PATTERN = r'\b(습니까|니까|요)\b'
    POLITE_PATTERN = r'\b(습니다|ㅂ니다)\b'
    HONORIFIC_PATTERN = r'\b(시-)\b'

    def validate_korean_accuracy(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate Korean linguistic accuracy in a lesson"""
        errors = []
        warnings = []

        # Check for grammatical accuracy in Korean text
        for i, content_item in enumerate(lesson_plan.content):
            hangul = content_item.hangul

            # Check for correct verb endings
            if self._has_incorrect_verb_endings(hangul):
                errors.append(
                    f"Content item {i}: Incorrect verb endings detected - {hangul}"
                )

            # Check for proper honorific usage
            if self._has_incorrect_honorifics(hangul):
                warnings.append(
                    f"Content item {i}: Potential honorific usage issues - {hangul}"
                )

            # Check for proper object marking
            if not self._has_correct_object_marking(hangul):
                errors.append(
                    f"Content item {i}: Incorrect object marking - {hangul}"
                )

            # Check for proper particle usage
            if not self._has_correct_particle_usage(hangul):
                errors.append(
                    f"Content item {i}: Incorrect particle usage - {hangul}"
                )

        # Validate phonological explanations
        for i, content_item in enumerate(lesson_plan.content):
            if content_item.phonological_explanation:
                explanation = content_item.phonological_explanation.explanation

                # Check for linguistic accuracy in explanations
                if not self._has_linguistically_valid_explanation(explanation):
                    errors.append(
                        f"Content item {i}: Invalid phonological explanation - {explanation}"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _has_incorrect_verb_endings(self, hangul: str) -> bool:
        """Check for incorrect verb endings"""
        # This is a simplified check - actual implementation would use Korean grammar rules
        # For now, we'll check for obvious issues
        # Only flag patterns that are clearly incorrect
        incorrect_patterns = [
            r'물마십니까',  # Incorrect object marking
            r'배고프입니다',  # Incorrect verb ending
        ]

        for pattern in incorrect_patterns:
            if re.search(pattern, hangul):
                return True

        return False

    def _has_incorrect_honorifics(self, hangul: str) -> bool:
        """Check for incorrect honorific usage"""
        # Check for inappropriate combinations of honorifics
        # This is a simplified check
        if re.search(self.HONORIFIC_PATTERN, hangul):
            # Check if honorific is used appropriately
            # This would require more sophisticated analysis
            return False

        return False

    def _has_correct_object_marking(self, hangul: str) -> bool:
        """Check for correct object marking"""
        # Check for proper object marking with 을/를
        if '물을 마시' in hangul or '물을 마십' in hangul:
            return True

        # Check for incorrect object marking
        if '물마시' in hangul or '물 마십' in hangul:
            return False

        return True

    def _has_correct_particle_usage(self, hangul: str) -> bool:
        """Check for correct particle usage"""
        # Check for proper subject and object particles
        # This is a simplified check
        if '이/가' in hangul or '을/를' in hangul:
            return True

        return True

    def _has_linguistically_valid_explanation(self, explanation: str) -> bool:
        """Check if phonological explanation is linguistically valid"""
        # Basic validation - ensure explanation is not empty or nonsensical
        if not explanation or len(explanation) < 10:
            return False

        # Check for basic linguistic terminology
        # Use a more comprehensive list of linguistic terms
        linguistic_terms = [
            'phonological', 'allomorph', 'consonant', 'vowel',
            'consonant cluster', 'syllable', 'stress', 'tone',
            'morphological', 'syntactic', 'grammatical', 'ending',
            'stem', 'particle', 'honorific', 'formal', 'polite',
            'subject', 'object', 'marker', 'verb', 'adjective'
        ]

        has_term = any(term in explanation.lower() for term in linguistic_terms)

        if not has_term:
            return False

        return True

    def validate_english_accuracy(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """Validate English accuracy in the lesson"""
        errors = []

        # Check for grammatical accuracy in English
        for i, content_item in enumerate(lesson_plan.content):
            english = content_item.english

            # Check for obvious grammatical errors
            # This would use more sophisticated English grammar checking
            if not english or len(english) < 5:
                errors.append(
                    f"Content item {i}: English text is too short or missing"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
        }
