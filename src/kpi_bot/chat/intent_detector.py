import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..models import KPIQuery, KPIDefinition
from ...monitoring.logger import logger


class IntentDetector:
    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.intent_patterns = {
            "kpi_query": [
                r"what.*(revenue|sales|income)",
                r"show.*(opex|expenses|costs)",
                r"how.*(performing|doing)",
                r"(variance|difference|change).*from",
                r"what.*(margin|profit)",
                r"cash.*(position|flow)",
                r"(compare|vs|versus|against)",
                r"(trend|trending|pattern)"
            ],
            "drill_down": [
                r"(detail|breakdown|drill|deeper)",
                r"show.*(more|detail|specific)",
                r"(segment|region|department|category)"
            ],
            "time_filter": [
                r"(this|last|previous).*(month|quarter|year)",
                r"(ytd|year to date|quarterly|monthly)",
                r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
                r"(q1|q2|q3|q4|quarter)"
            ],
            "comparison": [
                r"(vs|versus|compared to|against)",
                r"(prior year|py|last year|ly)",
                r"(plan|budget|forecast)",
                r"(fx.neutral|currency.adjusted)"
            ]
        }
        
        self.kpi_keywords = {
            "revenue": ["revenue", "sales", "income", "gross revenue", "net revenue"],
            "opex": ["opex", "operating expenses", "operational costs", "overhead"],
            "gross_margin": ["gross margin", "gm", "margin", "profitability"],
            "cash": ["cash", "cash flow", "liquidity", "cash position"],
            "variance": ["variance", "difference", "change", "deviation"]
        }

    def detect_intent(self, query: str, available_kpis: List[KPIDefinition]) -> Dict[str, any]:
        query_lower = query.lower()
        
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent] = score
        
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "kpi_query"
        
        detected_kpis = self._detect_kpis(query_lower, available_kpis)
        time_filters = self._extract_time_filters(query_lower)
        comparison_type = self._detect_comparison_type(query_lower)
        
        return {
            "primary_intent": primary_intent,
            "confidence": intent_scores.get(primary_intent, 0) / len(self.intent_patterns[primary_intent]),
            "detected_kpis": detected_kpis,
            "time_filters": time_filters,
            "comparison_type": comparison_type,
            "raw_query": query
        }

    def _detect_kpis(self, query: str, available_kpis: List[KPIDefinition]) -> List[Dict[str, any]]:
        detected = []
        
        for kpi in available_kpis:
            kpi_score = 0
            
            if kpi.name.lower() in query:
                kpi_score += 3
            
            for keyword in kpi.tags:
                if keyword.lower() in query:
                    kpi_score += 2
            
            if kpi.description.lower() in query:
                kpi_score += 1
            
            if kpi_score > 0:
                detected.append({
                    "kpi_id": kpi.id,
                    "name": kpi.name,
                    "confidence": min(kpi_score / 5, 1.0)
                })
        
        return sorted(detected, key=lambda x: x["confidence"], reverse=True)

    def _extract_time_filters(self, query: str) -> Dict[str, str]:
        time_filters = {}
        
        quarter_match = re.search(r'(q[1-4]|quarter [1-4])', query)
        if quarter_match:
            time_filters["quarter"] = quarter_match.group(1)
        
        year_match = re.search(r'(20\d{2}|\d{4})', query)
        if year_match:
            time_filters["year"] = year_match.group(1)
        
        month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', query)
        if month_match:
            time_filters["month"] = month_match.group(1)
        
        if "ytd" in query or "year to date" in query:
            time_filters["period"] = "ytd"
        elif "this month" in query:
            time_filters["period"] = "current_month"
        elif "this quarter" in query:
            time_filters["period"] = "current_quarter"
        elif "last month" in query:
            time_filters["period"] = "previous_month"
        elif "last quarter" in query:
            time_filters["period"] = "previous_quarter"
        elif "last year" in query:
            time_filters["period"] = "previous_year"
        
        return time_filters

    def _detect_comparison_type(self, query: str) -> Optional[str]:
        if re.search(r'(prior year|py|last year|ly)', query):
            return "prior_year"
        elif re.search(r'(plan|budget|forecast)', query):
            return "plan"
        elif re.search(r'(fx.neutral|currency.adjusted)', query):
            return "fx_neutral"
        return None

    def enhance_with_llm(self, query: str, context: Dict[str, any]) -> Dict[str, any]:
        try:
            prompt = f"""
            Analyze this business query and extract structured information:
            
            Query: "{query}"
            
            Available KPIs: {[kpi['name'] for kpi in context.get('detected_kpis', [])]}
            
            Please identify:
            1. Primary business intent
            2. Specific KPIs mentioned
            3. Time period requested
            4. Comparison type needed
            5. Any filters or dimensions
            
            Return as structured JSON.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business intelligence assistant that analyzes KPI queries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            llm_analysis = response.choices[0].message.content
            
            context["llm_analysis"] = llm_analysis
            return context
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return context

    def find_similar_queries(self, query: str, previous_queries: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        if not previous_queries:
            return []
        
        query_embedding = self.model.encode([query])
        previous_embeddings = self.model.encode(previous_queries)
        
        similarities = cosine_similarity(query_embedding, previous_embeddings)[0]
        
        similar_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(previous_queries[i], similarities[i]) for i in similar_indices if similarities[i] > 0.7]