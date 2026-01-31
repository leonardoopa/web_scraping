import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from app.scraper import CMCScraper
from app.analyzer import CryptoAnalyzer

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SystemOrchestrator")


async def main():
    print("\n" + "=" * 50)
    print("   SISTEMA DE INTELIGÊNCIA CRIPTO (CMC + GEMINI)   ")
    print("=" * 50 + "\n")

    # Scraping
    scraper = CMCScraper()
    try:
        raw_posts = await scraper.run(scroll_attempts=5, headless=True)
    except Exception as e:
        logger.critical(f"Falha no Scraping: {e}")
        return

    if not raw_posts:
        logger.warning("Nenhum dado coletado. Encerrando.")
        return

    print(f"\n✅ [Scraper] {len(raw_posts)} posts coletados. Iniciando IA...\n")

    # LLM
    try:
        analyzer = CryptoAnalyzer()
        insight_report = analyzer.analyze_market_sentiment(raw_posts)

        if insight_report:
            print("=" * 50)
            print("RELATÓRIO DE MERCADO - BITCOIN")
            print("=" * 50)
            # Imprime o JSON formatado e bonitinho
            print(json.dumps(insight_report, indent=4, ensure_ascii=False))
            print("=" * 50)

            # (Opcional) Salvar em arquivo para histórico
            with open("relatorio_btc.json", "w", encoding="utf-8") as f:
                json.dump(insight_report, f, indent=4, ensure_ascii=False)
                logger.info("Relatório salvo em 'relatorio_btc.json'")

    except ValueError as e:
        logger.error(f"Configuração da IA inválida: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado na análise: {e}")


if __name__ == "__main__":
    asyncio.run(main())
