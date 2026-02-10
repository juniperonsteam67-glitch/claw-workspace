#!/usr/bin/env python3
"""
claw_evaluate.py - Self-Evaluation System for AI Outputs

A tool that critiques AI outputs before delivery, evaluating against
criteria like accuracy, completeness, clarity, and tone. Can auto-revise
based on critique feedback.

Usage:
    python claw_evaluate.py "proposed output" [--criteria accuracy,clarity] [--revise]
    python claw_evaluate.py --file proposal.txt [--criteria all] [--revise]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum
import textwrap


class Criterion(Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    TONE = "tone"


class EvaluationStatus(Enum):
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


@dataclass
class CriterionScore:
    name: str
    score: int  # 1-10
    feedback: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    original_text: str
    revised_text: Optional[str]
    status: EvaluationStatus
    overall_score: float
    criteria_scores: List[CriterionScore]
    summary: str
    iteration: int = 0
    max_iterations: int = 2


class SelfEvaluator:
    """Self-evaluation engine for critiquing AI outputs."""
    
    # Evaluation prompts/heuristics for each criterion
    CRITERIA_PROMPTS = {
        Criterion.ACCURACY: {
            "description": "Factual correctness and truthfulness",
            "checks": [
                "Are all facts, dates, numbers, and claims correct?",
                "Is there any misinformation or hallucination?",
                "Are technical details accurate?",
                "Would an expert agree with this content?"
            ]
        },
        Criterion.COMPLETENESS: {
            "description": "Coverage of all relevant information",
            "checks": [
                "Does it address all parts of the user's request?",
                "Are there missing steps, context, or details?",
                "Would the user need to ask follow-up questions?",
                "Are edge cases or alternatives mentioned?"
            ]
        },
        Criterion.CLARITY: {
            "description": "Understandability and structure",
            "checks": [
                "Is the language clear and unambiguous?",
                "Is the structure logical and easy to follow?",
                "Are technical terms explained appropriately?",
                "Would a non-expert understand this?"
            ]
        },
        Criterion.TONE: {
            "description": "Appropriateness for context and audience",
            "checks": [
                "Is the tone appropriate for the situation?",
                "Is it respectful and professional?",
                "Does it match the user's apparent emotional state?",
                "Is it neither too casual nor too formal?"
            ]
        }
    }
    
    def __init__(self, criteria: Optional[List[Criterion]] = None):
        self.criteria = criteria or list(Criterion)
        self.iteration = 0
        self.max_iterations = 2
    
    def evaluate(self, text: str, context: Optional[str] = None) -> EvaluationResult:
        """Evaluate the proposed output against all criteria."""
        self.iteration += 1
        
        scores = []
        for criterion in self.criteria:
            score = self._evaluate_criterion(text, criterion, context)
            scores.append(score)
        
        overall_score = sum(s.score for s in scores) / len(scores)
        
        # Determine status based on overall score and individual scores
        min_score = min(s.score for s in scores)
        if overall_score >= 8 and min_score >= 6:
            status = EvaluationStatus.APPROVED
        elif overall_score >= 5:
            status = EvaluationStatus.NEEDS_REVISION
        else:
            status = EvaluationStatus.REJECTED
        
        summary = self._generate_summary(text, scores, status, overall_score)
        
        return EvaluationResult(
            original_text=text,
            revised_text=None,
            status=status,
            overall_score=overall_score,
            criteria_scores=scores,
            summary=summary,
            iteration=self.iteration,
            max_iterations=self.max_iterations
        )
    
    def _evaluate_criterion(self, text: str, criterion: Criterion, 
                           context: Optional[str]) -> CriterionScore:
        """Evaluate text against a single criterion using heuristic analysis."""
        prompts = self.CRITERIA_PROMPTS[criterion]
        
        # Heuristic scoring based on text analysis
        score, feedback, suggestions = self._analyze_for_criterion(
            text, criterion, prompts
        )
        
        return CriterionScore(
            name=criterion.value,
            score=score,
            feedback=feedback,
            suggestions=suggestions
        )
    
    def _analyze_for_criterion(self, text: str, criterion: Criterion,
                               prompts: Dict) -> Tuple[int, str, List[str]]:
        """Analyze text and return score, feedback, and suggestions."""
        suggestions = []
        issues = []
        
        if criterion == Criterion.ACCURACY:
            return self._check_accuracy(text)
        elif criterion == Criterion.COMPLETENESS:
            return self._check_completeness(text)
        elif criterion == Criterion.CLARITY:
            return self._check_clarity(text)
        elif criterion == Criterion.TONE:
            return self._check_tone(text)
        
        return 7, "Analysis completed.", ["Review manually for best results."]
    
    def _check_accuracy(self, text: str) -> Tuple[int, str, List[str]]:
        """Check for potential accuracy issues."""
        issues = []
        suggestions = []
        score = 8  # Default assumption of good faith
        
        # Check for vague quantifiers (potential inaccuracy)
        vague_patterns = [
            (r'\b(many|most|some|few|several|various)\s+people\b', "vague quantification"),
            (r'\b(always|never|everyone|no one|all|none)\b', "absolute terms"),
            (r'\b(probably|maybe|likely|presumably)\b', "uncertain language"),
        ]
        
        for pattern, issue in vague_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append(f"Contains {issue}: {', '.join(set(matches[:3]))}")
                score -= 1
        
        # Check for unsupported claims
        claim_patterns = [
            r'\b(is|are|was|were)\s+(the\s+)?(best|worst|most|least|only)\b',
            r'\b(studies?\s+show|research\s+proves|science\s+says)\b',
        ]
        
        for pattern in claim_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Makes strong claims that may need citation")
                score -= 1
                suggestions.append("Add sources or soften strong claims")
        
        # Check for technical terms without context
        technical_pattern = r'\b(API|JSON|XML|REST|SDK|framework|library)\b'
        if re.search(technical_pattern, text) and "example" not in text.lower():
            suggestions.append("Consider adding examples for technical terms")
        
        if not issues:
            feedback = "No obvious accuracy concerns detected."
        else:
            feedback = f"Potential issues: {'; '.join(issues)}"
        
        return max(1, score), feedback, suggestions if suggestions else ["Verify all facts independently"]
    
    def _check_completeness(self, text: str) -> Tuple[int, str, List[str]]:
        """Check for completeness issues."""
        issues = []
        suggestions = []
        score = 7
        
        # Check for incomplete thoughts
        incomplete_patterns = [
            (r'\b(etc|and so on|and more)\b', "truncated list"),
            (r'\.{3,}$', "trailing ellipsis"),
            (r'\b(see below|as mentioned|refer to)\b', "reference without content"),
        ]
        
        for pattern, issue in incomplete_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(issue)
                score -= 1
        
        # Check for questions left unanswered
        question_pattern = r'\?'
        questions = re.findall(question_pattern, text)
        if len(questions) > 0 and "answer" not in text.lower():
            issues.append("contains questions without clear answers")
            suggestions.append("Ensure all questions raised are addressed")
        
        # Check length appropriateness
        word_count = len(text.split())
        if word_count < 20:
            score -= 2
            issues.append("very brief response")
            suggestions.append("Expand with more detail or context")
        
        # Check for actionable items without steps
        action_words = ['install', 'configure', 'set up', 'create', 'build']
        has_action = any(word in text.lower() for word in action_words)
        has_steps = re.search(r'\b(step|first|second|third|then|next|finally)\b', text, re.IGNORECASE)
        
        if has_action and not has_steps and word_count > 50:
            suggestions.append("Consider breaking instructions into numbered steps")
        
        if not issues:
            feedback = "Appears reasonably complete."
        else:
            feedback = f"Completeness concerns: {'; '.join(issues)}"
        
        return max(1, score), feedback, suggestions if suggestions else ["Review if all user questions are answered"]
    
    def _check_clarity(self, text: str) -> Tuple[int, str, List[str]]:
        """Check for clarity issues."""
        issues = []
        suggestions = []
        score = 8
        
        # Check sentence length
        sentences = re.split(r'[.!?]+', text)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if len(long_sentences) > 0:
            issues.append(f"{len(long_sentences)} very long sentences")
            score -= 1
            suggestions.append("Break long sentences into shorter ones")
        
        # Check paragraph length
        paragraphs = text.split('\n\n')
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]
        if len(long_paragraphs) > 0:
            issues.append(f"{len(long_paragraphs)} very long paragraphs")
            suggestions.append("Use shorter paragraphs for readability")
        
        # Check for jargon density
        jargon_words = ['utilize', 'leverage', 'synergy', 'paradigm', 'optimize', 
                       'facilitate', 'implement', 'configure']
        jargon_count = sum(1 for word in jargon_words if word in text.lower())
        if jargon_count > 3:
            issues.append("high jargon density")
            score -= 1
            suggestions.append("Replace jargon with simpler terms where possible")
        
        # Check for passive voice (simple heuristic)
        passive_patterns = [r'\b(is|are|was|were)\s+\w+ed\b', r'\b(has|have|had)\s+been\s+\w+ed\b']
        passive_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in passive_patterns)
        if passive_count > 3:
            suggestions.append("Consider using active voice for stronger clarity")
        
        # Check formatting
        if len(text) > 200 and '\n' not in text:
            issues.append("wall of text - no line breaks")
            score -= 1
            suggestions.append("Add line breaks and structure for readability")
        
        if not issues:
            feedback = "Generally clear and well-structured."
        else:
            feedback = f"Clarity issues: {'; '.join(issues)}"
        
        return max(1, score), feedback, suggestions if suggestions else ["Read aloud to check flow"]
    
    def _check_tone(self, text: str) -> Tuple[int, str, List[str]]:
        """Check for tone appropriateness."""
        issues = []
        suggestions = []
        score = 8
        
        # Check for overly casual language in formal context
        casual_patterns = [
            (r'\b(yeah|yep|nope|gonna|wanna|gotta)\b', "very casual"),
            (r'\b(lol|haha|omg|btw)\b', "internet slang"),
            (r'!{2,}', "excessive excitement"),
        ]
        
        for pattern, issue in casual_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"{issue} language detected")
                score -= 1
        
        # Check for overly formal/stiff language
        formal_words = ['herein', 'herewith', 'aforementioned', 'thusly', 'henceforth']
        formal_count = sum(1 for word in formal_words if word in text.lower())
        if formal_count > 0:
            issues.append("overly formal/archaic language")
            suggestions.append("Use more natural, conversational language")
        
        # Check for negative or dismissive tone
        negative_patterns = [
            (r'\b(obviously|clearly|simply)\b.*\?', "potentially condescending"),
            (r'\bjust\s+(do|use|try)\b', "minimizing effort"),
            (r'\b(should have|could have|why didn\'t you)\b', "judgmental"),
        ]
        
        for pattern, issue in negative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(issue)
                score -= 1
                suggestions.append("Rephrase to be more supportive and less judgmental")
        
        # Check for excessive apologies
        apology_count = len(re.findall(r'\b(sorry|apologize)\b', text, re.IGNORECASE))
        if apology_count > 1:
            issues.append("excessive apologizing")
            suggestions.append("One apology is sufficient; focus on solutions")
        
        # Check for ALL CAPS (shouting)
        caps_words = re.findall(r'\b[A-Z]{3,}\b', text)
        if len(caps_words) > 2:
            issues.append("excessive capitalization")
            suggestions.append("Use formatting (bold/italics) instead of caps for emphasis")
        
        if not issues:
            feedback = "Tone appears appropriate."
        else:
            feedback = f"Tone concerns: {'; '.join(issues)}"
        
        return max(1, score), feedback, suggestions if suggestions else ["Consider the user's emotional context"]
    
    def _generate_summary(self, text: str, scores: List[CriterionScore], 
                         status: EvaluationStatus, overall: float) -> str:
        """Generate an overall summary of the evaluation."""
        summaries = []
        
        if status == EvaluationStatus.APPROVED:
            summaries.append(f"✓ Output approved with score {overall:.1f}/10")
        elif status == EvaluationStatus.NEEDS_REVISION:
            summaries.append(f"⚠ Output needs revision (score {overall:.1f}/10)")
        else:
            summaries.append(f"✗ Output rejected (score {overall:.1f}/10)")
        
        # Add specific improvement areas
        low_scores = [s for s in scores if s.score < 6]
        if low_scores:
            areas = ", ".join(s.name for s in low_scores)
            summaries.append(f"Focus areas for improvement: {areas}")
        
        return " | ".join(summaries)
    
    def revise(self, text: str, evaluation: EvaluationResult) -> str:
        """Generate a revised version based on evaluation feedback."""
        revised = text
        
        # Apply improvements based on suggestions
        for score in evaluation.criteria_scores:
            for suggestion in score.suggestions:
                revised = self._apply_suggestion(revised, score.name, suggestion)
        
        return revised
    
    def _apply_suggestion(self, text: str, criterion: str, suggestion: str) -> str:
        """Apply a single suggestion to the text (simplified revision)."""
        # This is a simplified revision - in a real implementation,
        # this might use an LLM to actually rewrite based on feedback
        
        if "line breaks" in suggestion.lower():
            # Add paragraph breaks for long text
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if len(sentences) > 3:
                chunks = []
                for i in range(0, len(sentences), 3):
                    chunk = ' '.join(sentences[i:i+3])
                    chunks.append(chunk)
                return '\n\n'.join(chunks)
        
        if "shorter sentences" in suggestion.lower():
            # Break at conjunctions for very long sentences
            text = re.sub(r',\s+and\s+', '.\nAnd ', text, flags=re.IGNORECASE)
            text = re.sub(r',\s+but\s+', '.\nBut ', text, flags=re.IGNORECASE)
        
        if "active voice" in suggestion.lower():
            # Simple passive to active transformations
            text = re.sub(r'is\s+used\s+for', 'helps', text, flags=re.IGNORECASE)
            text = re.sub(r'was\s+created\s+by', 'created', text, flags=re.IGNORECASE)
        
        return text
    
    def evaluate_with_revision(self, text: str, max_iterations: int = 2,
                               context: Optional[str] = None) -> EvaluationResult:
        """Evaluate and optionally auto-revise the output."""
        self.max_iterations = max_iterations
        current_text = text
        
        for i in range(max_iterations + 1):
            result = self.evaluate(current_text, context)
            
            if result.status == EvaluationStatus.APPROVED:
                result.revised_text = current_text if i > 0 else None
                return result
            
            if i < max_iterations and result.status != EvaluationStatus.REJECTED:
                current_text = self.revise(current_text, result)
                result.revised_text = current_text
            else:
                result.revised_text = current_text if i > 0 else None
                return result
        
        return result


def format_output(result: EvaluationResult, verbose: bool = False, 
                  json_output: bool = False) -> str:
    """Format evaluation result for display."""
    
    if json_output:
        data = {
            "status": result.status.value,
            "overall_score": result.overall_score,
            "iteration": result.iteration,
            "max_iterations": result.max_iterations,
            "criteria": [
                {
                    "name": c.name,
                    "score": c.score,
                    "feedback": c.feedback,
                    "suggestions": c.suggestions
                }
                for c in result.criteria_scores
            ],
            "summary": result.summary,
            "original_text": result.original_text if verbose else None,
            "revised_text": result.revised_text
        }
        return json.dumps(data, indent=2)
    
    lines = []
    lines.append("=" * 60)
    lines.append("EVALUATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Status: {result.status.value.upper()}")
    lines.append(f"Overall Score: {result.overall_score:.1f}/10")
    lines.append(f"Iteration: {result.iteration}/{result.max_iterations}")
    lines.append("")
    
    # Criteria breakdown
    lines.append("-" * 60)
    lines.append("CRITERIA BREAKDOWN")
    lines.append("-" * 60)
    
    for score in result.criteria_scores:
        score_emoji = "✓" if score.score >= 7 else "⚠" if score.score >= 5 else "✗"
        lines.append(f"\n{score_emoji} {score.name.upper()}: {score.score}/10")
        lines.append(f"   {score.feedback}")
        if score.suggestions:
            lines.append("   Suggestions:")
            for sugg in score.suggestions:
                lines.append(f"     • {sugg}")
    
    lines.append("")
    lines.append("-" * 60)
    lines.append("SUMMARY")
    lines.append("-" * 60)
    lines.append(result.summary)
    
    if result.revised_text and result.revised_text != result.original_text:
        lines.append("")
        lines.append("-" * 60)
        lines.append("REVISED TEXT")
        lines.append("-" * 60)
        lines.append(result.revised_text)
    
    if verbose:
        lines.append("")
        lines.append("-" * 60)
        lines.append("ORIGINAL TEXT")
        lines.append("-" * 60)
        lines.append(result.original_text)
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def parse_criteria(criteria_str: str) -> List[Criterion]:
    """Parse criteria string into list of Criterion enums."""
    if criteria_str.lower() == "all":
        return list(Criterion)
    
    criteria_map = {c.value: c for c in Criterion}
    selected = []
    
    for item in criteria_str.split(','):
        item = item.strip().lower()
        if item in criteria_map:
            selected.append(criteria_map[item])
    
    return selected if selected else list(Criterion)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate AI outputs for quality before delivery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Your proposed response here"
  %(prog)s "Your response" --criteria accuracy,clarity
  %(prog)s "Your response" --revise
  %(prog)s --file proposal.txt --criteria all --revise --verbose
        """
    )
    
    parser.add_argument(
        'text',
        nargs='?',
        help='The proposed output text to evaluate'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='Read proposed output from file instead of command line'
    )
    
    parser.add_argument(
        '--criteria', '-c',
        default='all',
        help='Comma-separated criteria to evaluate (accuracy,completeness,clarity,tone,all)'
    )
    
    parser.add_argument(
        '--revise', '-r',
        action='store_true',
        help='Auto-revise based on critique (up to 2 iterations)'
    )
    
    parser.add_argument(
        '--max-iterations', '-m',
        type=int,
        default=2,
        help='Maximum revision iterations (default: 2)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Include original text in output'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output as JSON'
    )
    
    parser.add_argument(
        '--context',
        help='Additional context about the request or user'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=7.0,
        help='Minimum acceptable score (default: 7.0)'
    )
    
    args = parser.parse_args()
    
    # Get text from file or argument
    if args.file:
        try:
            with open(args.file, 'r') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        # Try reading from stdin
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)
    
    # Parse criteria
    criteria = parse_criteria(args.criteria)
    
    # Run evaluation
    evaluator = SelfEvaluator(criteria=criteria)
    
    if args.revise:
        result = evaluator.evaluate_with_revision(
            text, 
            max_iterations=args.max_iterations,
            context=args.context
        )
    else:
        result = evaluator.evaluate(text, context=args.context)
    
    # Output results
    output = format_output(result, verbose=args.verbose, json_output=args.json)
    print(output)
    
    # Exit with appropriate code
    if result.status == EvaluationStatus.APPROVED:
        sys.exit(0)
    elif result.status == EvaluationStatus.NEEDS_REVISION:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
