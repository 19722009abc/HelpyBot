import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from typing import Optional, List, Dict, Union, Any

from utils.emoji_config import Emoji
from utils.storage import ChannelStorage, import_time
from utils.permissions import PermissionManager
import datetime
import os

logger = logging.getLogger('discord_bot.channel_manager')

class ChannelEditModal(discord.ui.Modal):
    """Modal for editing a channel."""
    
    def __init__(self, channel_name: str, channel_desc: str = ""):
        super().__init__(title="Editar Canal")
        self.name = discord.ui.TextInput(
            label="Nome do canal",
            placeholder="ex: bate-papo",
            default=channel_name,
            max_length=100
        )
        self.add_item(self.name)
        
        self.description = discord.ui.TextInput(
            label="Descrição do canal",
            placeholder="ex: Um canal para conversas gerais",
            style=discord.TextStyle.paragraph,
            required=False,
            default=channel_desc
        )
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        # This will be handled by the callback that calls this modal
        pass

class CategoryEditModal(discord.ui.Modal):
    """Modal for editing a category."""
    
    def __init__(self, category_name: str):
        super().__init__(title="Editar Categoria")
        self.name = discord.ui.TextInput(
            label="Nome da categoria",
            placeholder="ex: Geral",
            default=category_name,
            max_length=100
        )
        self.add_item(self.name)
    
    async def on_submit(self, interaction: discord.Interaction):
        # This will be handled by the callback that calls this modal
        pass

class ModalCategoria(discord.ui.Modal):
    """Modal for creating a category."""
    
    def __init__(self):
        super().__init__(title="Criar Categoria")
        self.nome = discord.ui.TextInput(
            label="Nome da categoria", 
            placeholder="ex: Geral", 
            max_length=100
        )
        self.add_item(self.nome)

    async def on_submit(self, interaction: discord.Interaction):
        storage = ChannelStorage()
        guild_id = interaction.guild.id
        
        # Add category to storage
        category_id = storage.add_category(guild_id, self.nome.value)
        
        # Update the view
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(guild_id)
        )

class ModalCanal(discord.ui.Modal):
    """Modal for creating a channel."""
    
    def __init__(self, tipo: str, category_id: Optional[str] = None):
        super().__init__(title="Criar Canal")
        self.tipo = tipo
        self.category_id = category_id
        
        self.nome = discord.ui.TextInput(
            label="Nome do canal", 
            placeholder="ex: bate-papo", 
            max_length=100
        )
        self.add_item(self.nome)
        
        self.descricao = discord.ui.TextInput(
            label="Descrição do canal", 
            placeholder="ex: Um canal para conversas gerais", 
            style=discord.TextStyle.paragraph, 
            required=False
        )
        self.add_item(self.descricao)

    async def on_submit(self, interaction: discord.Interaction):
        storage = ChannelStorage()
        guild_id = interaction.guild.id
        
        # Add channel to storage
        storage.add_channel(
            guild_id,
            self.nome.value,
            self.tipo,
            self.descricao.value,
            self.category_id
        )
        
        # Update the view
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(guild_id)
        )

class TipoCanalDropdown(discord.ui.Select):
    """Dropdown for selecting channel type."""
    
    def __init__(self, category_id: Optional[str] = None):
        options = [
            discord.SelectOption(label="Canal de Texto", value="texto", emoji="💬"),
            discord.SelectOption(label="Canal de Voz", value="voz", emoji="🔊"),
        ]
        super().__init__(placeholder="Escolha o tipo de canal", options=options, row=0)
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalCanal(self.values[0], self.category_id))

