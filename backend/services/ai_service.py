"""AI service for Mistral AI integration."""
import json
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with Mistral AI API."""
    
    def __init__(self):
        """Initialize AI service with API key and model."""
        self.api_key = settings.mistral_api_key
        self.model = settings.mistral_model
        self.base_url = "https://api.mistral.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _parse_json_response(self, response: str) -> Any:
        """
        Parse JSON from AI response, handling markdown code blocks.
        
        Args:
            response: raw string from AI
            
        Returns:
            Parsed JSON object
        """
        if not response:
            return None
            
        clean_response = response.strip()
        
        # Remove markdown code blocks if present
        if clean_response.startswith("```"):
            # Find the first newline to skip ```json or ```
            lines = clean_response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_response = "\n".join(lines).strip()
            
        try:
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {clean_response}")
            logger.error(f"Error: {str(e)}")
            return None
    
    async def _make_request(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Make a request to Mistral AI API.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            AI response text or None if error
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPError as e:
            logger.error(f"Mistral AI API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in AI request: {str(e)}")
            return None
    
    async def analyze_task(self, description: str) -> Dict[str, Any]:
        """
        Analyze a task description and extract metadata.
        
        Args:
            description: Natural language task description
            
        Returns:
            Dictionary with extracted task information
        """
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"""You are a task planning assistant.
Current date and time: {current_date}

Analyze the following task description and extract:
1. Task name/summary (concise title)
2. Estimated duration (in minutes)
3. Priority (high/medium/low)
4. Deadline (if mentioned, in ISO format. Use the current date to resolve relative dates like "tomorrow" or "Friday")
5. Any dependencies or prerequisites
6. Whether it requires focused time or can be interrupted (is_flexible: true/false)

Task: "{description}"

Respond ONLY with valid JSON in this exact format:
{{
    "title": "extracted task title",
    "estimated_duration": 60,
    "priority": "medium",
    "deadline": "2024-01-20T17:00:00" or null,
    "dependencies": [],
    "is_flexible": true,
    "confidence": 0.8,
    "missing_info": ["list of unclear details"]
}}

If information is unclear or missing, include it in missing_info array."""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.3)
        
        if not response:
            return {
                "title": description[:100],
                "estimated_duration": None,
                "priority": "medium",
                "deadline": None,
                "dependencies": [],
                "is_flexible": True,
                "confidence": 0.0,
                "missing_info": ["AI service unavailable"]
            }
        
        try:
            # Parse JSON response
            result = self._parse_json_response(response)
            if result:
                return result
            raise ValueError("Empty or invalid parse result")
        except Exception:
            logger.error(f"Failed to parse AI response: {response}")
            return {
                "title": description[:100],
                "estimated_duration": None,
                "priority": "medium",
                "deadline": None,
                "dependencies": [],
                "is_flexible": True,
                "confidence": 0.0,
                "missing_info": ["Failed to parse AI response"]
            }
    
    async def generate_clarifications(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Generate clarifying questions for a task.
        
        Args:
            task_data: Task information dictionary
            
        Returns:
            List of clarifying questions
        """
        prompt = f"""Based on this task information:
Title: {task_data.get('title', 'Unknown')}
Description: {task_data.get('description', 'No description')}
Priority: {task_data.get('priority', 'Not specified')}
Deadline: {task_data.get('deadline', 'Not specified')}
Duration: {task_data.get('estimated_duration', 'Not specified')} minutes

Generate 2-3 targeted questions to help schedule this task effectively. Focus on missing details like:
- Exact duration if not specified
- Flexibility (can it be moved/interrupted?)
- Optimal time of day
- Dependencies on other tasks

Respond ONLY with valid JSON array of strings:
["Question 1?", "Question 2?", "Question 3?"]"""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.5)
        
        if not response:
            return ["How long do you estimate this task will take?", 
                    "Is there a specific time of day that works best for this task?"]
        
        try:
            questions = self._parse_json_response(response)
            return questions if isinstance(questions, list) else []
        except Exception:
            logger.error(f"Failed to parse clarification questions: {response}")
            return ["How long do you estimate this task will take?"]
    
    async def suggest_schedule(self, tasks: List[Dict], calendar_events: List[Dict], 
                               preferences: Dict) -> Dict[str, Any]:
        """
        Get AI suggestions for optimal scheduling.
        
        Args:
            tasks: List of tasks to schedule
            calendar_events: Existing calendar events
            preferences: User preferences
            
        Returns:
            Dictionary with scheduling suggestions
        """
        prompt = f"""You are a scheduling assistant. Given these constraints:

Tasks to schedule:
{json.dumps(tasks, indent=2)}

Existing calendar events:
{json.dumps(calendar_events, indent=2)}

User preferences:
{json.dumps(preferences, indent=2)}

Suggest optimal time slots for each task. Consider:
- Task deadlines and priorities
- Working hours
- Break requirements
- Task dependencies
- Optimal work patterns (complex tasks in morning, etc.)

Respond ONLY with valid JSON:
{{
    "suggestions": [
        {{
            "task_id": 1,
            "suggested_start": "2024-01-20T09:00:00",
            "suggested_end": "2024-01-20T10:30:00",
            "reasoning": "High priority task scheduled in morning for peak productivity"
        }}
    ],
    "warnings": ["Any potential conflicts or issues"]
}}"""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.4)
        
        if not response:
            return {"suggestions": [], "warnings": ["AI service unavailable"]}
        
        try:
            result = self._parse_json_response(response)
            if result:
                return result
            raise ValueError("Empty or invalid parse result")
        except Exception:
            logger.error(f"Failed to parse schedule suggestions: {response}")
            return {"suggestions": [], "warnings": ["Failed to parse AI response"]}
    
    async def explain_scheduling(self, task: Dict, slot: Dict, context: Dict) -> str:
        """
        Generate explanation for why a task was scheduled at a specific time.
        
        Args:
            task: Task information
            slot: Time slot information
            context: Additional context (other tasks, preferences, etc.)
            
        Returns:
            Human-readable explanation
        """
        prompt = f"""Explain why this task was scheduled at this time:

Task: {task.get('title')}
Priority: {task.get('priority')}
Deadline: {task.get('deadline', 'None')}
Duration: {task.get('estimated_duration')} minutes

Scheduled time: {slot.get('start_time')} to {slot.get('end_time')}

Context:
{json.dumps(context, indent=2)}

Provide a brief, clear explanation (2-3 sentences) for why this is a good time slot for this task."""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.6)
        
        return response or "This time slot was selected based on task priority and available time."


# Global AI service instance
ai_service = AIService()
