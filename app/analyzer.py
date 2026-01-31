import os
import json
import logging
from typing import Dict, Optional
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoAnalyzer:
    CANDIDATE_MODELS = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash",
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key missing")
        self.client = genai.Client(api_key=self.api_key)

    def analyze_market_health(self, data: Dict) -> Optional[Dict]:
        if not data:
            return None

        prompt = f"""
        Você é um Analista de Inteligência Cripto. Sua tarefa é gerar um relatório segregado baseando-se em 3 fontes distintas.

        === FONTE 1: DADOS MATEMÁTICOS (Top Gainers & Losers) ===
        {json.dumps(data.get('market_movements'), ensure_ascii=False)}

        === FONTE 2: MÍDIA E NOTÍCIAS (Fatos) ===
        {json.dumps(data.get('latest_news'), ensure_ascii=False)}

        === FONTE 3: SENTIMENTO SOCIAL (Voz da Comunidade) ===
        {json.dumps(data.get('community_posts'), ensure_ascii=False)}

        --- INSTRUÇÃO DE RESPOSTA ---
        Gere um JSON com chaves separadas para cada análise. Não misture as análises.

        {{
            "1_gainers_losers_analysis": {{
                "highlight_gainer": {{ "coin": "Nome", "percentage": "%", "reason_hypothesis": "Por que subiu?" }},
                "highlight_loser": {{ "coin": "Nome", "percentage": "%", "reason_hypothesis": "Por que caiu?" }},
                "pattern_detected": "Ex: Moedas de IA estão subindo em bloco / Memecoins estão sangrando."
            }},

            "2_news_intelligence": [
                {{
                    "headline": "Título da Notícia Real",
                    "summary": "Resumo de 1 linha",
                    "importance": "High/Medium",
                    "affected_coins": ["BTC", "ETH", etc]
                }}
                // Liste as 5 notícias mais importantes
            ],

            "3_community_sentiment": {{
                "overall_mood": "Fear / Neutral / Greed",
                "hot_topics": ["O que estão discutindo? ex: Preço do BTC, Scam, Lua"],
                "retail_perception": "O investidor de varejo está comprando ou vendendo em pânico?"
            }},

            "4_final_conclusion": "Resumo estratégico unindo os 3 pontos acima."
        }}
        """

        for model in self.CANDIDATE_MODELS:
            try:
                logger.info(f"Analisando com {model}...")
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Erro no modelo {model}: {e}")
                continue
        return None