class ItemActionsView(discord.ui.View):
    """View with actions for selected channel or category."""
    
    def __init__(self, item_id: str, item_type: str, guild_id: str):
        super().__init__(timeout=60)
        self.item_id = item_id
        self.item_type = item_type  # "channel" or "category"
        self.guild_id = guild_id
        self.storage = ChannelStorage()
        self.permission_manager = PermissionManager()
    
    @discord.ui.button(label="Editar", style=discord.ButtonStyle.primary, emoji=Emoji.EDIT)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.item_type == "channel":
            channel = self.storage.get_channel(self.guild_id, self.item_id)
            if channel:
                modal = ChannelEditModal(channel["name"], channel.get("description", ""))
                
                async def on_modal_submit(modal_interaction):
                    # Update the channel
                    self.storage.update_channel(
                        self.guild_id, 
                        self.item_id, 
                        modal.name.value, 
                        modal.description.value
                    )
                    
                    await modal_interaction.response.edit_message(
                        content="> 🎨 **Painel de Personalização de Canais**\n"
                                "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                                "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
                        view=PersonalizaçãoView(self.guild_id)
                    )
                
                modal.on_submit = on_modal_submit
                await interaction.response.send_modal(modal)
        else:  # category
            category = self.storage.get_category(self.guild_id, self.item_id)
            if category:
                modal = CategoryEditModal(category["name"])
                
                async def on_modal_submit(modal_interaction):
                    # Update the category
                    self.storage.update_category(
                        self.guild_id, 
                        self.item_id, 
                        modal.name.value
                    )
                    
                    await modal_interaction.response.edit_message(
                        content="> 🎨 **Painel de Personalização de Canais**\n"
                                "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                                "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
                        view=PersonalizaçãoView(self.guild_id)
                    )
                
                modal.on_submit = on_modal_submit
                await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Configurar Permissões", style=discord.ButtonStyle.primary, emoji=Emoji.LOCK)
    async def permissions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        permissions = self.permission_manager.get_permissions(
            self.guild_id, 
            self.item_id, 
            self.item_type
        )
        
        await interaction.response.edit_message(
            content="> 🔒 **Configuração de Permissões**\n"
                    "> Selecione as permissões abaixo para configurar o acesso ao canal/categoria.\n",
            view=PermissionView(self.guild_id, self.item_id, self.item_type, permissions)
        )
    
    @discord.ui.button(label="Excluir", style=discord.ButtonStyle.danger, emoji=Emoji.DELETE)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Delete the item
        if self.item_type == "channel":
            self.storage.delete_channel(self.guild_id, self.item_id)
        else:  # category
            self.storage.delete_category(self.guild_id, self.item_id)
        
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(self.guild_id)
        )

class PermissionCheckbox(discord.ui.Select):
    """Dropdown for selecting permissions."""
    
    def __init__(self, permissions: List[Dict[str, Any]]):
        options = []
        for perm in permissions:
            options.append(
                discord.SelectOption(
                    label=perm["name"],
                    value=perm["id"],
                    emoji="✅" if perm["enabled"] else "❌",
                    default=perm["enabled"]
                )
            )
        
        super().__init__(
            placeholder="Selecione as permissões",
            options=options,
            min_values=0,
            max_values=len(options),
            row=0
        )
        self.permissions = {perm["id"]: perm for perm in permissions}
    
    async def callback(self, interaction: discord.Interaction):
        # This will be handled by the submit button
        await interaction.response.defer()

class PermissionView(discord.ui.View):
    """View for configuring permissions."""
    
    def __init__(self, guild_id: str, item_id: str, item_type: str, permissions: List[Dict[str, Any]]):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.item_id = item_id
        self.item_type = item_type
        self.permission_manager = PermissionManager()
        
        self.permission_select = PermissionCheckbox(permissions)
        self.add_item(self.permission_select)
    
    @discord.ui.button(label="Salvar Permissões", style=discord.ButtonStyle.success, emoji="💾", row=1)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update permissions based on selected values
        selected_permissions = self.permission_select.values
        
        # Update permissions in storage
        for perm_id, perm in self.permission_select.permissions.items():
            enabled = perm_id in selected_permissions
            self.permission_manager.set_permission(
                self.guild_id,
                self.item_id,
                self.item_type,
                perm_id,
                enabled
            )
        
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(self.guild_id)
        )
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌", row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(self.guild_id)
        )

