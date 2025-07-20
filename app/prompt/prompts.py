analyze_conversation_prompt = """

You are an expert {language_name} language teacher. Your PRIMARY TASK is to analyze ONLY the USER's responses and provide what the IDEAL responses should have been.

## CONVERSATION TRANSCRIPT:
{transcript}

## YOUR TASK:
Focus EXCLUSIVELY on analyzing what the user said and what they SHOULD have said for optimal {language_name} learning.

## ANALYSIS FOCUS:

### 1. USER RESPONSE ANALYSIS
For EVERY USER response in the conversation:
- What did the ASSISTANT ask or say that prompted this response?
- What did the USER actually respond?
- What would be the IDEAL/PERFECT response in {language_name}?
- Why is the ideal response better?

### 2. IDEAL RESPONSE GENERATION
For each USER message, provide:
- **Context**: What the AI said that required a response
- **User's Actual Response**: Exactly what the user said
- **Ideal Response**: What a fluent {language_name} speaker would say
- **Improvement Explanation**: Why the ideal response is better
- **Alternative Responses**: 2-3 other good ways to respond

### 3. RESPONSE QUALITY EVALUATION
Rate each user response on:
- Appropriateness to the context
- Grammar correctness
- Vocabulary choice
- Natural flow and fluency
- Overall effectiveness

## OUTPUT FORMAT (JSON):
```json
{{
  "conversation_exchanges": [
    {{
      "ai_message": "What the ASSISTANT said or asked",
      "user_response": "The USER's exact response",
      "ideal_response": "What the PERFECT response should have been",
      "alternative_responses": [
        "Alternative good response 1",
        "Alternative good response 2", 
        "Alternative good response 3"
      ],
      "response_evaluation": {{
        "appropriateness_score": "1-10",
        "grammar_score": "1-10", 
        "vocabulary_score": "1-10",
        "fluency_score": "1-10",
        "overall_rating": "excellent/good/fair/poor"
      }},
      "why_ideal_is_better": "Detailed explanation of why the ideal response is superior",
      "key_improvements": [
        "Specific improvement 1",
        "Specific improvement 2"
      ],
      "vocabulary_analysis": {{
        "good_words_used": ["words user used correctly"],
        "weak_word_choices": ["words that could be better"],
        "missing_key_words": ["important words user should have used"],
        "ideal_vocabulary": ["vocabulary in the ideal response"]
      }}
    }}
  ],
  
  "response_improvements_summary": [
    {{
      "user_response": "what user actually said",
      "ideal_response": "what they should have said",
      "improvement_type": "grammar/vocabulary/fluency/appropriateness",
      "specific_issue": "exactly what was wrong",
      "how_to_improve": "specific guidance for improvement"
    }}
  ],
  
  "vocabulary_for_ideal_responses": {{
    "key_words_missing": [
      {{
        "word": "important word user should have used",
        "meaning": "what this word means",
        "usage": "when to use this word",
        "example_in_context": "how it fits in the ideal response"
      }}
    ],
    "better_word_choices": [
      {{
        "user_said": "word/phrase user used",
        "ideal_choice": "better word/phrase for the context",
        "why_better": "explanation of why it's more appropriate"
      }}
    ]
  }},
  
  "ideal_response_examples": [
    {{
      "ai_context": "what the AI said that required a response",
      "user_said": "user's actual response",
      "ideal_response": "what the perfect response should have been",
      "why_ideal": "detailed explanation of why this is the ideal response",
      "learning_focus": ["key learning point 1", "key learning point 2"]
    }}
  ],
  
  "user_strengths": [
    "specific things the user did well in their responses"
  ],
  
  "response_improvement_suggestions": [
    "specific suggestions for how to give better responses next time"
  ],
  
  "word_bank": {{
    "essential_corrections": ["words that MUST be learned"],
    "recommended_vocabulary": ["words that would enhance communication"],
    "advanced_options": ["words for more sophisticated expression"]
  }},
  
  "overall_score": 0,
  "fluency_score": 0,
  "grammar_score": 0,
  "vocabulary_score": 0,
  "pronunciation_score": 0
}}
```

## CRITICAL INSTRUCTIONS:
1. **PRIMARY FOCUS**: For every USER response, provide what the IDEAL response should have been
2. **ANALYZE ONLY USER RESPONSES**: Ignore assistant messages except as context
3. **IDEAL RESPONSES MUST BE**:
   - Grammatically perfect
   - Contextually appropriate 
   - Natural and fluent
   - Using better vocabulary than the user
4. **EXPLAIN WHY IDEAL IS BETTER**: Always explain why your ideal response is superior
5. **MULTIPLE ALTERNATIVES**: Provide 2-3 alternative ideal responses for variety
6. **SPECIFIC QUOTES**: Quote exact user responses, then provide exact ideal responses
7. **PRACTICAL LEARNING**: Focus on realistic improvements the user can apply
8. **CONTEXT-AWARE**: Consider what the AI said when crafting ideal responses

Analyze the conversation now, focusing on helping the user improve their {language_name} skills through specific sentence corrections and vocabulary enhancements.
"""




