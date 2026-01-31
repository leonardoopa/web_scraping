import asyncio
import json
import logging
from dotenv import load_dotenv
from app.scraper import CMCScraper
from app.analyzer import CryptoAnalyzer
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")


async def main():
    print("--- INICIANDO SCANNER DE MERCADO ---")

    scraper = CMCScraper()
    try:
        market_data = await scraper.run_comprehensive_scan(headless=True)
    except Exception as e:
        logger.critical(f"Erro no Scraper: {e}")
        return

    print(f"\n Dados Coletados:")
    print(
        f"- Gainers/Losers: {'Correto' if market_data['market_movements'] else 'Falha'}"
    )
    print(f"- Notícias: {len(market_data['latest_news'])} manchetes")
    print(f"- Posts Sociais: {len(market_data['community_posts'])} posts")

    analyzer = CryptoAnalyzer()
    print("\n Processando Inteligência de Mercado...")

    insight = analyzer.analyze_market_health(market_data)

    if insight:
        print("\n" + "=" * 50)
        print(" RELATÓRIO DE INTELIGÊNCIA CRIPTO")
        print("=" * 50)
        print(json.dumps(insight, indent=4, ensure_ascii=False))

        # Salva o arquivo
        with open("market_intelligence.json", "w", encoding="utf-8") as f:
            json.dump(insight, f, indent=4, ensure_ascii=False)
            print("\n Relatório salvo em 'market_intelligence.json'")
    else:
        print("Falha na análise da IA.")


if __name__ == "__main__":
    asyncio.run(main())
