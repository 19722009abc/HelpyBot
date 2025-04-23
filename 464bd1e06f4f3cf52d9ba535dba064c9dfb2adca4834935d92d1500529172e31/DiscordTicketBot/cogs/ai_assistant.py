import discord
from discord.ext import commands
from typing import Dict, Any
import logging

from utils.ai_helper import AIAssistant
from utils.emoji_config import Emoji
from utils.storage import ChannelStorage
from cogs.channel_manager import CanalView

logger = logging.getLogger('discord_bot.ai_assistant')

async def enviar_mensagem_em_partes(interaction: discord.Interaction, texto: str):
    partes = [texto[i:i+1900] for i in range(0, len(texto), 1900)]
    # Envia a primeira parte
    await interaction.followup.send(content=partes[0], ephemeral=True)
    # Envia as demais partes
    for parte in partes[1:]:
        await interaction.followup.send(content=parte, ephemeral=True)


class DescriptionModal(discord.ui.Modal):
    def __init__(self, guild_name: str):
        super().__init__(title="Descreva seu servidor")
        self.guild_name = guild_name
        self.description = discord.ui.TextInput(
            label="O que seu servidor é sobre?",
            placeholder="ex: Comunidade de jogadores de RPG",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=500
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        pass

class AIChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Gerar com IA", emoji=Emoji.IA, style=discord.ButtonStyle.primary)
    async def generate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DescriptionModal(interaction.guild.name)

        async def on_modal_submit(modal_interaction):
            await modal_interaction.response.edit_message(
                content=f"> {Emoji.IA} **Gerando sugestões com IA...**\n"
                        f"> Estou analisando seu servidor e criando uma estrutura personalizada.\n"
                        f"> Isso pode levar alguns segundos...",
                view=None
            )

            ai_assistant = AIAssistant()
            suggestions = await ai_assistant.generate_channel_suggestion(
                interaction.guild.name,
                modal.description.value
            )

            if "error" in suggestions:
                await modal_interaction.edit_original_response(
                    content=f"> {Emoji.ERROR} **Erro na IA**\n"
                            f"> Não foi possível gerar sugestões: {suggestions['error']}\n"
                            f"> Tente novamente mais tarde.",
                    view=self
                )
                return

            content = f"> {Emoji.IA} **Sugestões de Canais Geradas por IA**\n"\
                      f"> Baseado na descrição: *{modal.description.value}*\n\n"

            for i, category in enumerate(suggestions.get("categories", [])):
                content += f"**{i+1}. {category['name']}**\n"
                for channel in category.get("channels", []):
                    emoji = Emoji.TEXT_CHANNEL if channel["type"] == "texto" else Emoji.VOICE_CHANNEL
                    content += f"  {emoji} {channel['name']} - {channel.get('description', '')}\n"
                content += "\n"

            implement_view = ImplementSuggestionsView(suggestions)
            await enviar_mensagem_em_partes(modal_interaction, content)
            await modal_interaction.followup.send(view=implement_view, ephemeral=True)

        modal.on_submit = on_modal_submit
        await interaction.response.send_modal(modal)

class ImplementSuggestionsView(discord.ui.View):
    def __init__(self, suggestions: Dict[str, Any]):
        super().__init__(timeout=180)
        self.suggestions = suggestions

    @discord.ui.button(label="Criar Canais no Discord", emoji=Emoji.CHECK, style=discord.ButtonStyle.success)
    async def implement_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        categories_created = 0
        channels_created = 0
        messages_sent = 0

        try:
            for category_data in self.suggestions.get("categories", []):
                category_name = category_data["name"]
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        add_reactions=True
                    ),
                    guild.me: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_channels=True,
                        manage_permissions=True
                    )
                }
                if guild.owner:
                    overwrites[guild.owner] = discord.PermissionOverwrite(administrator=True)
                discord_category = await guild.create_category(name=category_name, overwrites=overwrites)
                categories_created += 1

                for channel_data in category_data.get("channels", []):
                    channel_name = channel_data["name"]
                    channel_type = channel_data["type"]
                    channel_overwrites = overwrites.copy()
                    has_default_message = "default_message" in channel_data and channel_data["default_message"].strip()
                    special_channels = ["boas-vindas", "bem-vindo", "welcome", "regras", "rules", "informacoes", "information", "info", "anuncios", "announcements"]
                    is_special_channel = channel_type == "texto" and any(special in channel_name for special in special_channels)

                    if is_special_channel:
                        channel_overwrites[guild.default_role] = discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=False,
                            add_reactions=True
                        )

                    if channel_type == "texto":
                        created_channel = await discord_category.create_text_channel(
                            name=channel_name,
                            topic=channel_data.get("description", ""),
                            overwrites=channel_overwrites
                        )
                        if has_default_message:
                            try:
                                await created_channel.send(channel_data["default_message"])
                                messages_sent += 1
                            except Exception as e:
                                logger.error(f"Erro ao enviar mensagem padrão em {channel_name}: {e}")
                    elif channel_type == "voz":
                        channel_overwrites[guild.default_role].update(speak=True, connect=True, stream=True)
                        await discord_category.create_voice_channel(
                            name=channel_name,
                            overwrites=channel_overwrites
                        )
                    channels_created += 1

            await interaction.followup.send(
                content=f"> {Emoji.SUCCESS} **Servidor configurado com sucesso!**\n"
                        f"> Foram criados diretamente no seu servidor:\n"
                        f"> - {categories_created} categorias\n"
                        f"> - {channels_created} canais\n"
                        f"> - {messages_sent} mensagens automáticas\n\n"
                        f"> Os canais já estão disponíveis com permissões e conteúdo configurados!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                content=f"> {Emoji.ERROR} **Erro ao Criar Canais**\n"
                        f"> O bot não tem permissões suficientes para criar canais neste servidor.\n"
                        f"> Verifique se o bot tem as permissões de 'Gerenciar Canais' e 'Gerenciar Servidor'.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                content=f"> {Emoji.ERROR} **Erro ao Criar Canais**\n"
                        f"> Ocorreu um erro ao tentar criar os canais: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="Voltar", emoji=Emoji.BACK, style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="> 🛠️ **Gerenciamento de Canais**\n"
                    "> Escolha uma das opções abaixo para gerenciar seu servidor.\n"
                    "> Tudo de forma rápida, segura e sem complicação! 😉",
            view=CanalView()
        )

class AIAssistantCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_assistant = AIAssistant()
        logger.info("AI Assistant cog initialized and integrated with channel manager")

async def setup(bot):
    await bot.add_cog(AIAssistantCog(bot))
    logger.info("AI Assistant cog loaded")