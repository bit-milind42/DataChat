"""Query Validator Agent - Validates if NL queries are semantically sound before execution"""

import json
from langchain_google_genai import ChatGoogleGenerativeAI
from databases.models import Dataset
import os


class QueryValidator:
    """Validates natural language queries against dataset schema"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    def validate(self, question: str, dataset: Dataset) -> dict:
        """
        Validate if a question can be answered with the given dataset
        
        Returns:
            {
                "is_valid": bool,
                "confidence": 0.0-1.0,
                "reason": str,
                "suggestions": [str]  # if not valid, suggestions to fix
            }
        """
        try:
            table_info = "\n".join([f"- {col}" for col in (dataset.columns or [])])
            
            prompt = f"""You are a data validation expert. Determine if this question can be answered using the available data.

Question: {question}

Available columns in dataset:
{table_info}

Dataset has {dataset.row_count} rows total.

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation",
  "suggestions": ["suggestion1", "suggestion2"] or []
}}

Validation rules:
1. Question should reference columns that exist in the dataset
2. Question should be answerable with SELECT queries
3. Question should not ask for data that's clearly impossible
4. Vague questions are acceptable (can be interpreted multiple ways)
5. Return confidence score: 1.0 = definitely answerable, 0.0 = definitely not"""
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON
            try:
                if "{" in response_text and "}" in response_text:
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                    validation_result = json.loads(json_str)
                    
                    # Ensure all keys exist
                    return {
                        "is_valid": validation_result.get("is_valid", True),
                        "confidence": validation_result.get("confidence", 0.5),
                        "reason": validation_result.get("reason", ""),
                        "suggestions": validation_result.get("suggestions", [])
                    }
            except json.JSONDecodeError:
                pass
            
            # Fallback to valid if can't parse
            return {
                "is_valid": True,
                "confidence": 0.5,
                "reason": "Unable to validate, proceeding with query",
                "suggestions": []
            }
            
        except Exception as e:
            return {
                "is_valid": True,
                "confidence": 0.3,
                "reason": f"Validation error: {str(e)}",
                "suggestions": []
            }
