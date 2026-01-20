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
    
    async def analyze_task(self, description: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Analyze a task description and extract metadata.
        
        Args:
            description: Natural language task description or follow-up answer
            history: Optional conversation history for context
            
        Returns:
            Dictionary with extracted task information
        """
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
                system_prompt = f"""You are a task planning assistant.
Current date and time: {current_date}

Goal: extract one or more tasks from a single user message. The user may list multiple tasks in one sentence (e.g., "email Alex, finish report, and buy groceries"). Detect each task separately.

For EACH task, extract:
1. title: Concise summary
2. estimated_duration: In minutes (int)
3. priority: "high", "medium", or "low"
4. deadline: ISO format or null. Resolve relative dates like "tomorrow".
5. dependencies: List of task IDs or titles it depends on.
6. is_flexible: boolean (true for interruptible tasks)

Respond ONLY with valid JSON in this format (always use tasks array, even for one task):
{
    "tasks": [
        {
            "title": "string",
            "estimated_duration": int or null,
            "priority": "string",
            "deadline": "ISO string" or null,
            "dependencies": [],
            "is_flexible": bool,
            "missing_info": ["field_name1", "field_name2"],
            "status": "COMPLETE" or "NEEDS_CLARIFICATION"
        }
    ]
}

Status per task: set COMPLETE only if title, estimated_duration, priority, AND a deadline (or confirmed no deadline) are present. Otherwise add missing fields to missing_info and set NEEDS_CLARIFICATION.
"""

        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": description})
        
        response = await self._make_request(messages, temperature=0.2)
        
        if not response:
            return {
                "title": description[:100],
                "status": "ERROR",
                "missing_info": ["AI service unavailable"]
            }
        
        try:
            raw = self._parse_json_response(response)
            if not raw:
                raise ValueError("Empty parse")

            # Normalize to tasks array
            tasks = raw.get("tasks") if isinstance(raw, dict) else None
            if tasks is None:
                tasks = [raw]

            normalized = []
            for item in tasks:
                if not isinstance(item, dict):
                    continue
                status = item.get("status") or ("COMPLETE" if not item.get("missing_info") else "NEEDS_CLARIFICATION")
                normalized.append({
                    "title": item.get("title") or description[:100],
                    "estimated_duration": item.get("estimated_duration"),
                    "priority": item.get("priority") or "medium",
                    "deadline": item.get("deadline"),
                    "dependencies": item.get("dependencies") or [],
                    "is_flexible": item.get("is_flexible", True),
                    "missing_info": item.get("missing_info") or [],
                    "status": status,
                })

            if not normalized:
                raise ValueError("No tasks after normalization")

            return {"tasks": normalized}

        except Exception:
            logger.error(f"Failed to parse AI response: {response}")
            return {
                "tasks": [{
                    "title": description[:100],
                    "estimated_duration": None,
                    "priority": "medium",
                    "deadline": None,
                    "dependencies": [],
                    "is_flexible": True,
                    "missing_info": ["Failed to parse AI response"],
                    "status": "ERROR"
                }]
            }
    
    async def generate_clarifications(self, task_data: Dict[str, Any], history: Optional[List[Dict[str, str]]] = None) -> List[str]:
        """
        Generate clarifying questions for a task with conversational context.
        """
        prompt = f"""Based on this task analysis so far:
{json.dumps(task_data, indent=2)}

Generate ONE short, friendly follow-up question to ask the user to clarify the most important missing details.
Common missing details: duration, deadline, priority, or if they have dependencies.

Respond ONLY with a JSON array containing the question:
["Your short question here?"]"""

        messages = [{"role": "system", "content": "You are a helpful scheduling assistant."}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        response = await self._make_request(messages, temperature=0.5)
        
        if not response:
            return ["Could you tell me how long this task might take?"]
        
        try:
            questions = self._parse_json_response(response)
            return questions if isinstance(questions, list) else []
        except Exception:
            return ["Could you provide more details about this task?"]

    async def generate_rescheduling_explanation(self, updated_task: Dict, original_task: Optional[Dict], 
                                                reason: str, context: Dict) -> str:
        """
        Generate an AI explanation for why a task was rescheduled.
        """
        prompt = f"""Explain why this task was shifted in the schedule:
Task: {updated_task.get('title')}
Reason for update: {reason}
Original timing: {original_task.get('start_time') if original_task else 'Not scheduled'}
New timing: {updated_task.get('start_time')}

Provide a brief, supportive explanation (1-2 sentences) for the user."""

        messages = [
            {"role": "system", "content": "You are a supportive personal assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.6)
        return response or f"Rescheduled {updated_task.get('title')} due to {reason}."
    
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
