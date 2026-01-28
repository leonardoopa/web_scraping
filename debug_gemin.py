import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def listar_modelos():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    print(f"--- LISTA DE MODELOS DISPONÍVEIS ({api_key[:5]}...) ---")

    try:
        # Pega todos os modelos
        for m in client.models.list():
            if "gemini" in m.name and "flash" in m.name:
                print(f"✅ {m.name}")

    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    listar_modelos()