class MeuDropdown(discord.ui.Select):
    """Dropdown for selecting created items."""
    
    def __init__(self, guild_id: str):
        self.storage = ChannelStorage()
        self.guild_id = guild_id
        
        # Get all items from storage
        categories = self.storage.get_all_categories(guild_id)
        channels = self.storage.get_all_channels(guild_id)
        
        opcoes = []
        for cat in categories:
            opcoes.append(
                discord.SelectOption(
                    label=cat["name"],
                    value=f"category:{cat['id']}",
                    emoji="📁"
                )
            )
        
        for channel in channels:
            emoji = "💬" if channel["type"] == "texto" else "🔊"
            opcoes.append(
                discord.SelectOption(
                    label=channel["name"],
                    value=f"channel:{channel['id']}",
                    emoji=emoji
                )
            )
        
        if not opcoes:
            opcoes = [
                discord.SelectOption(label="Nada criado ainda", value="nada", emoji="🔍")
            ]
        
        super().__init__(placeholder="Itens criados aparecerão aqui", options=opcoes, row=1)
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "nada":
            await interaction.response.send_message("Nenhum item criado ainda. Crie uma categoria ou canal primeiro!", ephemeral=True)
            return
        
        # Parse the value to get item type and ID
        item_type, item_id = self.values[0].split(":", 1)
        
        # Show actions for the selected item
        await interaction.response.edit_message(
            content=f"> 🔧 **Gerenciando {item_type.capitalize()}**\n"
                    f"> Selecione uma ação para este item abaixo.\n",
            view=ItemActionsView(item_id, item_type, self.guild_id)
        )

class TipoCanalView(discord.ui.View):
    """View for selecting channel type."""
    
    def __init__(self, category_id: Optional[str] = None):
        super().__init__(timeout=None)
        self.add_item(TipoCanalDropdown(category_id))
    
    @discord.ui.button(label="Voltar", style=discord.ButtonStyle.secondary, emoji="◀️", row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(interaction.guild.id)
        )

