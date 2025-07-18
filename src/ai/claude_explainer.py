import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from anthropic import Anthropic
from ..config import settings
from ..models.schemas import Alert, AlertSummary
from ..rules.engine import RuleResult, RuleType

logger = logging.getLogger(__name__)

class ClaudeExplainer:
    """Uses Claude AI to generate explanations and risk assessments for alerts"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.claude_api_key)
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 1000
        self.temperature = 0.3
        
    async def explain_alert(self, alert: Alert, rule_result: RuleResult, context_data: Dict[str, Any]) -> AlertSummary:
        """Generate comprehensive explanation for an alert"""
        try:
            prompt = self._build_explanation_prompt(alert, rule_result, context_data)
            
            response = await self._call_claude(prompt)
            
            return self._parse_explanation_response(alert.id, response)
            
        except Exception as e:
            logger.error(f"Error generating explanation for alert {alert.id}: {str(e)}")
            return self._create_fallback_explanation(alert.id, str(e))
            
    async def explain_multiple_alerts(self, alerts_data: List[Dict[str, Any]]) -> List[AlertSummary]:
        """Generate explanations for multiple alerts efficiently"""
        tasks = []
        
        for alert_data in alerts_data:
            task = self.explain_alert(
                alert_data['alert'],
                alert_data['rule_result'],
                alert_data['context']
            )
            tasks.append(task)
            
        return await asyncio.gather(*tasks, return_exceptions=True)
        
    def _build_explanation_prompt(self, alert: Alert, rule_result: RuleResult, context_data: Dict[str, Any]) -> str:
        """Build prompt for Claude based on alert type and context"""
        
        base_prompt = f"""
Você é um especialista em auditoria fiscal municipal analisando gastos públicos de Capivari/SP. 
Analise o seguinte alerta de anomalia e forneça uma explicação completa e acessível.

INFORMAÇÕES DO ALERTA:
- Tipo de regra: {alert.rule_type}
- Título: {alert.title}
- Descrição: {alert.description}
- Score de risco: {alert.risk_score}/10
- Registros afetados: {len(alert.affected_records)}

EVIDÊNCIAS TÉCNICAS:
{json.dumps(rule_result.evidence, indent=2, ensure_ascii=False)}

CONTEXTO ADICIONAL:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Por favor, forneça uma resposta estruturada com:

1. RESUMO EXECUTIVO:
   - Explicação clara e concisa do problema encontrado
   - Gravidade e impacto potencial

2. EXPLICAÇÃO PARA CIDADÃOS:
   - Linguagem simples e acessível
   - Contexto sobre por que isso é importante para a cidade
   - Possíveis implicações financeiras

3. AVALIAÇÃO DE RISCO:
   - Justificativa para o score de risco atribuído
   - Fatores que influenciaram a classificação
   - Comparação com casos similares

4. AÇÕES RECOMENDADAS:
   - Passos específicos para investigação
   - Medidas preventivas sugeridas
   - Prioridade de ação

Seja objetivo, factual e mantenha um tom profissional mas acessível.
"""
        
        # Add rule-specific context
        if rule_result.rule_type == RuleType.OVERPRICING:
            base_prompt += self._get_overpricing_context()
        elif rule_result.rule_type == RuleType.SPLIT_ORDERS:
            base_prompt += self._get_split_orders_context()
        elif rule_result.rule_type == RuleType.SUPPLIER_CONCENTRATION:
            base_prompt += self._get_supplier_concentration_context()
        elif rule_result.rule_type == RuleType.RECURRING_EMERGENCY:
            base_prompt += self._get_recurring_emergency_context()
        elif rule_result.rule_type == RuleType.PAYROLL_ANOMALY:
            base_prompt += self._get_payroll_anomaly_context()
            
        return base_prompt
        
    def _get_overpricing_context(self) -> str:
        return """
        
CONTEXTO ESPECÍFICO - SOBREPREÇO:
- Sobrepreço indica possível superfaturamento em compras públicas
- Pode representar desperdício de recursos ou corrupção
- Impacto direto no orçamento municipal e nos serviços públicos
- Lei 8.666/93 exige pesquisa de preços para garantir economicidade
"""

    def _get_split_orders_context(self) -> str:
        return """
        
