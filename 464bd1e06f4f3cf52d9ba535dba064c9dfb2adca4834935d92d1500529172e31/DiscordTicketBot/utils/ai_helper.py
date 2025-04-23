import os
import logging
import json
import google.generativeai as genai
from typing import Dict, Any

logger = logging.getLogger('discord_bot.ai_helper')

GEMINI_API_KEY = "AIzaSyCv3TjOZfLvuylSnl5oa8GaDXWNnXNIn8g"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY não configurada. Recursos de IA desativados.")

GEN_CONFIG = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

class AIAssistant:
    def __init__(self):
        self.available = GEMINI_API_KEY is not None
        if self.available:
            try:
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash-001",
                    generation_config=GEN_CONFIG,
                    safety_settings=DEFAULT_SAFETY_SETTINGS
                )
                logger.info("AI Assistant initialized successfully with Gemini")
            except Exception as e:
                logger.error(f"Failed to initialize AI Assistant: {e}")
                self.available = False

    async def generate_channel_suggestion(self, guild_name: str, description: str = "") -> Dict[str, Any]:
        if not self.available:
            return {"error": "AI Service não disponível"}

        try:
            prompt = f"""Você é uma IA especializada em criar estruturas de servidor Discord.

            Crie uma estrutura completa e criativa para um servidor Discord chamado "{guild_name}".
            Tema/Foco do servidor: {description}

            Regras:
            1. Analise o tema e crie uma estrutura que faça sentido
            2. Use emojis criativos e relevantes
            3. Crie categorias e canais que façam sentido para o tema
            4. Inclua mensagens de boas-vindas e regras personalizadas
            5. Seja criativo e inovador!

            Retorne a estrutura em formato JSON com:
            - categories: lista de categorias
              - name: nome da categoria
              - channels: lista de canais
                - name: nome do canal (com emoji)
                - type: "texto" ou "voz"
                - description: descrição do canal
                - default_message: mensagem padrão (opcional)
            """

            response = self.model.generate_content(prompt)
            response_text = response.text

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            clean_text = response_text.strip().replace("'", '"')
            if not clean_text.startswith("{"):
                clean_text = "{" + clean_text.split("{", 1)[1]
            if not clean_text.endswith("}"):
                clean_text = clean_text.split("}", 1)[0] + "}"

            result = json.loads(clean_text)

            if "categories" not in result:
                raise ValueError("JSON não contém a chave 'categories'")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {"error": "Erro ao processar resposta da IA"}
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return {"error": f"Erro ao gerar sugestões: {str(e)}"}

    def _get_fallback_suggestions(self, guild_name: str, description: str = "") -> Dict[str, Any]:
        fallback = {
            "categories": [
                {
                    "name": "INFORMAÇÕES",
                    "channels": [
                        {
                            "name": "👋 boas-vindas",
                            "type": "texto",
                            "description": "Canal de boas-vindas",
                            "default_message": f"# 👋 Bem-vindo(a) ao {guild_name}!\n\n**Estamos felizes em ter você aqui!**"
                        },
                        {
                            "name": "📜 regras",
                            "type": "texto",
                            "description": "Regras do servidor",
                            "default_message": "# 📜 Regras\n\n1. Respeite todos\n2. Não faça spam\n3. Divirta-se!"
                        }
                    ]
                },
                {
                    "name": "GERAL",
                    "channels": [
                        {
                            "name": "💬 chat-geral",
                            "type": "texto",
                            "description": "Chat principal"
                        },
                        {
                            "name": "🔊 voz-geral",
                            "type": "voz",
                            "description": "Canal de voz"
                        }
                    ]
                }
            ]
        }

        if description:
            fallback["categories"].append({
                "name": description.split()[0].upper(),
                "channels": [
                    {"name": "💬 chat-tema", "type": "texto", "description": f"Chat sobre {description}"},
                    {"name": "🔊 voz-tema", "type": "voz", "description": f"Canal de voz para {description}"}
                ]
            })

        return fallback

async def enviar_mensagem_em_partes(interaction, content: str):
    partes = [content[i:i+2000] for i in range(0, len(content), 2000)]
    await interaction.followup.send(partes[0], ephemeral=True)
    for parte in partes[1:]:
        await interaction.followup.send(parte, ephemeral=True)



