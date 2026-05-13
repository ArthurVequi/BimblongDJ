import asyncio
from config import gemini_model



async def interpret_music_request(prompt):
    """Envia uma descrição vaga pro Gemini e recebe "Artista - Nome da Música".
    Retorna (search_query, None) em sucesso ou (None, erro) em falha."""
    if not gemini_model:
        return None, "⚠️ A Chave da API do Gemini não foi configurada. Coloque-a no arquivo `.env` para usar esse comando."

    try:
        ai_prompt = (
            f"O usuário está pedindo uma música com a seguinte descrição: '{prompt}'. "
            "Retorne APENAS o nome exato da música e o artista/banda para que eu possa "
            "pesquisar no YouTube. Não adicione nenhum outro texto, aspas, ou explicação."
        )
        response = await asyncio.to_thread(gemini_model.generate_content, ai_prompt)
        return response.text.strip(), None
    except Exception as e:
        return None, f"❌ Erro na IA: {e}"