CONTEXTO ESPECÍFICO - FRACIONAMENTO:
- Fracionamento de despesas pode burlar limites de licitação
- Prática ilegal que visa evitar procedimentos licitatórios
- Pode indicar direcionamento de contratos ou corrupção
- Lei 8.666/93 proíbe fracionamento para fugir de licitação
"""

    def _get_supplier_concentration_context(self) -> str:
        return """
        
CONTEXTO ESPECÍFICO - CONCENTRAÇÃO DE FORNECEDORES:
- Concentração excessiva reduz competitividade
- Pode indicar direcionamento ou conluio entre fornecedores
- Aumenta riscos de dependência e inflação de preços
- Contratos públicos devem promover ampla concorrência
"""

    def _get_recurring_emergency_context(self) -> str:
        return """
        
CONTEXTO ESPECÍFICO - EMERGÊNCIAS RECORRENTES:
- Emergências frequentes podem indicar má gestão ou simulação
- Dispensa de licitação para emergências deve ser excepcional
- Pode mascarar direcionamento de contratos
- Lei 8.666/93 permite dispensa apenas em casos reais de emergência
"""

    def _get_payroll_anomaly_context(self) -> str:
        return """
        
CONTEXTO ESPECÍFICO - ANOMALIAS NA FOLHA:
- Discrepâncias salariais podem indicar privilégios irregulares
- Pagamentos atípicos requerem justificativa legal
- Transparência na folha é fundamental para controle social
- Lei de Responsabilidade Fiscal limita gastos com pessoal
"""

    async def _call_claude(self, prompt: str) -> str:
        """Make API call to Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            raise
            
    def _parse_explanation_response(self, alert_id: str, response: str) -> AlertSummary:
        """Parse Claude's response into structured format"""
        try:
            # Extract sections using regex
            sections = {
                'summary': self._extract_section(response, "RESUMO EXECUTIVO"),
                'citizen_explanation': self._extract_section(response, "EXPLICAÇÃO PARA CIDADÃOS"),
                'risk_assessment': self._extract_section(response, "AVALIAÇÃO DE RISCO"),
                'recommended_actions': self._extract_actions(response)
            }
            
            return AlertSummary(
                alert_id=alert_id,
                summary=sections['summary'] or "Anomalia detectada nos dados fiscais",
                citizen_explanation=sections['citizen_explanation'] or "Foram identificadas irregularidades que requerem investigação",
                risk_assessment=sections['risk_assessment'] or "Risco moderado identificado",
                recommended_actions=sections['recommended_actions'] or ["Investigar registros afetados", "Solicitar documentação adicional"]
            )
            
        except Exception as e:
            logger.error(f"Error parsing Claude response: {str(e)}")
            return self._create_fallback_explanation(alert_id, str(e))
            
    def _extract_section(self, text: str, section_title: str) -> str:
        """Extract a specific section from the response"""
        pattern = rf"{section_title}:?\s*\n(.*?)(?=\n\d+\.|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            # Clean up formatting
            content = re.sub(r'\n\s*-\s*', '\n• ', content)
            return content
            
        return ""
        
    def _extract_actions(self, text: str) -> List[str]:
        """Extract recommended actions as a list"""
        actions_section = self._extract_section(text, "AÇÕES RECOMENDADAS")
        
        if not actions_section:
            return ["Investigar registros afetados", "Solicitar documentação adicional"]
            
        # Split by bullet points or numbered items
        actions = re.split(r'\n\s*[-•\d]+\.?\s*', actions_section)
        actions = [action.strip() for action in actions if action.strip()]
        
        return actions[:5]  # Limit to 5 actions
        
    def _create_fallback_explanation(self, alert_id: str, error_msg: str) -> AlertSummary:
        """Create fallback explanation when AI fails"""
        return AlertSummary(
            alert_id=alert_id,
            summary="Anomalia detectada nos dados fiscais que requer investigação",
            citizen_explanation="Foram identificadas irregularidades nos gastos públicos que podem representar desperdício de recursos ou práticas inadequadas. É importante investigar para garantir o uso correto do dinheiro público.",
            risk_assessment="Risco moderado identificado. A análise automatizada detectou padrões que desviam do comportamento normal esperado.",
            recommended_actions=[
                "Investigar os registros afetados",
                "Solicitar documentação adicional",
                "Verificar conformidade com a legislação",
                "Consultar especialista em auditoria se necessário"
            ]
        )
        
    async def generate_digest_summary(self, alerts: List[Alert]) -> str:
        """Generate a summary for weekly digest"""
        if not alerts:
            return "Nenhum alerta foi gerado nesta semana."
            
        prompt = f"""
Você é um especialista em auditoria fiscal municipal. Crie um resumo semanal dos alertas de anomalias fiscais de Capivari/SP.

ALERTAS DA SEMANA ({len(alerts)} total):
"""
        
        # Group alerts by type
        alert_groups = {}
        for alert in alerts:
            rule_type = alert.rule_type
            if rule_type not in alert_groups:
                alert_groups[rule_type] = []
            alert_groups[rule_type].append(alert)
            
        for rule_type, group_alerts in alert_groups.items():
            prompt += f"\n{rule_type.upper()}: {len(group_alerts)} alertas"
            
        prompt += """

Por favor, crie um resumo executivo que inclua:

1. PANORAMA GERAL:
   - Quantidade total de alertas
   - Tipos de anomalias mais frequentes
   - Tendências observadas

2. PRINCIPAIS PREOCUPAÇÕES:
   - Alertas de maior risco
   - Impacto potencial no orçamento
   - Áreas que requerem atenção imediata

3. RECOMENDAÇÕES:
   - Prioridades de investigação
   - Medidas preventivas
   - Próximos passos

Mantenha o tom profissional e acessível para gestores públicos.
"""
        
        try:
            response = await self._call_claude(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating digest summary: {str(e)}")
            return f"Resumo automático: {len(alerts)} alertas foram gerados nesta semana, incluindo {len(alert_groups)} tipos diferentes de anomalias. Recomenda-se revisar todos os alertas para identificar possíveis irregularidades."
            
    async def explain_data_quality(self, quality_metrics: Dict[str, Any]) -> str:
        """Generate explanation for data quality issues"""
        prompt = f"""
Analise as seguintes métricas de qualidade dos dados fiscais de Capivari/SP:

MÉTRICAS DE QUALIDADE:
{json.dumps(quality_metrics, indent=2, ensure_ascii=False)}

Forneça uma explicação em português sobre:
1. Estado geral da qualidade dos dados
2. Principais problemas identificados
3. Impacto na confiabilidade das análises
4. Recomendações para melhoria

Seja conciso e focado nas implicações práticas.
"""
        
        try:
            response = await self._call_claude(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error explaining data quality: {str(e)}")
            return "Não foi possível gerar explicação sobre a qualidade dos dados neste momento."
            
    def get_risk_score_explanation(self, rule_type: RuleType, score: int, evidence: Dict[str, Any]) -> str:
        """Generate explanation for risk score"""
        explanations = {
            RuleType.OVERPRICING: f"Score {score}/10: Baseado no nível de sobrepreço detectado e quantidade de itens afetados",
            RuleType.SPLIT_ORDERS: f"Score {score}/10: Baseado no número de casos suspeitos de fracionamento detectados",
            RuleType.SUPPLIER_CONCENTRATION: f"Score {score}/10: Baseado no nível de concentração de fornecedores",
            RuleType.RECURRING_EMERGENCY: f"Score {score}/10: Baseado na frequência de emergências do mesmo fornecedor",
            RuleType.PAYROLL_ANOMALY: f"Score {score}/10: Baseado na magnitude dos desvios salariais detectados"
        }
        
        return explanations.get(rule_type, f"Score {score}/10: Risco calculado com base nos padrões identificados")
        
    async def batch_process_alerts(self, alerts_batch: List[Dict[str, Any]], batch_size: int = 5) -> List[AlertSummary]:
        """Process alerts in batches to avoid rate limits"""
        results = []
        
        for i in range(0, len(alerts_batch), batch_size):
            batch = alerts_batch[i:i + batch_size]
            
            # Process batch
            batch_results = await self.explain_multiple_alerts(batch)
            results.extend(batch_results)
            
            # Rate limiting pause
            if i + batch_size < len(alerts_batch):
                await asyncio.sleep(1)
                
        return results