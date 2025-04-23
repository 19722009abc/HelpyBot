import discord
from discord.ext import commands
import google.generativeai as genai
import re

genai.configure(api_key="AIzaSyCv3TjOZfLvuylSnl5oa8GaDXWNnXNIn8g")

model = genai.GenerativeModel(
    'models/gemini-1.5-flash-001',
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

def gerar_texto(tema_text):
    prompt = f"Crie um texto para o tema '{tema_text}'."
    response = model.generate_content(prompt)
    generated_text = response.text
    generated_text = re.sub(r'\b(?:embed|cor):', '', generated_text, flags=re.IGNORECASE).strip()
    return generated_text

class Ia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ia')
    async def ia(self, ctx, *, tema: str = None):
        if not tema:
            return await ctx.reply("❌ | Você precisa informar um tema!\n`Exemplo: ..ia universo`")

        await ctx.reply("🧠 | Gerando texto... Isso pode levar alguns segundos.")
        try:
            texto_gerado = gerar_texto(tema)
            embed = discord.Embed(
                title=f"Tema: {tema}",
                description=texto_gerado,
                color=discord.Color.blurple()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.reply(f"⚠️ | Ocorreu um erro ao gerar o texto: `{e}`")

async def setup(bot):
    await bot.add_cog(Ia(bot))

