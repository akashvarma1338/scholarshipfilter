"""
Rules Engine for Scholarship Eligibility Filter
This module handles the core logic of evaluating student eligibility
based on dynamic rules stored in the database.
"""

import json


class RulesEngine:
    """
    The RulesEngine class evaluates student eligibility against scholarship rules.
    It supports:
    - Multiple scholarship evaluation
    - Detailed rejection reasons
    - Priority scoring based on marks and income
    """
    
    def __init__(self):
        """Initialize the rules engine"""
        pass
    
    def evaluate_rule(self, student, rule):
        """
        Evaluate a single rule against a student's data.
        
        Args:
            student: Student object with attributes
            rule: Rule object with field, operator, and value
            
        Returns:
            tuple: (passed: bool, error_message: str or None)
        """
        # Get the student's value for the field being checked
        student_value = getattr(student, rule.field, None)
        
        if student_value is None:
            return False, f"Unknown field: {rule.field}"
        
        # Parse the rule value based on the field type
        rule_value = self._parse_value(rule.field, rule.value)
        
        # Evaluate based on operator
        try:
            if rule.operator == '>=':
                passed = student_value >= rule_value
            elif rule.operator == '<=':
                passed = student_value <= rule_value
            elif rule.operator == '>':
                passed = student_value > rule_value
            elif rule.operator == '<':
                passed = student_value < rule_value
            elif rule.operator == '==':
                passed = student_value == rule_value
            elif rule.operator == '!=':
                passed = student_value != rule_value
            elif rule.operator == 'in':
                # For category checks - value is comma-separated list
                allowed_values = [v.strip().lower() for v in rule.value.split(',')]
                passed = str(student_value).lower() in allowed_values
            else:
                return False, f"Unknown operator: {rule.operator}"
            
            # Return result with error message if failed
            if passed:
                return True, None
            else:
                return False, rule.error_message or f"{rule.description} - Failed"
                
        except Exception as e:
            return False, f"Error evaluating rule: {str(e)}"
    
    def _parse_value(self, field, value):
        """
        Parse the rule value to the appropriate type based on the field.
        
        Args:
            field: The field name being checked
            value: The string value from the rule
            
        Returns:
            Parsed value in appropriate type
        """
        # Boolean fields
        if field in ['has_backlogs', 'is_full_time']:
            return value.lower() in ['true', '1', 'yes']
        
        # Numeric fields
        if field in ['marks_percentage', 'family_income', 'year_of_study']:
            return float(value)
        
        # String fields (category, course, etc.)
        return value
    
    def check_eligibility(self, student, scholarship):
        """
        Check if a student is eligible for a specific scholarship.
        
        Args:
            student: Student object
            scholarship: Scholarship object with rules
            
        Returns:
            dict: {
                'eligible': bool,
                'scholarship_name': str,
                'scholarship_amount': float,
                'rejection_reasons': list,
                'priority_score': float
            }
        """
        rejection_reasons = []
        all_passed = True
        
        # Evaluate each rule for this scholarship
        for rule in scholarship.rules:
            passed, error_message = self.evaluate_rule(student, rule)
            
            if not passed:
                all_passed = False
                if error_message:
                    rejection_reasons.append(error_message)
        
        # Calculate priority score only if eligible
        priority_score = 0.0
        if all_passed:
            priority_score = self.calculate_priority_score(student, scholarship)
        
        return {
            'eligible': all_passed,
            'scholarship_id': scholarship.id,
            'scholarship_name': scholarship.name,
            'scholarship_amount': scholarship.amount,
            'scholarship_description': scholarship.description,
            'rejection_reasons': rejection_reasons,
            'priority_score': round(priority_score, 2)
        }
    
    def calculate_priority_score(self, student, scholarship):
        """
        Calculate a priority score for ranking eligible students.
        
        Scoring Criteria:
        - Higher marks = Higher score (max 50 points)
        - Lower family income = Higher score (max 50 points)
        
        Args:
            student: Student object
            scholarship: Scholarship object
            
        Returns:
            float: Priority score (0-100 scale)
        """
        score = 0.0
        
        # Marks contribution (0-50 points)
        # Linear scaling: 60% = 0 points, 100% = 50 points
        marks_score = max(0, (student.marks_percentage - 60) / 40 * 50)
        score += marks_score
        
        # Income contribution (0-50 points)
        # Lower income = higher score
        # Income of 0 = 50 points, Income of 500000 = 0 points
        max_income = 500000  # Maximum income for scoring
        income_score = max(0, (max_income - student.family_income) / max_income * 50)
        score += income_score
        
        # Bonus points for specific categories (optional)
        category_bonus = {
            'SC': 5,
            'ST': 5,
            'OBC': 3,
            'EWS': 4,
            'General': 0
        }
        score += category_bonus.get(student.category, 0)
        
        return min(score, 105)  # Cap at 105 (100 base + 5 bonus)
    
    def check_all_scholarships(self, student, scholarships):
        """
        Check a student's eligibility for all available scholarships.
        
        Args:
            student: Student object
            scholarships: List of Scholarship objects
            
        Returns:
            dict: {
                'student': dict,
                'eligible_scholarships': list,
                'ineligible_scholarships': list,
                'total_eligible_amount': float
            }
        """
        eligible_scholarships = []
        ineligible_scholarships = []
        total_eligible_amount = 0.0
        
        for scholarship in scholarships:
            if not scholarship.is_active:
                continue
                
            result = self.check_eligibility(student, scholarship)
            
            if result['eligible']:
                eligible_scholarships.append(result)
                total_eligible_amount += result['scholarship_amount']
            else:
                ineligible_scholarships.append(result)
        
        # Sort eligible scholarships by priority score (descending)
        eligible_scholarships.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'student': student.to_dict(),
            'eligible_scholarships': eligible_scholarships,
            'ineligible_scholarships': ineligible_scholarships,
            'total_eligible_amount': total_eligible_amount,
            'eligible_count': len(eligible_scholarships),
            'ineligible_count': len(ineligible_scholarships)
        }
    
    def rank_students(self, students, scholarship):
        """
        Rank all eligible students for a specific scholarship by priority score.
        
        Args:
            students: List of Student objects
            scholarship: Scholarship object
            
        Returns:
            list: Ranked list of eligible students with scores
        """
        ranked_students = []
        
        for student in students:
            result = self.check_eligibility(student, scholarship)
            
            if result['eligible']:
                ranked_students.append({
                    'student': student.to_dict(),
                    'priority_score': result['priority_score'],
                    'scholarship_name': scholarship.name
                })
        
        # Sort by priority score (descending)
        ranked_students.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Add rank numbers
        for i, item in enumerate(ranked_students, 1):
            item['rank'] = i
        
        return ranked_students


# Create a global instance for use across the application
rules_engine = RulesEngine()
