import openai
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..models import KPIResult, KPIDefinition, KPIQuery, KPIResponse
from ...monitoring.logger import logger


class NarrativeGenerator:
    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.system_prompts = {
            "revenue": "You are a finance expert specializing in revenue analysis. Provide clear, actionable insights about revenue performance.",
            "expenses": "You are a finance expert specializing in expense analysis. Focus on cost management and variance explanations.",
            "margin": "You are a finance expert specializing in profitability analysis. Explain margin trends and their business implications.",
            "cash": "You are a treasury expert specializing in cash flow analysis. Provide insights on liquidity and cash management.",
            "variance": "You are a finance expert specializing in variance analysis. Explain deviations from plan and prior year with business context."
        }

    def generate_narrative(self, kpi_results: List[KPIResult], query: KPIQuery) -> str:
        try:
            if not kpi_results:
                return "No data available for the requested KPIs."
            
            context = self._build_context(kpi_results, query)
            system_prompt = self._get_system_prompt(kpi_results[0])
            user_prompt = self._build_user_prompt(context, query)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            narrative = response.choices[0].message.content
            
            enhanced_narrative = self._enhance_with_insights(narrative, kpi_results)
            
            return enhanced_narrative
            
        except Exception as e:
            logger.error(f"Failed to generate narrative: {e}")
            return f"Unable to generate narrative summary. Error: {str(e)}"

    def _build_context(self, kpi_results: List[KPIResult], query: KPIQuery) -> Dict[str, Any]:
        context = {
            "query": query.query_text,
            "timestamp": datetime.now().isoformat(),
            "kpis": []
        }
        
        for result in kpi_results:
            kpi_context = {
                "name": result.name,
                "value": result.value,
                "unit": result.unit,
                "currency": result.currency,
                "time_period": result.time_period,
                "variance_py": result.variance_py,
                "variance_plan": result.variance_plan,
                "variance_fx_neutral": result.variance_fx_neutral,
                "metadata": result.metadata
            }
            context["kpis"].append(kpi_context)
        
        return context

    def _get_system_prompt(self, kpi_result: KPIResult) -> str:
        category = self._determine_category(kpi_result.name)
        return self.system_prompts.get(category, self.system_prompts["variance"])

    def _determine_category(self, kpi_name: str) -> str:
        name_lower = kpi_name.lower()
        
        if any(keyword in name_lower for keyword in ["revenue", "sales", "income"]):
            return "revenue"
        elif any(keyword in name_lower for keyword in ["expense", "cost", "opex"]):
            return "expenses"
        elif any(keyword in name_lower for keyword in ["margin", "profitability"]):
            return "margin"
        elif any(keyword in name_lower for keyword in ["cash", "liquidity"]):
            return "cash"
        else:
            return "variance"

    def _build_user_prompt(self, context: Dict[str, Any], query: KPIQuery) -> str:
        prompt = f"""
        Analyze the following KPI data and provide a concise narrative summary:

        User Query: "{context['query']}"
        
        KPI Results:
        """
        
        for kpi in context["kpis"]:
            prompt += f"""
        - {kpi['name']}: {kpi['value']:,.2f} {kpi['unit']} ({kpi['currency'] or ''})
          Time Period: {kpi['time_period']}
          """
            
            if kpi['variance_py'] is not None:
                prompt += f"Prior Year Variance: {kpi['variance_py']:,.2f}\n          "
            
            if kpi['variance_plan'] is not None:
                prompt += f"Plan Variance: {kpi['variance_plan']:,.2f}\n          "
            
            if kpi['variance_fx_neutral'] is not None:
                prompt += f"FX Neutral Variance: {kpi['variance_fx_neutral']:,.2f}\n          "
        
        prompt += """
        
        Please provide:
        1. A concise summary of the key metrics
        2. Analysis of any significant variances
        3. Business implications and potential causes
        4. Actionable insights where appropriate
        
        Keep the response under 200 words and use clear, business-friendly language.
        """
        
        return prompt

    def _enhance_with_insights(self, narrative: str, kpi_results: List[KPIResult]) -> str:
        insights = []
        
        for result in kpi_results:
            if result.variance_py and abs(result.variance_py) > result.value * 0.1:
                if result.variance_py > 0:
                    insights.append(f"📈 {result.name} increased significantly vs. prior year")
                else:
                    insights.append(f"📉 {result.name} declined significantly vs. prior year")
            
            if result.variance_plan and abs(result.variance_plan) > result.value * 0.05:
                if result.variance_plan > 0:
                    insights.append(f"⚠️ {result.name} is above plan")
                else:
                    insights.append(f"✅ {result.name} is below plan")
        
        if insights:
            insight_text = "\n\n**Key Insights:**\n" + "\n".join(insights)
            return narrative + insight_text
        
        return narrative

    def generate_suggestions(self, kpi_results: List[KPIResult], query: KPIQuery) -> List[str]:
        try:
            suggestions = []
            
            for result in kpi_results:
                if result.variance_py and abs(result.variance_py) > result.value * 0.1:
                    suggestions.append(f"Drill down into {result.name} by department")
                
                if result.variance_plan and abs(result.variance_plan) > result.value * 0.05:
                    suggestions.append(f"Compare {result.name} to industry benchmarks")
                
                if "margin" in result.name.lower():
                    suggestions.append(f"Analyze cost drivers affecting {result.name}")
                
                if "cash" in result.name.lower():
                    suggestions.append(f"Review cash flow forecast for {result.name}")
            
            general_suggestions = [
                "View quarterly trends for this KPI",
                "Compare with peer companies",
                "Set up automated alerts for significant changes"
            ]
            
            suggestions.extend(general_suggestions[:3 - len(suggestions)])
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return ["Ask about quarterly trends", "Request department breakdown", "Set up alerts"]

    def generate_alert_summary(self, kpi_results: List[KPIResult], threshold_breaches: List[Dict[str, Any]]) -> str:
        try:
            if not threshold_breaches:
                return "All KPIs are within normal ranges."
            
            prompt = f"""
            Generate a concise alert summary for the following KPI threshold breaches:
            
            Breaches:
            """
            
            for breach in threshold_breaches:
                prompt += f"""
            - {breach['kpi_name']}: {breach['actual_value']:,.2f} (Threshold: {breach['threshold']:,.2f})
              Severity: {breach['severity']}
              """
            
            prompt += """
            
            Provide a brief summary highlighting:
            1. Most critical breaches
            2. Potential business impact
            3. Recommended immediate actions
            
            Keep under 150 words.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business intelligence assistant focused on alert summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate alert summary: {e}")
            return "Multiple KPI thresholds have been breached. Please review individual alerts."

    def generate_trend_analysis(self, historical_data: List[Dict[str, Any]], kpi_name: str) -> str:
        try:
            prompt = f"""
            Analyze the following historical trend data for {kpi_name}:
            
            Historical Data:
            """
            
            for data_point in historical_data:
                prompt += f"- {data_point['period']}: {data_point['value']:,.2f}\n"
            
            prompt += """
            
            Provide:
            1. Trend direction and pattern
            2. Seasonality observations
            3. Notable inflection points
            4. Forecast implications
            
            Keep under 200 words.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in trend analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {e}")
            return f"Unable to analyze trends for {kpi_name}."