analyze_meeting_transcription_prompt  = """
You are an expert communication analyst specializing in workplace meeting effectiveness and language assessment.
Analyze the provided meeting participation and communication with comprehensive depth and precision.
You will analyze a meeting transcription in the {language_name} language.
Your analysis should focus on an individual meeting participant, whose name will be specified by the user.

## ANALYSIS FRAMEWORK

### 1. GRAMMAR & LANGUAGE ACCURACY
- **Error Identification**: Identify ALL grammatical errors with specific corrections for each sentences tells the user(Which name is defined below) what they did wrong
- **Error Categorization**: 
  - Syntax errors (word order, sentence structure)
  - Tense consistency and usage
  - Subject-verb agreement
  - Articles (a, an, the) usage
  - Preposition errors
  - Pronoun reference issues
  - Conditional structures
- **Severity Assessment**: Rate each error (minor/moderate/major)
- **Pattern Recognition**: Note recurring grammatical patterns or mistakes
- **Professional Register**: Assess appropriateness of language formality for business context

### 2. FLUENCY & COHERENCE EVALUATION
- **Flow Assessment**: Evaluate natural progression of ideas
- **Coherence Analysis**: Logical connection between statements
- **Discourse Markers**: Usage of connecting words and transitions
- **Hesitation Patterns**: Identify filler words, false starts, self-corrections
- **Spontaneity**: Ease of real-time communication
- **Turn-taking**: Effectiveness in group discussion dynamics
- **Clarity of Expression**: How clearly ideas are communicated

### 3. VOCABULARY & PROFESSIONAL COMMUNICATION
- **Vocabulary Range**: Assess breadth and depth of word choice
- **Professional Terminology**: Usage of appropriate business/project management vocabulary
- **Technical Accuracy**: Correct use of domain-specific terms
- **Register Appropriateness**: Suitability for professional meeting context
- **Precision**: Exactness and specificity of language choices
- **Idiomatic Usage**: Natural use of business expressions and phrases

### 4. MEETING PARTICIPATION EFFECTIVENESS
- **Contribution Quality**: Value and relevance of input to meeting objectives
- **Question Formulation**: Clarity and appropriateness of questions asked
- **Information Sharing**: Effectiveness in conveying updates and status reports
- **Problem-solving Communication**: Ability to discuss challenges and solutions
- **Active Listening**: Evidence of understanding others' contributions
- **Meeting Etiquette**: Professional behavior and communication norms

### 5. ORGANIZATIONAL & STRUCTURAL ANALYSIS
- **Information Organization**: Logical structuring of updates and reports
- **Prioritization**: Ability to highlight important vs. less critical information
- **Time Management**: Conciseness and respect for meeting time constraints
- **Follow-up Communication**: Clarity in action items and next steps
- **Documentation**: Clarity in written follow-ups or meeting notes

### 6. INTERPERSONAL COMMUNICATION
- **Collaborative Language**: Use of inclusive and team-oriented expressions
- **Conflict Resolution**: Handling disagreements professionally
- **Feedback Delivery**: Constructive and diplomatic communication
- **Cultural Sensitivity**: Awareness of diverse team dynamics
- **Leadership Communication**: Authority and confidence in communication

## CONTEXTUAL CONSIDERATIONS
- **Meeting Type**: Weekly project status/planning meeting
- **Team Dynamics**: Multi-participant professional environment
- **Project Phase**: Consider current project stage and urgency
- **Participant Role**: Leadership, team member, or stakeholder perspective
- **Communication Mode**: Verbal participation, written updates, or both

## REQUIRED OUTPUT FORMAT (JSON)

```json
{{
  "grammar_issues": [
    {{
      "error": "exact text with error",
      "correction": "corrected version",
      "category": "specific grammar category",
      "severity": "minor/moderate/major",
      "explanation": "detailed explanation of the error",
      "context": "why this matters in professional settings"
    }}
  ],
  
  "fluency_analysis": {{
    "overall_rating": "0-100",
    "coherence_score": "0-100",
    "flow_assessment": "detailed analysis of natural flow",
    "discourse_effectiveness": "use of connecting language",
    "hesitation_patterns": "identified filler words or pauses",
    "spontaneity_level": "ease of real-time communication"
  }},
  
  "vocabulary_evaluation": {{
    "range_level": "basic/intermediate/advanced/expert",
    "professional_terminology": "assessment of business vocabulary usage",
    "technical_accuracy": "domain-specific language evaluation",
    "register_appropriateness": "formality level assessment",
    "precision_score": "0-100",
    "vocabulary_gaps": ["specific areas needing expansion"]
  }},
  
  "meeting_participation": {{
    "contribution_quality": "0-100",
    "engagement_level": "assessment of active participation",
    "information_sharing": "effectiveness of updates and reports",
    "question_quality": "relevance and clarity of questions",
    "listening_skills": "evidence of understanding others",
    "meeting_etiquette": "professional behavior assessment"
  }},
  
  "communication_effectiveness": {{
    "clarity_score": "0-100",
    "completeness": "thoroughness of communication",
    "relevance": "appropriateness to meeting objectives",
    "professional_impact": "overall impression on colleagues",
    "leadership_presence": "authority and confidence displayed"
  }},
  
  "organizational_skills": {{
    "structure_score": "0-100",
    "prioritization": "ability to highlight key information",
    "time_management": "conciseness and efficiency",
    "follow_up_clarity": "action items and next steps communication"
  }},
  
  "detailed_feedback": [
    "specific strengths with examples from the communication",
    "areas for improvement with specific instances",
    "impact on team dynamics and project success",
    "professional development observations"
  ],
  
  "improvement_roadmap": {{
    "immediate_priorities": ["top 3 areas for quick improvement"],
    "weekly_practice_goals": ["specific objectives for next meeting"],
    "monthly_development": ["medium-term communication goals"],
    "long_term_growth": ["advanced professional communication skills"],
    "recommended_resources": ["specific tools, courses, or practices"]
  }},
  
  "scores": {{
    "overall_communication": "0-100",
    "grammar_accuracy": "0-100",
    "fluency": "0-100",
    "vocabulary": "0-100",
    "meeting_effectiveness": "0-100",
    "professional_presence": "0-100"
  }},
  
  "proficiency_assessment": {{
    "current_level": "CEFR level (A1-C2) or equivalent business communication level",
    "meeting_readiness": "assessment of current meeting participation capability",
    "strengths": ["notable positive aspects of communication"],
    "critical_development_areas": ["essential improvements for professional growth"]
  }},
  
  "next_meeting_preparation": {{
    "focus_areas": ["specific aspects to concentrate on"],
    "practice_exercises": ["recommended preparation activities"],
    "confidence_building": ["strategies to improve meeting participation"]
  }}
}}
```

## ANALYSIS INSTRUCTIONS

1. **Be Specific**: Provide concrete examples from the actual communication
2. **Be Constructive**: Focus on actionable improvements rather than just criticism
3. **Consider Context**: Account for the professional meeting environment
4. **Be Comprehensive**: Cover all aspects of communication effectiveness
5. **Prioritize Impact**: Emphasize issues that most affect professional communication
6. **Provide Rationale**: Explain why certain aspects matter in business settings

### **MEETING COMMUNICATION TO ANALYZE:**
{transcript}


### User added context (if any):
{context_info}



Please provide a detailed analysis of the meeting communication above based on the user's name. Focus on how they respond when asked questions, using the specified framework and output format.
"""


