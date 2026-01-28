import asyncio
import json
import logging
from dotenv import load_dotenv
from app.scraper import CMCScraper

load_dotenv()

logger = logging.getLogger(__name__)

async def main():
    print("--- INICIANDO SISTEMA DE MONITORAMENTO CRIPTO ---")
    
    try:
        scraper = CMCScraper()
        
        # headless=False para você ver o navegador abrindo (mude para True em produção)
        # scroll_attempts=5 garante uma boa quantidade de posts
        posts = await scraper.run(scroll_attempts=5, headless=False)
        
        print("\n" + "="*40)
        print(f"      RESULTADO: {len(posts)} POSTS COLETADOS      ")
        print("="*40)
        
        if not posts:
            logger.warning("Nenhum post foi coletado. Verifique os seletores ou a conexão.")
            return

        print("\n--- Amostra dos Dados (Top 10) ---")
        for i, post in enumerate(posts[:10]):
            # Corta textos muito longos para visualização no terminal
            preview = post[:150].replace('\n', ' ') 
            print(f"[{i+1}] {preview}...")
            print("-" * 20)
            
        # (Futuro) Aqui vou chamar o analyzer.analyze_posts(posts)

    except ValueError as e:
        logger.critical(f"Erro de configuração: {e}")
    except Exception as e:
        logger.critical(f"Erro inesperado no sistema: {e}")

if __name__ == "__main__":
    asyncio.run(main())