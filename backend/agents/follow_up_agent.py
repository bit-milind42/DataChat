"""Follow-up Questions Agent - Suggests context-aware follow-up questions"""

import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from databases.models import Dataset, QueryResult
import os


class FollowUpAgent:
    """Generates intelligent context-aware follow-up questions"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    def generate_follow_ups(
        self, 
        original_question: str, 
        results: List[Dict[str, Any]], 
        columns: List[str],
        dataset: Dataset,
        previous_questions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate context-aware follow-up questions based on original question and results
        
        Returns:
            {
                "follow_up_questions": [
                    {
                        "question": "What is the trend over time?",
                        "reasoning": "Based on the temporal data in results",
                        "type": "trend_analysis"  # drill_down, comparison, trend, anomaly, etc.
                    }
                ],
                "suggested_next_steps": ["Export data", "Create visualization"],
                "available_analyses": ["correlation", "distribution", "outliers"]
            }
        """
        try:
            if not results:
                return {
                    "follow_up_questions": [],
                    "suggested_next_steps": [],
                    "available_analyses": []
                }
            
            # Prepare context
            sample_results = results[:5]
            columns_str = ", ".join(columns[:10])
            previous_questions_str = "\n".join(previous_questions[-3:] if previous_questions else [])
            
            prompt = f"""You are a data analysis expert. Based on the original question and query results, suggest 3-4 intelligent follow-up questions that would provide deeper insights.

Original Question: {original_question}

Available Columns: {columns_str}

Sample Results (first 5 rows):
{json.dumps(sample_results, default=str)}

Total Results: {len(results)} rows

{('Previous Questions Asked:\n' + previous_questions_str + '\n') if previous_questions else ''}

Generate follow-up questions in JSON format ONLY (no markdown):
{{
  "follow_up_questions": [
    {{
      "question": "specific follow-up question",
      "reasoning": "why this question would be useful",
      "type": "drill_down|comparison|trend|anomaly|distribution|correlation|outlier"
    }}
  ],
  "suggested_next_steps": ["step1", "step2"],
  "available_analyses": ["analysis1", "analysis2"]
}}

Guidelines:
- Questions should build on the original query
- Consider temporal, categorical, and numerical relationships
- Avoid questions already asked (if shown above)
- Include mix of: drill-downs, comparisons, trends, and anomaly detection
- Each question should be answerable with the available data
- Focus on actionable insights"""
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract and parse JSON
            try:
                if "{" in response_text and "}" in response_text:
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                    suggestions = json.loads(json_str)
                    
                    return {
                        "follow_up_questions": suggestions.get("follow_up_questions", [])[:4],
                        "suggested_next_steps": suggestions.get("suggested_next_steps", []),
                        "available_analyses": suggestions.get("available_analyses", [])
                    }
            except json.JSONDecodeError:
                pass
            
            # Fallback
            return {
                "follow_up_questions": [
                    {
                        "question": "What are the trends over time in this data?",
                        "reasoning": "To understand temporal patterns",
                        "type": "trend"
                    },
                    {
                        "question": "How does this break down by category?",
                        "reasoning": "To understand categorical distributions",
                        "type": "drill_down"
                    }
                ],
                "suggested_next_steps": ["Visualize data", "Export results"],
                "available_analyses": ["distribution", "correlation"]
            }
            
        except Exception as e:
            return {
                "follow_up_questions": [],
                "suggested_next_steps": [],
                "available_analyses": [],
                "error": str(e)
            }