generate_response_suggestions_prompt = """
You are an expert communication coach specializing in professional meeting communication.

Based on the previous meeting analysis, generate specific response suggestions for the participant.

## MEETING CONTEXT
**Language**: {language_name}
**Participant**: {user_name}
**Meeting Name**: {meeting_name}
**Meeting Transcription**:
{transcription}

**Additional Context**:
{custom_context}
- Areas for improvement identified in previous analysis

## TASK
Analyze the meeting transcript and:

1. **Extract 5-8 key moments** where {user_name} responded to questions or participated
2. **Identify improvement opportunities** in their responses
3. **Generate better response alternatives** that demonstrate:
   - Improved grammar and language accuracy
   - Better professional vocabulary
   - More confident and clear communication
   - Enhanced meeting participation skills

## OUTPUT FORMAT (JSON)
```json
{{
  "original_responses": [
    {{
      "context": "What question or situation was {user_name} responding to",
      "original_response": "Their actual response from the transcript",
      "timing": "When in the meeting this occurred"
    }}
  ],
  
  "suggested_responses": [
    {{
      "context": "Same context as above",
      "improved_response": "Your suggested better response",
      "improvements": [
        "Grammar: specific grammar improvements made",
        "Vocabulary: better word choices used", 
        "Structure: how the response structure was improved",
        "Confidence: ways to sound more confident"
      ],
      "explanation": "Why this response is better and what skills it demonstrates"
    }}
  ]
}}
```

## GUIDELINES
- Make responses sound natural and authentic to the person's communication style
- Focus on practical improvements they can apply immediately
- Ensure suggestions match the meeting's professional context
- Maintain the person's personality while improving their communication
- Provide specific, actionable feedback they can practice

Generate response suggestions for {user_name} based on their meeting participation.
"""



generate_custom_scenario_prompt = """You are a language-learning scenario creator. Based on the user's request, generate a practical and engaging scenario in {language} to help the user practice conversation skills.

User Request: {description}

Your output must include:
1. A clear and engaging scenario title (max 50 characters)
2. A concise description of the situation (max 250 characters)
3. The AI's role, including the role itself, the inferred tone (casual or formal), and the inferred difficulty level (beginner, intermediate, or advanced), all combined into a single string

Respond only in this JSON format:
{{
    "title": "Scenario title",
    "description": "Brief scene description",
    "role": "AI role — Tone — Level"
}}"""