class PersonalizaçãoView(discord.ui.View):
    """Main view for channel customization."""
    
    def __init__(self, guild_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.add_item(MeuDropdown(guild_id))
    
    @discord.ui.button(label='Criar Canal', style=discord.ButtonStyle.blurple, emoji=Emoji.ADD, row=2)
    async def canaladd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="> Está na hora de configurar! Escolha abaixo o tipo de canal que você deseja criar — seja um espaço para bate-papos ou uma sala de voz para interações ao vivo.", 
            view=TipoCanalView()
        )
    
    @discord.ui.button(label='Criar Categoria', style=discord.ButtonStyle.blurple, emoji=Emoji.FOLDER, row=2)
    async def categoriaadd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCategoria())
        
    @discord.ui.button(label='Aplicar no Servidor', style=discord.ButtonStyle.success, emoji=Emoji.SAVE, row=3)
    async def aplicar_alteracoes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        
        storage = ChannelStorage()
        guild_id = self.guild_id
        guild = interaction.guild
        
        # Obter todas as categorias e canais armazenados
        categories = storage.get_all_categories(guild_id)
        
        # Informações para relatório
        categories_created = 0
        channels_created = 0
        
        try:
            # Criar categorias no Discord
            for category_data in categories:
                # Criar categoria no Discord
                category_name = category_data["name"]
                
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        add_reactions=True
                    )
                }
                
                discord_category = await guild.create_category(
                    name=category_name,
                    overwrites=overwrites
                )
                categories_created += 1
                
                # Obter canais dessa categoria
                channels = storage.get_all_channels(guild_id, category_data["id"])
                
                for channel_data in channels:
                    # Criar canal no Discord
                    channel_name = channel_data["name"]
                    channel_type = channel_data["type"]
                    
                    if channel_type == "texto":
                        await discord_category.create_text_channel(
                            name=channel_name,
                            topic=channel_data.get("description", "")
                        )
                    elif channel_type == "voz":
                        await discord_category.create_voice_channel(
                            name=channel_name
                        )
                    
                    channels_created += 1
            
            # Criar canais que não estão em categorias
            uncategorized_channels = storage.get_all_channels(guild_id, None)
            
            for channel_data in uncategorized_channels:
                channel_name = channel_data["name"]
                channel_type = channel_data["type"]
                
                if channel_type == "texto":
                    await guild.create_text_channel(
                        name=channel_name,
                        topic=channel_data.get("description", "")
                    )
                elif channel_type == "voz":
                    await guild.create_voice_channel(
                        name=channel_name
                    )
                
                channels_created += 1
            
            # Limpar dados armazenados após aplicar no servidor
            for category in categories:
                storage.delete_category(guild_id, category["id"])
            
            # Enviar relatório
            await interaction.followup.send(
                content=f"> {Emoji.SUCCESS} **Alterações Aplicadas com Sucesso!**\n"
                        f"> Foram criados no Discord:\n"
                        f"> - {categories_created} categorias\n"
                        f"> - {channels_created} canais\n\n"
                        f"> Os canais agora estão disponíveis no seu servidor!",
                ephemeral=True
            )
            
            # Retornar à visualização inicial
            await interaction.edit_original_response(
                content="> 🛠️ **Gerenciamento de Canais**\n"
                       "> Escolha uma das opções abaixo para gerenciar seu servidor.\n"
                       "> Tudo de forma rápida, segura e sem complicação! 😉",
                view=CanalView()
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                content=f"> {Emoji.ERROR} **Erro ao Aplicar Alterações**\n"
                        f"> O bot não tem permissões suficientes para criar canais neste servidor.\n"
                        f"> Verifique se o bot tem as permissões de 'Gerenciar Canais' e 'Gerenciar Servidor'.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                content=f"> {Emoji.ERROR} **Erro ao Aplicar Alterações**\n"
                        f"> Ocorreu um erro ao tentar criar os canais: {str(e)}",
                ephemeral=True
            )
    
    @discord.ui.button(label='Voltar', style=discord.ButtonStyle.secondary, emoji=Emoji.BACK, row=3)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Limpar dados armazenados para resolver o bug de persistência
        storage = ChannelStorage()
        guild_id = self.guild_id
        
        # Obter todas as categorias
        categories = storage.get_all_categories(guild_id)
        
        # Excluir todas as categorias e canais associados
        for category in categories:
            storage.delete_category(guild_id, category["id"])
        
        # Excluir canais não categorizados
        uncategorized_channels = storage.get_all_channels(guild_id, None)
        for channel in uncategorized_channels:
            storage.delete_channel(guild_id, channel["id"])
        
        await interaction.response.edit_message(
            content="> 🛠️ **Gerenciamento de Canais**\n"
                   "> Escolha uma das opções abaixo para gerenciar seu servidor.\n"
                   "> Tudo de forma rápida, segura e sem complicação! 😉",
            view=CanalView()
        )

import random

