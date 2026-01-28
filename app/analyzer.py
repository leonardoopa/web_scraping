import os
import json
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class CryptoAnalyzer:

    CANDIDATE_MODELS = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest",
        "models/gemini-3-flash-preview",
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self._configure_client()

    def _configure_client(self):
        if not self.api_key:
            raise ValueError("The Gemini API key (GEMINI_API_KEY) is required.")

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Error configuring Gemini client: {e}")
            raise

    def _build_prompt(self, posts: List[str]) -> str:
        return f"""
        Você é um Analista de Criptoativos Sênior.
        Analise estes posts da comunidade CoinMarketCap:
        {json.dumps(posts, ensure_ascii=False)}

        Tarefa:
        1. Identificar o sentimento predominante (Bullish/Bearish/Neutral).
        2. Calcular Score de confiança (0-100).
        3. Identificar 3 Tópicos Principais e seus impactos.

        Retorne APENAS um JSON com esta estrutura:
        {{
            "market_sentiment": "Bullish | Bearish | Neutral",
            "sentiment_score": 0,
            "top_insights": [
                {{ "topic": "Título Curto", "summary": "Resumo de 1 linha", "impact": "Positive|Negative" }}
            ],
            "conclusion": "Resumo executivo de 2 linhas."
        }}
        """

    def analyze_market_sentiment(self, posts: List[str]) -> Optional[Dict]:
        if not posts:
            return None

        prompt = self._build_prompt(posts)

        # Loop de tentativa (Retry com Fallback)
        for model in self.CANDIDATE_MODELS:
            logger.info(f"Trying to analyze with the model:'{model}'...")

            try:
                # Na nova SDK, response_mime_type ajuda a garantir JSON puro
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )

                if not response.text:
                    logger.warning(
                        f"Model '{model}' Returned an empty response. Trying next..."
                    )
                    continue

                parsed_result = json.loads(response.text)
                logger.info(f"Sucess, analysis performed by the model: {model}")
                return parsed_result

            except Exception as e:
                # Loga o erro mas não para o programa, tenta o próximo modelo da lista
                logger.warning(f"Model '{model}' failed or not found. Error: {e}")

        logger.error("All models failed. Check your API Key or quotas.")
        return None
