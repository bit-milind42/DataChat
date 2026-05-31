"""Data Insights Agent - Generates intelligent insights from query results"""

import json
from langchain_google_genai import ChatGoogleGenerativeAI
from databases.models import Dataset
import os


class DataInsights:
    """Generates insights and patterns from query results"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,  # Higher for more creative insights
            api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    def analyze(self, question: str, results: list, columns: list, dataset: Dataset) -> dict:
        """
        Generate key insights from query results
        
        Returns:
            {
                "summary": "1-2 sentence overview of findings",
                "key_findings": ["insight1", "insight2", "insight3"],
                "patterns": ["pattern1", "pattern2"],
                "anomalies": ["anomaly1"] or [],
                "recommendations": ["rec1", "rec2"]
            }
        """
        try:
            if not results:
                return {
                    "summary": "No results found for the query.",
                    "key_findings": [],
                    "patterns": [],
                    "anomalies": [],
                    "recommendations": []
                }
            
            # Prepare results sample
            sample_size = min(10, len(results))
            results_sample = results[:sample_size]
            
            # Get column info
            columns_str = ", ".join(columns[:15])  # Limit to first 15 columns
            
            prompt = f"""You are a data analyst. Analyze these query results and provide actionable insights.

Original Question: {question}

Data Columns: {columns_str}

Sample Results (showing {sample_size} of {len(results)} rows):
{json.dumps(results_sample, default=str)}

Total Rows Returned: {len(results)}

Provide insights in JSON format ONLY (no markdown):
{{
  "summary": "1-2 sentence overview of the most important finding",
  "key_findings": ["finding1 with numbers/specifics", "finding2", "finding3"],
  "patterns": ["observable pattern1", "observable pattern2"],
  "anomalies": ["unusual value or trend1"] or [],
  "recommendations": ["actionable recommendation1", "recommendation2"]
}}

Guidelines:
- Findings should be specific with actual numbers from the data
- Patterns should describe trends or relationships
- Anomalies: only include if there are obvious outliers
- Recommendations: suggest what action could be taken
- Keep each insight to 1-2 sentences max"""
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON
            try:
                if "{" in response_text and "}" in response_text:
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                    insights = json.loads(json_str)
                    
                    # Validate structure
                    return {
                        "summary": insights.get("summary", "Analysis complete."),
                        "key_findings": insights.get("key_findings", [])[:3],
                        "patterns": insights.get("patterns", [])[:2],
                        "anomalies": insights.get("anomalies", [])[:2],
                        "recommendations": insights.get("recommendations", [])[:2]
                    }
            except json.JSONDecodeError:
                pass
            
            # Fallback
            return {
                "summary": f"Returned {len(results)} results for the query.",
                "key_findings": [],
                "patterns": [],
                "anomalies": [],
                "recommendations": []
            }
            
        except Exception as e:
            return {
                "summary": "Unable to generate insights.",
                "key_findings": [],
                "patterns": [],
                "anomalies": [],
                "recommendations": [],
                "error": str(e)
            }