class DeleteChannelsModal(discord.ui.Modal):
    def __init__(self, codigo: str):
        super().__init__(title=f"⚠️ Código de Verificação: {codigo}")
        self.codigo = codigo
        self.confirmacao = discord.ui.TextInput(
            label=f"Código: {codigo}",
            placeholder="Ex: 12345",
            required=True,
            max_length=5
        )
        self.add_item(self.confirmacao)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmacao.value != self.codigo:
            await interaction.response.send_message(
                content=f"> {Emoji.ERROR} **Operação Cancelada**\n"
                        f"> O código digitado está incorreto.\n"
                        f"> Nenhum canal foi excluído.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        current_channel = interaction.channel
        total_canais = len(guild.channels) - 1
        excluidos = 0
        erro_canais = []

        try:
            for channel in guild.channels:
                if channel.id == current_channel.id:
                    continue
                try:
                    await channel.delete(reason=f"Solicitado por {interaction.user} (limpeza do servidor)")
                    excluidos += 1
                except Exception as e:
                    erro_canais.append(f"{channel.name} ({str(e)})")

            if excluidos == total_canais:
                await interaction.followup.send(
                    content=f"> {Emoji.SUCCESS} **Canais Excluídos com Sucesso!**\n"
                            f"> Todos os {excluidos} canais foram excluídos.\n"
                            f"> Apenas o canal atual foi mantido.",
                    ephemeral=True
                )
            else:
                erro_msg = "\n> ".join(erro_canais[:5])
                if len(erro_canais) > 5:
                    erro_msg += f"\n> ... e mais {len(erro_canais) - 5} canais com erro."
                await interaction.followup.send(
                    content=f"> {Emoji.WARNING} **Exclusão Parcial de Canais**\n"
                            f"> {excluidos} de {total_canais} canais foram excluídos.\n"
                            f"> Erros encontrados:\n> {erro_msg}",
                    ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(
                content=f"> {Emoji.ERROR} **Erro ao Excluir Canais**\n"
                        f"> Ocorreu um erro inesperado: {str(e)}",
                ephemeral=True
            )


class CanalView(discord.ui.View):
    """Initial view for channel management."""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Criar Canais", emoji=Emoji.ADD, style=discord.ButtonStyle.success)
    async def criar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="> 🎨 **Painel de Personalização de Canais**\n"
                    "> Aqui você pode criar **categorias** 📁 e **canais** para deixar seu servidor do jeitinho que quiser!\n"
                    "> Tudo o que for criado aparecerá logo abaixo, em tempo real.\n",
            view=PersonalizaçãoView(interaction.guild.id)
        )
    
    @discord.ui.button(label="Criar com IA", emoji=Emoji.IA, style=discord.ButtonStyle.primary)
    async def criar_com_ia(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.ai_assistant import AIChannelView
        await interaction.response.edit_message(
            content="> 🤖 **Criação de Canais com IA**\n"
                   "> Deixe nosso assistente inteligente sugerir uma estrutura de canais para seu servidor!\n"
                   "> Basta descrever o propósito do seu servidor e receber sugestões personalizadas.",
            view=AIChannelView()
        )
    
    @discord.ui.button(label="Excluir", emoji=Emoji.DELETE, style=discord.ButtonStyle.danger)
    async def excluir_canais(self, interaction: discord.Interaction, button: discord.ui.Button):
        codigo = ''.join(random.choices("0123456789", k=5))
        await interaction.response.send_modal(DeleteChannelsModal(codigo))


class Canal(commands.Cog):
    """Cog for channel management commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = {}  # Track active sessions by user
        
        # Limpar todos os arquivos temporários ao iniciar
        self._cleanup_all_temp_files()
        
    def _generate_session_id(self):
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _clear_guild_data(self, guild_id: str):
        """Clear data for guild and return True on success."""
        storage = ChannelStorage()
        success = storage.clear_guild_data(guild_id)
        return success
        
    def _cleanup_all_temp_files(self):
        """Limpar todos os arquivos temporários da pasta data."""
        try:
            storage_dir = "data"
            if not os.path.exists(storage_dir):
                return
                
            # Remover todos os arquivos de guild
            for filename in os.listdir(storage_dir):
                if filename.startswith("guild_") and filename.endswith(".json"):
                    file_path = os.path.join(storage_dir, filename)
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old data file: {filename}")
                    except Exception as e:
                        logger.error(f"Error removing file {filename}: {str(e)}")
                        
            logger.info("Cleaned up all temporary guild data files")
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
    
    @app_commands.command(name='criar-canal', description='Crie canais para o seu servidor')
    async def canais(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "> ❌ **Permissão Negada**\n"
                "> Você precisa ter permissão para gerenciar canais para usar este comando.",
                ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        session_id = self._generate_session_id()
        current_time = datetime.datetime.utcnow().isoformat()
        self.active_sessions[user_id] = {
            "guild_id": guild_id,
            "session_id": session_id,
            "start_time": current_time
        }

        self._clear_guild_data(guild_id)

        await interaction.response.defer(thinking=True, ephemeral=True)

        await interaction.followup.send(
            "> 🛠️ **Gerenciamento de Canais**\n"
            "> Escolha uma das opções abaixo para gerenciar seu servidor.\n"
            "> Tudo de forma rápida, segura e sem complicação! 😉",
            view=CanalView(),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Canal(bot))