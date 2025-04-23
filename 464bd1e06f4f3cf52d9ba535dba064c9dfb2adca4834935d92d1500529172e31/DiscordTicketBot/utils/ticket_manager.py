import discord
import uuid
import logging
import json
import asyncio
from datetime import datetime
from typing import Optional, Union
from utils.config_manager import (
    get_panel_data, update_panel_data, create_panel_data,
    get_ticket_data, update_ticket_data, create_ticket_data,
    get_config, get_all_panels, delete_panel_data,
    initialize_edit_session, get_edit_session, update_edit_session
)
from utils.embed_creator import (
    create_config_embed, create_ticket_embed, create_panel_preview
)
from utils.emoji_config import Emoji

logger = logging.getLogger('ticket_bot.manager')

class TicketManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def create_panel_callback(self, interaction: discord.Interaction):
        """Callback for Create Panel button"""
        try:
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            
            # Create a new panel ID
            panel_id = str(uuid.uuid4())
            
            # Initialize edit session with default values
            panel_data = {
                "id": panel_id,
                "panel_id": panel_id,  # Adicionando o panel_id explicitamente 
                "panel_name": f"Painel #{panel_id[:8]}",  # Nome para identificação do painel
                "title": "Painel de Ticket",
                "description": "Clique no botão abaixo para abrir um ticket.",
                "color": "blue",
                "support_role_id": None,
                "category_id": None,
                "interaction_type": "button",
                "button_style": "primary",
                "button_emoji": "🎫",
                "button_text": "Abrir Ticket",
                "dropdown_placeholder": "Selecione uma opção",
                "dropdown_options": [],
                "ticket_name_format": "ticket-{number}",  # Formato padrão do nome do ticket
                "creator_id": user_id,
                "guild_id": guild_id,
                "created_at": datetime.now().isoformat()
            }
            
            initialize_edit_session(user_id, guild_id, panel_data)
            print(f"Panel data initialized with panel_id: {panel_id}")
            
            # Show the panel editor
            await self.show_panel_editor(interaction, panel_id, new_panel=True)
            
        except Exception as e:
            logger.error(f"Error in create_panel_callback: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao criar o painel: {e}",
                ephemeral=True
            )
    
    async def edit_panel_callback(self, interaction: discord.Interaction):
        """Callback for Edit Panel button"""
        try:
            guild_id = str(interaction.guild_id)
            
            # Get all panels for the guild
            panels = get_all_panels(guild_id)
            
            if not panels:
                await interaction.response.send_message(
                    "Não há painéis para editar neste servidor!",
                    ephemeral=True
                )
                return
            
            # Create dropdown to select panel
            view = discord.ui.View(timeout=300)
            
            # Create panel select
            select = discord.ui.Select(
                placeholder="Selecione um painel para editar",
                custom_id="edit_panel_select"
            )
            
            for panel_id, panel in panels.items():
                title = panel.get("title", "Painel sem título")
                panel_name = panel.get("panel_name", f"Painel #{panel_id[:8]}")
                created_at = panel.get("created_at", "Data desconhecida")
                
                select.add_option(
                    label=panel_name,
                    value=panel_id,
                    description=f"{title[:30]}... | Criado: {created_at[:10]}"
                )
            
            view.add_item(select)
            
            embed = create_config_embed(
                title="Editar Painel de Tickets",
                description="Selecione o painel que deseja editar na lista abaixo.",
                color=discord.Color.blue()
            )
            
            # Add a cancel button
            cancel_button = discord.ui.Button(
                label="Cancelar",
                style=discord.ButtonStyle.secondary,
                custom_id="cancel_edit"
            )
            cancel_button.callback = self.cancel_callback
            view.add_item(cancel_button)
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in edit_panel_callback: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao listar painéis para edição: {e}",
                ephemeral=True
            )
    
    async def delete_panel_callback(self, interaction: discord.Interaction):
        """Callback for Delete Panel button"""
        try:
            guild_id = str(interaction.guild_id)
            
            # Get all panels for the guild
            panels = get_all_panels(guild_id)
            
            if not panels:
                await interaction.response.send_message(
                    "Não há painéis para excluir neste servidor!",
                    ephemeral=True
                )
                return
            
            # Create dropdown to select panel
            view = discord.ui.View(timeout=300)
            
            # Create panel select
            select = discord.ui.Select(
                placeholder="Selecione um painel para excluir",
                custom_id="delete_panel_select"
            )
            
            for panel_id, panel in panels.items():
                title = panel.get("title", "Painel sem título")
                panel_name = panel.get("panel_name", f"Painel #{panel_id[:8]}")
                created_at = panel.get("created_at", "Data desconhecida")
                
                select.add_option(
                    label=panel_name,
                    value=panel_id,
                    description=f"{title[:30]}... | Criado: {created_at[:10]}"
                )
            
            view.add_item(select)
            
            embed = create_config_embed(
                title="Excluir Painel de Tickets",
                description="⚠️ **ATENÇÃO**: Selecione o painel que deseja excluir na lista abaixo.",
                color=discord.Color.red()
            )
            
            # Add a cancel button
            cancel_button = discord.ui.Button(
                label="Cancelar",
                style=discord.ButtonStyle.secondary,
                custom_id="cancel_delete"
            )
            cancel_button.callback = self.cancel_callback
            view.add_item(cancel_button)
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in delete_panel_callback: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao listar painéis para exclusão: {e}",
                ephemeral=True
            )
    
    async def advanced_settings_callback(self, interaction: discord.Interaction):
        """Callback for Advanced Settings button"""
        try:
            await self.show_advanced_settings(interaction)
            
        except Exception as e:
            logger.error(f"Error in advanced_settings_callback: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao abrir as configurações avançadas: {e}",
                ephemeral=True
            )
    
    async def show_advanced_settings(self, interaction: discord.Interaction, updated: bool = False):
        """Show advanced settings panel"""
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        # Get current global config (para outras configurações que ainda não estão no painel)
        config = get_config(guild_id)
        
        # Get user's edit session (painel específico que está sendo editado)
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição não encontrada. Inicie uma edição de painel primeiro.", ephemeral=True)
            return
        
        # Create embed
        embed = create_config_embed(
            title="Configurações Avançadas do Painel",
            description="Configure opções avançadas para este painel de tickets.",
            color=discord.Color.dark_purple()
        )
        
        # Add current settings to embed - usando dados específicos do painel
        max_tickets = session.get("max_tickets_per_user", 1)
        embed.add_field(
            name="🎟️ Máximo de Tickets por Usuário (deste painel)",
            value=f"Atual: **{max_tickets}**",
            inline=True
        )
        
        allow_member_close = config.get("allow_member_close", False)
        embed.add_field(
            name="🚪 Fechamento por Membros",
            value=f"Atual: **{'Ativado' if allow_member_close else 'Desativado'}**",
            inline=True
        )
        
        inactivity_time = config.get("inactivity_close_time", 72)
        inactivity_status = "Desativado" if inactivity_time == 0 else f"{inactivity_time} horas"
        embed.add_field(
            name="⏱️ Fechamento por Inatividade",
            value=f"Atual: **{inactivity_status}**",
            inline=True
        )
        
        ticket_format = config.get("ticket_name_format", "ticket-{number}")
        embed.add_field(
            name="🏷️ Formato do Nome do Ticket",
            value=f"Atual: **{ticket_format}**",
            inline=True
        )
        
        auto_archive = config.get("auto_archive_on_close", False)
        embed.add_field(
            name="📂 Arquivamento Automático",
            value=f"Atual: **{'Ativado' if auto_archive else 'Desativado'}**",
            inline=True
        )
        
        require_reason = config.get("require_reason_on_close", False)
        embed.add_field(
            name="📝 Exigir Motivo ao Fechar",
            value=f"Atual: **{'Ativado' if require_reason else 'Desativado'}**",
            inline=True
        )
        
        notify_on_open = config.get("notify_on_ticket_open", False)
        embed.add_field(
            name="🔔 Notificar ao Abrir Ticket",
            value=f"Atual: **{'Ativado' if notify_on_open else 'Desativado'}**",
            inline=True
        )
        
        # Create view with settings buttons
        view = discord.ui.View(timeout=300)
        
        # Button for max tickets per user
        max_tickets_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Tickets por Usuário",
            emoji="🎟️",
            row=0
        )
        
        async def max_tickets_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Máximo de Tickets por Usuário", custom_id="max_tickets_modal")
            
            ticket_input = discord.ui.TextInput(
                label="Máximo de Tickets (1-10)",
                placeholder="Digite um número de 1 a 10",
                default=str(max_tickets),
                required=True,
                min_length=1,
                max_length=2
            )
            
            modal.add_item(ticket_input)
            
            async def on_submit(modal_interaction: discord.Interaction):
                try:
                    new_max = int(ticket_input.value.strip())
                    if 1 <= new_max <= 10:
                        # Atualizar o valor na sessão do usuário (configuração específica do painel)
                        session["max_tickets_per_user"] = new_max
                        update_edit_session(user_id, guild_id, session)
                        
                        # Gerar mensagem de sucesso
                        await self.show_advanced_settings(modal_interaction, updated=True)
                    else:
                        await modal_interaction.response.send_message(
                            "O valor deve estar entre 1 e 10.",
                            ephemeral=True
                        )
                except ValueError:
                    await modal_interaction.response.send_message(
                        "Por favor, digite um número válido.",
                        ephemeral=True
                    )
            
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)
            
        max_tickets_button.callback = max_tickets_callback
        view.add_item(max_tickets_button)
        
        # Toggle button for member close
        member_close_button = discord.ui.Button(
            style=discord.ButtonStyle.success if allow_member_close else discord.ButtonStyle.secondary,
            label="Fechamento por Membros",
            emoji="🚪",
            row=0
        )
        
        async def member_close_callback(interaction: discord.Interaction):
            new_value = not allow_member_close
            from utils.config_manager import update_config
            update_config(guild_id, "allow_member_close", new_value)
            await self.show_advanced_settings(interaction, updated=True)
            
        member_close_button.callback = member_close_callback
        view.add_item(member_close_button)
        
        # Button for inactivity time
        inactivity_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Tempo de Inatividade",
            emoji="⏱️",
            row=1
        )
        
        async def inactivity_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Tempo de Inatividade", custom_id="inactivity_time_modal")
            
            time_input = discord.ui.TextInput(
                label="Horas (0-720, 0 = desativado)",
                placeholder="Digite um número de 0 a 720",
                default=str(inactivity_time),
                required=True,
                min_length=1,
                max_length=3
            )
            
            modal.add_item(time_input)
            await interaction.response.send_modal(modal)
            
        inactivity_button.callback = inactivity_callback
        view.add_item(inactivity_button)
        
        # Button for ticket name format
        ticket_format_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Formato do Ticket",
            emoji=Emoji.TICKET_FORMAT,
            row=1
        )
        
        async def ticket_format_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Formato do Nome do Ticket", custom_id="ticket_format_modal")
            
            format_input = discord.ui.TextInput(
                label="Formato (use {user}, {number}, {category})",
                placeholder="Exemplo: ticket-{user} ou {category}-{number}",
                default=ticket_format,
                required=True,
                min_length=3,
                max_length=50
            )
            
            modal.add_item(format_input)
            
            async def on_submit(modal_interaction: discord.Interaction):
                format_value = format_input.value
                from utils.config_manager import update_config
                update_config(guild_id, "ticket_name_format", format_value)
                print(f"Ticket format updated to: {format_value}")
                await self.show_advanced_settings(modal_interaction, updated=True)
                
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)
            
        ticket_format_button.callback = ticket_format_callback
        view.add_item(ticket_format_button)
        
        # Toggle button for auto archive
        auto_archive_button = discord.ui.Button(
            style=discord.ButtonStyle.success if auto_archive else discord.ButtonStyle.secondary,
            label="Arquivamento Auto.",
            emoji="📂",
            row=1
        )
        
        async def auto_archive_callback(interaction: discord.Interaction):
            new_value = not auto_archive
            from utils.config_manager import update_config
            update_config(guild_id, "auto_archive_on_close", new_value)
            await self.show_advanced_settings(interaction, updated=True)
            
        auto_archive_button.callback = auto_archive_callback
        view.add_item(auto_archive_button)
        
        # Toggle button for require reason
        require_reason_button = discord.ui.Button(
            style=discord.ButtonStyle.success if require_reason else discord.ButtonStyle.secondary,
            label="Exigir Motivo",
            emoji="📝",
            row=2
        )
        
        async def require_reason_callback(interaction: discord.Interaction):
            new_value = not require_reason
            from utils.config_manager import update_config
            update_config(guild_id, "require_reason_on_close", new_value)
            await self.show_advanced_settings(interaction, updated=True)
            
        require_reason_button.callback = require_reason_callback
        view.add_item(require_reason_button)
        
        # Toggle button for notify on open
        notify_button = discord.ui.Button(
            style=discord.ButtonStyle.success if notify_on_open else discord.ButtonStyle.secondary,
            label="Notificar ao Abrir",
            emoji="🔔",
            row=2
        )
        
        async def notify_callback(interaction: discord.Interaction):
            new_value = not notify_on_open
            from utils.config_manager import update_config
            update_config(guild_id, "notify_on_ticket_open", new_value)
            await self.show_advanced_settings(interaction, updated=True)
            
        notify_button.callback = notify_callback
        view.add_item(notify_button)
        
        # Button for button visibility settings
        visibility_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Visibilidade Botões",
            emoji="👁️",
            row=3
        )
        
        async def visibility_callback(interaction: discord.Interaction):
            await self.show_button_visibility_settings(interaction)
            
        visibility_button.callback = visibility_callback
        view.add_item(visibility_button)
        
        # Add back button
        back_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Voltar",
            emoji="⬅️",
            row=3
        )
        
        async def back_callback(interaction: discord.Interaction):
            # Go back to main config panel - recreate the main panel manually
            from utils.embed_creator import create_config_embed
            from utils.emoji_config import Emoji
            
            # Create the main config embed
            embed = create_config_embed(
                title="Configuração de Tickets",
                description="Utilize os botões abaixo para configurar o sistema de tickets.",
                color=discord.Color.blue()
            )
            
            # Create main buttons
            view = discord.ui.View(timeout=300)
            
            # Create Panel button
            create_button = discord.ui.Button(
                style=discord.ButtonStyle.success, 
                label="Criar Painel", 
                emoji=Emoji.ADD
            )
            create_button.callback = self.create_panel_callback
            
            # Edit Panel button
            edit_button = discord.ui.Button(
                style=discord.ButtonStyle.primary, 
                label="Editar Painel", 
                emoji=Emoji.EDIT
            )
            edit_button.callback = self.edit_panel_callback
            
            # Delete Panel button
            delete_button = discord.ui.Button(
                style=discord.ButtonStyle.danger, 
                label="Excluir Painel", 
                emoji=Emoji.DELETE
            )
            delete_button.callback = self.delete_panel_callback
            
            # Add buttons to view
            view.add_item(create_button)
            view.add_item(edit_button)
            view.add_item(delete_button)
            
            # Edit the message with the main panel
            await interaction.response.edit_message(embed=embed, view=view)
            
        back_button.callback = back_callback
        view.add_item(back_button)
        
        # Send or update message
        if updated:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_button_visibility_settings(self, interaction: discord.Interaction):
        """Show button visibility settings panel"""
        guild_id = str(interaction.guild_id)
        
        # Get current config
        config = get_config(guild_id)
        
        # Create embed
        embed = create_config_embed(
            title="Visibilidade dos Botões",
            description="Configure quais botões devem aparecer nos tickets.",
            color=discord.Color.blurple()
        )
        
        # Create view with toggle buttons
        view = discord.ui.View(timeout=300)
        
        # Button settings to toggle
        button_settings = [
            ("show_priority_button", "Prioridade", "🔺"),
            ("show_notify_button", "Notificação", "🔔"),
            ("show_archive_button", "Arquivar", "📂"),
            ("show_claim_button", "Atender", "👋"),
            ("show_transcript_button", "Transcrição", "📝")
        ]
        
        for setting_key, label, emoji in button_settings:
            is_enabled = config.get(setting_key, True)
            
            button = discord.ui.Button(
                style=discord.ButtonStyle.success if is_enabled else discord.ButtonStyle.secondary,
                label=label,
                emoji=emoji
            )
            
            async def button_callback(interaction, key=setting_key, current=is_enabled):
                from utils.config_manager import update_config
                update_config(guild_id, key, not current)
                await self.show_button_visibility_settings(interaction)
                
            button.callback = lambda i, k=setting_key, c=is_enabled: button_callback(i, k, c)
            view.add_item(button)
        
        # Add back button
        back_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Voltar",
            emoji="⬅️"
        )
        
        async def back_callback(interaction: discord.Interaction):
            await self.show_advanced_settings(interaction)
            
        back_button.callback = back_callback
        view.add_item(back_button)
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Callback for cancel buttons"""
        await interaction.response.edit_message(
            content="Operação cancelada.",
            embed=None,
            view=None
        )
    
    async def show_panel_editor(self, interaction: discord.Interaction, panel_id: str, new_panel: bool = False, updated: bool = False):
        """Show the panel editor interface"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
            
        # Update panel_id in session if necessary
        if panel_id and session.get("panel_id") != panel_id:
            session["panel_id"] = panel_id
            update_edit_session(user_id, guild_id, session)
        
        # Create embed for panel settings
        embed = create_config_embed(
            title=f"{'Criar' if new_panel else 'Editar'} Painel de Tickets",
            description="Configure o painel de tickets utilizando os botões abaixo.",
            color=discord.Color.blue()
        )
        
        # Mostrar o nome do painel (para identificação)
        panel_name = session.get("panel_name", "Painel sem nome")
        embed.add_field(
            name="Nome do Painel (Identificação)",
            value=f"**{panel_name}**",
            inline=False
        )
        
        # Show current panel preview
        preview = create_panel_preview(session)
        embed.add_field(
            name="Prévia do Painel",
            value=preview,
            inline=False
        )
        
        # Create view with config buttons
        view = discord.ui.View(timeout=300)
        
        # Panel name button (para identificação interna)
        panel_name_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Nome do Painel",
            emoji="🏷️",
            row=0
        )
        
        async def panel_name_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Nome de Identificação do Painel", custom_id="panel_name_modal")
            
            name_input = discord.ui.TextInput(
                label="Nome do Painel",
                placeholder="Digite um nome para identificar este painel",
                default=session.get("panel_name", ""),
                required=True,
                max_length=100
            )
            
            modal.add_item(name_input)
            await interaction.response.send_modal(modal)
            
        panel_name_button.callback = panel_name_callback
        view.add_item(panel_name_button)
        
        # Title button
        title_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Título",
            emoji="📝",
            row=0
        )
        
        async def title_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Configurar Título do Painel", custom_id="panel_title_modal")
            
            title_input = discord.ui.TextInput(
                label="Título",
                placeholder="Digite o título do painel",
                default=session.get("title", "Painel de Ticket"),
                required=True,
                max_length=100
            )
            
            modal.add_item(title_input)
            await interaction.response.send_modal(modal)
            
        title_button.callback = title_callback
        view.add_item(title_button)
        
        # Description button
        desc_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Descrição",
            emoji="📄",
            row=0
        )
        
        async def desc_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Configurar Descrição do Painel", custom_id="panel_description_modal")
            
            desc_input = discord.ui.TextInput(
                label="Descrição",
                placeholder="Digite a descrição do painel",
                default=session.get("description", "Clique no botão abaixo para abrir um ticket."),
                required=True,
                max_length=1000,
                style=discord.TextStyle.paragraph
            )
            
            modal.add_item(desc_input)
            await interaction.response.send_modal(modal)
            
        desc_button.callback = desc_callback
        view.add_item(desc_button)
        
        # Color button
        color_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Cor",
            emoji="🎨",
            row=1
        )
        
        async def color_callback(interaction: discord.Interaction):
            # Create a view with color selection
            color_view = discord.ui.View(timeout=300)
            
            # Color dropdown
            color_select = discord.ui.Select(
                placeholder="Selecione uma cor",
                custom_id="panel_color_select"
            )
            
            colors = [
                ("red", "Vermelho", "🔴"),
                ("green", "Verde", "🟢"),
                ("blue", "Azul", "🔵"),
                ("yellow", "Amarelo", "🟡"),
                ("purple", "Roxo", "🟣"),
                ("black", "Preto", "⚫"),
                ("white", "Branco", "⚪")
            ]
            
            for color_id, label, emoji in colors:
                color_select.add_option(
                    label=label,
                    value=color_id,
                    emoji=emoji,
                    default=session.get("color") == color_id
                )
            
            color_view.add_item(color_select)
            
            # Back button
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Voltar",
                emoji="⬅️"
            )
            
            async def back_callback(interaction: discord.Interaction):
                await self.show_panel_editor(interaction, panel_id)
                
            back_button.callback = back_callback
            color_view.add_item(back_button)
            
            color_embed = create_config_embed(
                title="Selecione uma Cor",
                description="Escolha a cor para o painel de tickets.",
                color=discord.Color.blue()
            )
            
            await interaction.response.edit_message(embed=color_embed, view=color_view)
            
        color_button.callback = color_callback
        view.add_item(color_button)
        
        # Support role button
        role_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Cargo",
            emoji="👥",
            row=1
        )
        
        async def role_callback(interaction: discord.Interaction):
            # Create a view with role selection
            role_view = discord.ui.View(timeout=300)
            
            # Use RoleSelect para selecionar cargos
            role_select = discord.ui.RoleSelect(
                placeholder="Selecione um cargo para notificações",
                custom_id="panel_role_select",
                min_values=0,
                max_values=1
            )
            
            description = "Escolha o cargo de suporte que será notificado nos tickets. Este cargo terá acesso a todos os tickets criados."
            
            # Função de callback quando o usuário selecionar um cargo
            async def role_select_callback(role_interaction: discord.Interaction):
                try:
                    # Obter o cargo selecionado
                    if role_interaction.data.get("values") and len(role_interaction.data["values"]) > 0:
                        selected_role_id = role_interaction.data["values"][0]
                        
                        # Atualizar a sessão
                        session["support_role_id"] = selected_role_id
                        update_edit_session(user_id, guild_id, session)
                        
                        # Voltar para o editor de painel
                        await self.show_panel_editor(role_interaction, panel_id, updated=True)
                    else:
                        # Se nenhum cargo foi selecionado, definir como None
                        session["support_role_id"] = None
                        update_edit_session(user_id, guild_id, session)
                        
                        # Voltar para o editor de painel
                        await self.show_panel_editor(role_interaction, panel_id, updated=True)
                except Exception as e:
                    logger.error(f"Error in role_select_callback: {e}")
                    await role_interaction.response.send_message(
                        f"Ocorreu um erro ao selecionar o cargo: {e}",
                        ephemeral=True
                    )
            
            role_select.callback = role_select_callback
            role_view.add_item(role_select)
            
            # Back button
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Voltar",
                emoji="⬅️"
            )
            
            async def back_callback(interaction: discord.Interaction):
                await self.show_panel_editor(interaction, panel_id)
                
            back_button.callback = back_callback
            role_view.add_item(back_button)
            
            role_embed = create_config_embed(
                title="Selecione um Cargo",
                description=description,
                color=discord.Color.blue()
            )
            
            await interaction.response.edit_message(embed=role_embed, view=role_view)
            
        role_button.callback = role_callback
        view.add_item(role_button)
        
        # Category button
        cat_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Categoria",
            emoji="📁",
            row=2
        )
        
        async def cat_callback(interaction: discord.Interaction):
            # Create a view with channel selection
            cat_view = discord.ui.View(timeout=300)
            
            # Use ChannelSelect para selecionar categorias
            cat_select = discord.ui.ChannelSelect(
                placeholder="Selecione uma categoria",
                custom_id="panel_category_select",
                channel_types=[discord.ChannelType.category],
                min_values=0,
                max_values=1
            )
            
            description = "Escolha a categoria onde os tickets serão criados. Todos os tickets serão criados nesta categoria."
            
            # Função de callback quando o usuário selecionar uma categoria
            async def cat_select_callback(cat_interaction: discord.Interaction):
                try:
                    # Obter a categoria selecionada
                    if cat_interaction.data.get("values") and len(cat_interaction.data["values"]) > 0:
                        selected_cat_id = cat_interaction.data["values"][0]
                        
                        # Atualizar a sessão
                        session["category_id"] = selected_cat_id
                        update_edit_session(user_id, guild_id, session)
                        
                        # Voltar para o editor de painel
                        await self.show_panel_editor(cat_interaction, panel_id, updated=True)
                    else:
                        # Se nenhuma categoria foi selecionado, definir como None
                        session["category_id"] = None
                        update_edit_session(user_id, guild_id, session)
                        
                        # Voltar para o editor de painel
                        await self.show_panel_editor(cat_interaction, panel_id, updated=True)
                except Exception as e:
                    logger.error(f"Error in cat_select_callback: {e}")
                    await cat_interaction.response.send_message(
                        f"Ocorreu um erro ao selecionar a categoria: {e}",
                        ephemeral=True
                    )
            
            cat_select.callback = cat_select_callback
            cat_view.add_item(cat_select)
            
            # Back button
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Voltar",
                emoji="⬅️"
            )
            
            async def back_callback(interaction: discord.Interaction):
                await self.show_panel_editor(interaction, panel_id)
                
            back_button.callback = back_callback
            cat_view.add_item(back_button)
            
            cat_embed = create_config_embed(
                title="Selecione uma Categoria",
                description=description,
                color=discord.Color.blue()
            )
            
            await interaction.response.edit_message(embed=cat_embed, view=cat_view)
            
        cat_button.callback = cat_callback
        view.add_item(cat_button)
        
        # Appearance button
        app_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurar Aparência",
            emoji="🎭",
            row=2
        )
        
        async def app_callback(interaction: discord.Interaction):
            await self.show_panel_appearance_settings(interaction)
            
        app_button.callback = app_callback
        view.add_item(app_button)
        
        # Botão de mensagens personalizadas (novo botão para configurar mensagens)
        custom_msg_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Mensagens Personalizadas",
            emoji="💬",
            row=2
        )
        
        async def custom_msg_callback(interaction: discord.Interaction):
            await self.show_custom_messages_settings(interaction)
            
        custom_msg_button.callback = custom_msg_callback
        view.add_item(custom_msg_button)
        
        # Advanced settings button (agora dentro da edição de painel)
        adv_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configurações Avançadas",
            emoji="⚙️",
            row=2
        )
        
        async def adv_callback(interaction: discord.Interaction):
            await self.show_advanced_settings(interaction)
            
        adv_button.callback = adv_callback
        view.add_item(adv_button)
        
        # Save button
        save_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Salvar",
            emoji="💾",
            row=3
        )
        
        async def save_callback(interaction: discord.Interaction):
            # Validate required fields
            if not session.get("title"):
                await interaction.response.send_message("O título do painel é obrigatório!", ephemeral=True)
                return
                
            if not session.get("description"):
                await interaction.response.send_message("A descrição do painel é obrigatório!", ephemeral=True)
                return
                
            if session.get("interaction_type") == "dropdown" and not session.get("dropdown_options"):
                await interaction.response.send_message("É necessário adicionar pelo menos uma opção ao dropdown!", ephemeral=True)
                return
                
            # Save panel data
            panel_data = {
                "id": panel_id,
                "panel_id": panel_id,  # Adicionando o panel_id explicitamente
                "panel_name": session.get("panel_name", "Painel sem nome"),  # Nome para identificação
                "title": session.get("title"),
                "description": session.get("description"),
                "color": session.get("color"),
                "support_role_id": session.get("support_role_id"),
                "category_id": session.get("category_id"),
                "interaction_type": session.get("interaction_type"),
                "button_style": session.get("button_style"),
                "button_emoji": session.get("button_emoji"),
                "button_text": session.get("button_text"),
                "dropdown_placeholder": session.get("dropdown_placeholder"),
                "dropdown_options": session.get("dropdown_options", []),
                "ticket_name_format": session.get("ticket_name_format", "ticket-{number}"),  # Formato do nome do ticket
                "welcome_message": session.get("welcome_message", "Olá {user}, seu ticket foi criado com sucesso."),  # Mensagem de boas-vindas
                "instruction_message": session.get("instruction_message", "• Descreva seu problema detalhadamente\n• Aguarde o atendimento da equipe\n• Use o botão `Fechar Ticket` quando finalizar\n• Seja paciente e cortês"),  # Instruções do ticket
                "creator_id": session.get("creator_id"),
                "guild_id": guild_id,
                "created_at": session.get("created_at")
            }
            
            # Create or update panel
            if new_panel:
                create_panel_data(guild_id, panel_id, panel_data)
                message = "Painel criado com sucesso! Utilize `/ticket-setup` para criar um painel com estas configurações ou crie manualmente."
            else:
                update_panel_data(guild_id, panel_id, panel_data)
                message = "Painel atualizado com sucesso!"
            
            # Send confirmation
            await interaction.response.edit_message(
                content=message,
                embed=None,
                view=None
            )
            
        save_button.callback = save_callback
        view.add_item(save_button)
        
        # Cancel button
        cancel_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Cancelar",
            emoji="❌",
            row=3
        )
        
        async def cancel_save_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="Operação cancelada.",
                embed=None,
                view=None
            )
            
        cancel_button.callback = cancel_save_callback
        view.add_item(cancel_button)
        
        # Send or update message
        if updated:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            # For first load or when navigating back from a submenu
            if new_panel:
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_panel_appearance_settings(self, interaction: discord.Interaction, updated: bool = False):
        """Show panel appearance settings (button or dropdown)"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Get panel ID
        panel_id = session.get("panel_id")
        
        # Create embed for appearance settings
        embed = create_config_embed(
            title="Configurar Aparência do Painel",
            description="Escolha como os usuários irão interagir com o painel de tickets.",
            color=discord.Color.blue()
        )
        
        # Add current settings to embed
        interaction_type = session.get("interaction_type", "button")
        embed.add_field(
            name="Tipo de Interação",
            value=f"**{'Botão' if interaction_type == 'button' else 'Dropdown'}**",
            inline=False
        )
        
        # Mostrar formato do nome do ticket
        ticket_name_format = session.get("ticket_name_format", "ticket-{number}")
        embed.add_field(
            name="Formato do Nome do Ticket",
            value=f"**{ticket_name_format}**",
            inline=False
        )
        
        if interaction_type == "button":
            button_style = session.get("button_style", "primary")
            button_emoji = session.get("button_emoji", "🎫")
            button_text = session.get("button_text", "Abrir Ticket")
            
            embed.add_field(
                name="Estilo do Botão",
                value=f"**{button_style.capitalize()}**",
                inline=True
            )
            
            embed.add_field(
                name="Emoji do Botão",
                value=f"**{button_emoji}**",
                inline=True
            )
            
            embed.add_field(
                name="Texto do Botão",
                value=f"**{button_text}**",
                inline=True
            )
        else:
            dropdown_placeholder = session.get("dropdown_placeholder", "Selecione uma opção")
            dropdown_options = session.get("dropdown_options", [])
            
            embed.add_field(
                name="Placeholder do Dropdown",
                value=f"**{dropdown_placeholder}**",
                inline=True
            )
            
            embed.add_field(
                name="Opções do Dropdown",
                value=f"**{len(dropdown_options)}** opção(ões) configurada(s)",
                inline=True
            )
        
        # Create view with appearance buttons
        view = discord.ui.View(timeout=300)
        
        # Toggle button type
        toggle_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Alternar para {'Dropdown' if interaction_type == 'button' else 'Botão'}",
            emoji="🔄",
            row=0
        )
        
        async def toggle_callback(interaction: discord.Interaction):
            # Toggle interaction type
            new_type = "dropdown" if session.get("interaction_type") == "button" else "button"
            session["interaction_type"] = new_type
            update_edit_session(user_id, guild_id, session)
            
            # Show updated settings
            await self.show_panel_appearance_settings(interaction, updated=True)
            
        toggle_button.callback = toggle_callback
        view.add_item(toggle_button)
        
        # Ticket name format button
        ticket_format_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Formato do Nome do Ticket",
            emoji=Emoji.TICKET_FORMAT,
            row=0
        )
        
        async def ticket_format_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Formato do Nome do Ticket", custom_id="ticket_name_format_modal")
            
            format_input = discord.ui.TextInput(
                label="Formato do Nome",
                placeholder="Ex: ticket-{user}-{number}",
                default=session.get("ticket_name_format", "ticket-{number}"),
                required=True,
                max_length=100
            )
            
            modal.add_item(format_input)
            
            # Add description about available variables
            description = "Variáveis disponíveis:\n"
            description += "{user} - Nome do usuário\n"
            description += "{number} - Número sequencial do ticket\n"
            description += "{category} - Categoria selecionada (se estiver usando dropdown)"
            
            # Create a text input just for showing description (read-only)
            info_input = discord.ui.TextInput(
                label="Variáveis Disponíveis",
                default=description,
                required=False,
                style=discord.TextStyle.paragraph
            )
            
            modal.add_item(info_input)
            
            async def on_submit(modal_interaction: discord.Interaction):
                # Get the format from the input
                ticket_format = modal_interaction.data["components"][0]["components"][0]["value"]
                
                # Update the session
                session["ticket_name_format"] = ticket_format
                update_edit_session(user_id, guild_id, session)
                
                # Show updated settings
                await self.show_panel_appearance_settings(modal_interaction, updated=True)
                
                # Send response
                await modal_interaction.response.send_message(
                    f"Formato do nome do ticket atualizado para: `{ticket_format}`", 
                    ephemeral=True
                )
                
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)
            
        ticket_format_button.callback = ticket_format_callback
        view.add_item(ticket_format_button)
        
        # Button/Dropdown specific settings
        if interaction_type == "button":
            # Button style
            style_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Estilo do Botão",
                emoji="🎨",
                row=1
            )
            
            async def style_callback(interaction: discord.Interaction):
                # Create a view with style options
                style_view = discord.ui.View(timeout=300)
                
                # Style dropdown
                style_select = discord.ui.Select(
                    placeholder="Selecione um estilo",
                    custom_id="button_style_select"
                )
                
                styles = [
                    ("primary", "Azul (Primary)"),
                    ("success", "Verde (Success)"),
                    ("danger", "Vermelho (Danger)"),
                    ("secondary", "Cinza (Secondary)")
                ]
                
                for style_id, label in styles:
                    style_select.add_option(
                        label=label,
                        value=style_id,
                        default=session.get("button_style") == style_id
                    )
                
                style_view.add_item(style_select)
                
                # Back button
                back_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Voltar",
                    emoji="⬅️"
                )
                
                async def back_callback(interaction: discord.Interaction):
                    await self.show_panel_appearance_settings(interaction)
                    
                back_button.callback = back_callback
                style_view.add_item(back_button)
                
                style_embed = create_config_embed(
                    title="Selecione o Estilo do Botão",
                    description="Escolha a cor/estilo para o botão do painel de tickets.",
                    color=discord.Color.blue()
                )
                
                await interaction.response.edit_message(embed=style_embed, view=style_view)
                
            style_button.callback = style_callback
            view.add_item(style_button)
            
            # Button emoji
            emoji_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Emoji do Botão",
                emoji="😀",
                row=1
            )
            
            async def emoji_callback(interaction: discord.Interaction):
                modal = discord.ui.Modal(title="Configurar Emoji do Botão", custom_id="button_emoji_modal")
                
                emoji_input = discord.ui.TextInput(
                    label="Emoji",
                    placeholder="Digite um emoji",
                    default=session.get("button_emoji", "🎫"),
                    required=True,
                    max_length=5
                )
                
                modal.add_item(emoji_input)
                await interaction.response.send_modal(modal)
                
            emoji_button.callback = emoji_callback
            view.add_item(emoji_button)
            
            # Button text
            text_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Texto do Botão",
                emoji="📝",
                row=1
            )
            
            async def text_callback(interaction: discord.Interaction):
                modal = discord.ui.Modal(title="Configurar Texto do Botão", custom_id="button_text_modal")
                
                text_input = discord.ui.TextInput(
                    label="Texto",
                    placeholder="Digite o texto do botão",
                    default=session.get("button_text", "Abrir Ticket"),
                    required=True,
                    max_length=80
                )
                
                modal.add_item(text_input)
                await interaction.response.send_modal(modal)
                
            text_button.callback = text_callback
            view.add_item(text_button)
            
        else:
            # Dropdown placeholder
            placeholder_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Placeholder do Dropdown",
                emoji="📝",
                row=1
            )
            
            async def placeholder_callback(interaction: discord.Interaction):
                modal = discord.ui.Modal(title="Configurar Placeholder", custom_id="dropdown_placeholder_modal")
                
                placeholder_input = discord.ui.TextInput(
                    label="Placeholder",
                    placeholder="Digite o texto do placeholder",
                    default=session.get("dropdown_placeholder", "Selecione uma opção"),
                    required=True,
                    max_length=100
                )
                
                modal.add_item(placeholder_input)
                await interaction.response.send_modal(modal)
                
            placeholder_button.callback = placeholder_callback
            view.add_item(placeholder_button)
            
            # Dropdown options
            options_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Opções do Dropdown",
                emoji="📋",
                row=1
            )
            
            async def options_callback(interaction: discord.Interaction):
                await self.show_dropdown_options(interaction)
                
            options_button.callback = options_callback
            view.add_item(options_button)
        
        # Back button
        back_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Voltar",
            emoji="⬅️",
            row=2
        )
        
        async def back_callback(interaction: discord.Interaction):
            # Verify that panel_id is not None
            if panel_id is None:
                print(f"WARNING: panel_id is None in back_callback")
                panel_id_to_use = str(uuid.uuid4())
                print(f"Using generated panel_id instead: {panel_id_to_use}")
                session["panel_id"] = panel_id_to_use
                update_edit_session(user_id, guild_id, session)
                await self.show_panel_editor(interaction, panel_id_to_use)
            else:
                print(f"Using existing panel_id: {panel_id}")
                await self.show_panel_editor(interaction, panel_id)
            
        back_button.callback = back_callback
        view.add_item(back_button)
        
        # Send or update message
        if updated:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)
    
    async def show_dropdown_options(self, interaction: discord.Interaction, updated: bool = False):
        """Show dropdown options management interface"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Get dropdown options
        dropdown_options = session.get("dropdown_options", [])
        
        # Create embed for dropdown options
        embed = create_config_embed(
            title="Opções do Dropdown",
            description="Gerencie as opções que aparecerão no dropdown.",
            color=discord.Color.blue()
        )
        
        # Add current options to embed
        if dropdown_options:
            options_text = ""
            for option in dropdown_options:
                emoji = option.get("emoji", "")
                label = option.get("label", "")
                value = option.get("value", "")
                description = option.get("description", "")
                
                options_text += f"{emoji} **{label}** (ID: `{value}`)\n"
                options_text += f"> {description}\n\n"
                
            embed.add_field(
                name=f"Opções Configuradas ({len(dropdown_options)})",
                value=options_text or "Nenhuma opção configurada.",
                inline=False
            )
        else:
            embed.add_field(
                name="Opções Configuradas",
                value="Nenhuma opção configurada ainda.",
                inline=False
            )
        
        # Create view with option management buttons
        view = discord.ui.View(timeout=300)
        
        # Add option button
        add_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Adicionar Opção",
            emoji="➕",
            row=0
        )
        
        async def add_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Adicionar Opção ao Dropdown", custom_id="add_dropdown_option_modal")
            
            label_input = discord.ui.TextInput(
                label="Título da Opção",
                placeholder="Título que aparece no dropdown",
                required=True,
                max_length=100
            )
            
            value_input = discord.ui.TextInput(
                label="Valor da Opção (ID interno)",
                placeholder="ID interno da opção",
                required=True,
                max_length=100
            )
            
            description_input = discord.ui.TextInput(
                label="Descrição da Opção",
                placeholder="Descrição que aparece no dropdown",
                required=True,
                max_length=100
            )
            
            emoji_input = discord.ui.TextInput(
                label="Emoji da Opção",
                placeholder="Emoji para exibir (opcional)",
                required=False,
                max_length=5
            )
            
            modal.add_item(label_input)
            modal.add_item(value_input)
            modal.add_item(description_input)
            modal.add_item(emoji_input)
            
            await interaction.response.send_modal(modal)
            
        add_button.callback = add_callback
        view.add_item(add_button)
        
        if dropdown_options:
            # Edit option button
            edit_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Editar Opção",
                emoji="✏️",
                row=0
            )
            #1
            async def edit_callback(interaction: discord.Interaction):
                edit_view = discord.ui.View(timeout=300)

                option_select = discord.ui.Select(
                    placeholder="Selecione uma opção para editar",
                    custom_id="edit_dropdown_option_select"
                )

                for option in dropdown_options:
                    emoji = option.get("emoji")
                    if isinstance(emoji, str):
                        emoji = emoji.strip().replace("️", "")  # remove modificadores invisíveis
                    else:
                        emoji = None

                    label = option.get("label", "")
                    value = option.get("value", "")

                    if emoji:
                        option_select.add_option(label=label, value=value, emoji=emoji)
                    else:
                        option_select.add_option(label=label, value=value)

                edit_view.add_item(option_select)

                back_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Voltar",
                    emoji="⬅️"
                )

                async def back_callback(interaction: discord.Interaction):
                    await self.show_dropdown_options(interaction)

                back_button.callback = back_callback
                edit_view.add_item(back_button)

                edit_embed = create_config_embed(
                    title="Editar Opção do Dropdown",
                    description="Selecione a opção que deseja editar.",
                    color=discord.Color.blue()
                )

                await interaction.response.edit_message(embed=edit_embed, view=edit_view)

                #2
            edit_button.callback = edit_callback
            view.add_item(edit_button)
            
            # Remove option button
            remove_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Remover Opção",
                row=0
            )
            
            async def remove_callback(interaction: discord.Interaction):
                remove_view = discord.ui.View(timeout=300)

                option_select = discord.ui.Select(
                    placeholder="Selecione uma opção para remover",
                    custom_id="delete_dropdown_option_select"
                )

                for option in dropdown_options:
                    emoji = option.get("emoji")
                    if isinstance(emoji, str):
                        emoji = emoji.strip().replace("️", "")  # remove modificadores invisíveis
                    else:
                        emoji = None

                    label = option.get("label", "")
                    value = option.get("value", "")

                    if emoji:
                        option_select.add_option(label=label, value=value, emoji=emoji)
                    else:
                        option_select.add_option(label=label, value=value)

                remove_view.add_item(option_select)

                back_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Voltar",
                    emoji="⬅️"
                )

                async def back_callback(interaction: discord.Interaction):
                    await self.show_dropdown_options(interaction)

                back_button.callback = back_callback
                remove_view.add_item(back_button)

                remove_embed = create_config_embed(
                    title="Remover Opção do Dropdown",
                    description="Selecione a opção que deseja remover.",
                    color=discord.Color.red()
                )

                await interaction.response.edit_message(embed=remove_embed, view=remove_view)

                
            remove_button.callback = remove_callback
            view.add_item(remove_button)
        
        # Back button
        back_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Voltar",
            emoji="⬅️",
            row=1
        )
        
        async def back_callback(interaction: discord.Interaction):
            # Obter o panel_id da sessão para garantir consistência
            panel_id = session.get("panel_id")
            if panel_id is None:
                print(f"WARNING: panel_id is None in dropdown_options back_callback")
                panel_id_to_use = str(uuid.uuid4())
                print(f"Using generated panel_id instead: {panel_id_to_use}")
                session["panel_id"] = panel_id_to_use
                update_edit_session(user_id, guild_id, session)
            else:
                print(f"Using existing panel_id in dropdown_options: {panel_id}")
            await self.show_panel_appearance_settings(interaction)
            
        back_button.callback = back_callback
        view.add_item(back_button)
        
        # Send or update message
        if updated:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)
    
    async def show_custom_messages_settings(self, interaction: discord.Interaction, updated: bool = False):
        """Show the custom messages settings panel for a ticket panel"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get session data
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Get panel ID
        panel_id = session.get("panel_id")
        
        # Create embed for custom messages settings
        embed = create_config_embed(
            title="Mensagens Personalizadas do Painel",
            description="Configure as mensagens que serão exibidas nos tickets deste painel.",
            color=discord.Color.purple()
        )
        
        # Recuperar as mensagens personalizadas da sessão ou usar valores padrão
        welcome_message = session.get("welcome_message", "Olá {user}, seu ticket foi criado com sucesso.")
        instruction_message = session.get("instruction_message", "• Descreva seu problema detalhadamente\n• Aguarde o atendimento da equipe\n• Use o botão `Fechar Ticket` quando finalizar\n• Seja paciente e cortês")
        
        # Adicionar informações das mensagens atuais
        embed.add_field(
            name="💬 Mensagem de Boas-Vindas",
            value=welcome_message,
            inline=False
        )
        
        embed.add_field(
            name="📋 Instruções do Ticket",
            value=instruction_message,
            inline=False
        )
        
        embed.add_field(
            name="🔖 Variáveis Disponíveis",
            value="`{user}` - Menção ao usuário\n`{ticket_number}` - Número do ticket\n`{server}` - Nome do servidor",
            inline=False
        )
        
        # Criar view com botões para as diferentes mensagens
        view = discord.ui.View(timeout=300)
        
        # Botão para editar a mensagem de boas-vindas
        welcome_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Editar Mensagem de Boas-Vindas",
            emoji="💬",
            row=0
        )
        
        async def welcome_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Mensagem de Boas-Vindas", custom_id="welcome_message_modal")
            
            message_input = discord.ui.TextInput(
                label="Mensagem de Boas-Vindas",
                placeholder="Olá {user}, seu ticket foi criado com sucesso.",
                default=session.get("welcome_message", "Olá {user}, seu ticket foi criado com sucesso."),
                required=True,
                style=discord.TextStyle.paragraph,
                max_length=1000
            )
            
            modal.add_item(message_input)
            
            async def on_submit(modal_interaction: discord.Interaction):
                # Atualizar a mensagem de boas-vindas
                session["welcome_message"] = modal_interaction.data["components"][0]["components"][0]["value"]
                update_edit_session(user_id, guild_id, session)
                
                # Mostrar configurações atualizadas
                await self.show_custom_messages_settings(modal_interaction, updated=True)
                
                # Enviar resposta para o usuário
                await modal_interaction.response.send_message("Mensagem de boas-vindas atualizada!", ephemeral=True)
            
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)
        
        welcome_button.callback = welcome_callback
        view.add_item(welcome_button)
        
        # Botão para editar as instruções do ticket
        instruction_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Editar Instruções do Ticket",
            emoji="📋",
            row=0
        )
        
        async def instruction_callback(interaction: discord.Interaction):
            modal = discord.ui.Modal(title="Instruções do Ticket", custom_id="instruction_message_modal")
            
            message_input = discord.ui.TextInput(
                label="Instruções do Ticket",
                placeholder="• Descreva seu problema detalhadamente\n• Aguarde o atendimento...",
                default=session.get("instruction_message", "• Descreva seu problema detalhadamente\n• Aguarde o atendimento da equipe\n• Use o botão `Fechar Ticket` quando finalizar\n• Seja paciente e cortês"),
                required=True,
                style=discord.TextStyle.paragraph,
                max_length=1000
            )
            
            modal.add_item(message_input)
            
            async def on_submit(modal_interaction: discord.Interaction):
                # Atualizar as instruções do ticket
                session["instruction_message"] = modal_interaction.data["components"][0]["components"][0]["value"]
                update_edit_session(user_id, guild_id, session)
                
                # Mostrar configurações atualizadas
                await self.show_custom_messages_settings(modal_interaction, updated=True)
                
                # Enviar resposta para o usuário
                await modal_interaction.response.send_message("Instruções do ticket atualizadas!", ephemeral=True)
            
            modal.on_submit = on_submit
            await interaction.response.send_modal(modal)
        
        instruction_button.callback = instruction_callback
        view.add_item(instruction_button)
        
        # Botão para visualizar prévia
        preview_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Visualizar Prévia",
            emoji="👁️",
            row=1
        )
        
        async def preview_callback(interaction: discord.Interaction):
            # Criar uma prévia da mensagem de boas-vindas com as variáveis substituídas
            preview_welcome = welcome_message.replace("{user}", interaction.user.mention)
            preview_welcome = preview_welcome.replace("{ticket_number}", "123")
            preview_welcome = preview_welcome.replace("{server}", interaction.guild.name)
            
            # Criar embed de prévia
            preview_embed = discord.Embed(
                title="📋 Ticket #123", 
                description=preview_welcome,
                color=discord.Color.blue()
            )
            
            # Adicionar campos da prévia
            preview_embed.add_field(
                name="🔍 Informações",
                value=f"**Categoria:** Exemplo\n**Criado por:** {interaction.user.mention}\n**ID:** `123456789`",
                inline=True
            )
            
            preview_embed.add_field(
                name="⏰ Status",
                value="**Estado:** `Aberto`\n**Prioridade:** `Padrão`\n**Atendente:** `Nenhum`",
                inline=True
            )
            
            preview_embed.add_field(
                name="📢 Como utilizar o ticket",
                value=instruction_message,
                inline=False
            )
            
            preview_embed.set_footer(text="Esta é apenas uma prévia do ticket")
            
            # Enviar prévia como mensagem efêmera
            await interaction.response.send_message(
                content="**Prévia do Ticket:**",
                embed=preview_embed,
                ephemeral=True
            )
        
        preview_button.callback = preview_callback
        view.add_item(preview_button)
        
        # Botão para voltar
        back_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Voltar",
            emoji="⬅️",
            row=1
        )
        
        async def back_callback(interaction: discord.Interaction):
            # Voltar para o editor de painel
            await self.show_panel_editor(interaction, panel_id, updated=True)
        
        back_button.callback = back_callback
        view.add_item(back_button)
        
        # Enviar ou atualizar mensagem
        if updated:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def confirm_delete_panel(self, interaction: discord.Interaction, panel_id: str):
        """Show confirmation for panel deletion"""
        guild_id = str(interaction.guild_id)
        
        # Get panel data
        panel_data = get_panel_data(guild_id, panel_id)
        if not panel_data:
            await interaction.response.send_message("Painel não encontrado!", ephemeral=True)
            return
            
        # Create confirmation embed
        embed = create_config_embed(
            title="Confirmar Exclusão",
            description=f"Você está prestes a excluir o painel **{panel_data.get('title')}**.\n\nEsta ação não pode ser desfeita!",
            color=discord.Color.red()
        )
        
        # Create view with confirmation buttons
        view = discord.ui.View(timeout=300)
        
        # Confirm button
        confirm_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Confirmar Exclusão",
            emoji="⚠️",
            row=0
        )
        
        async def confirm_callback(interaction: discord.Interaction):
            # Delete panel
            delete_panel_data(guild_id, panel_id)
            
            await interaction.response.edit_message(
                content="Painel excluído com sucesso!",
                embed=None,
                view=None
            )
            
        confirm_button.callback = confirm_callback
        view.add_item(confirm_button)
        
        # Cancel button
        cancel_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Cancelar",
            emoji="❌",
            row=0
        )
        
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="Exclusão cancelada.",
                embed=None,
                view=None
            )
            
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def send_panel_to_channel(
        self,
        interaction: discord.Interaction,
        panel_id: str,
        channel: Optional[discord.TextChannel] = None
    ) -> bool:
        """Send a configured panel to the specified channel"""
        try:
            guild_id = str(interaction.guild.id)
            
            # If no channel was specified, use the current channel
            if not channel:
                channel = interaction.channel
            
            # Get panel data
            from utils.config_manager import get_panel_data
            panel_data = get_panel_data(guild_id, panel_id)
            
            if not panel_data:
                logger.error(f"Panel {panel_id} not found for guild {guild_id}")
                return False
            
            # Create panel embed
            color_map = {
                "red": discord.Color.red(),
                "green": discord.Color.green(),
                "blue": discord.Color.blue(),
                "yellow": discord.Color.gold(),
                "purple": discord.Color.purple(),
                "black": discord.Color.dark_grey(),
                "white": discord.Color.light_grey()
            }
            
            title = panel_data.get("title", "Painel de Ticket")
            description = panel_data.get("description", "Clique no botão abaixo para abrir um ticket.")
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color_map.get(panel_data.get("color"), discord.Color.blue())
            )
            
            # Create panel interaction component (button or dropdown)
            view = discord.ui.View(timeout=None)
            
            interaction_type = panel_data.get("interaction_type", "button")
            
            if interaction_type == "button":
                # Create button
                button_style_map = {
                    "primary": discord.ButtonStyle.primary,
                    "success": discord.ButtonStyle.success,
                    "danger": discord.ButtonStyle.danger,
                    "secondary": discord.ButtonStyle.secondary
                }
                
                button = discord.ui.Button(
                    style=button_style_map.get(panel_data.get("button_style"), discord.ButtonStyle.primary),
                    label=panel_data.get("button_text", "Abrir Ticket"),
                    emoji=panel_data.get("button_emoji", "🎫"),
                    custom_id=f"create_ticket:{panel_id}"
                )
                
                view.add_item(button)
            else:
                # Create dropdown
                dropdown = discord.ui.Select(
                    placeholder=panel_data.get("dropdown_placeholder", "Selecione uma opção"),
                    custom_id=f"create_ticket_dropdown:{panel_id}"
                )
                
                # Add options to dropdown
                dropdown_options = panel_data.get("dropdown_options", [])
                if not dropdown_options:
                    # Add at least one option if none exists
                    dropdown.add_option(
                        label="Ticket Padrão",
                        value="default",
                        description="Abrir um ticket padrão",
                        emoji="🎫"
                    )
                else:
                    for option in dropdown_options:
                        dropdown.add_option(
                            label=option.get("label", "Opção"),
                            value=option.get("value", "default"),
                            description=option.get("description", ""),
                            emoji=option.get("emoji", None)
                        )
                
                view.add_item(dropdown)
            
            # Send panel to channel
            await channel.send(embed=embed, view=view)
            
            logger.info(f"Panel {panel_id} sent to channel {channel.name} ({channel.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error in send_panel_to_channel: {e}")
            return False
            
    async def quick_setup_panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        role: Optional[discord.Role] = None,
        category: Optional[discord.CategoryChannel] = None
    ) -> bool:
        """Create a panel quickly with the /ticket-setup command"""
        try:
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel_id)
            
            # Create panel ID
            panel_id = str(uuid.uuid4())
            
            # Create panel data
            panel_data = {
                "id": panel_id,
                "panel_id": panel_id,  # Adicionando o panel_id explicitamente
                "title": title,
                "description": description,
                "color": "blue",
                "support_role_id": str(role.id) if role else None,
                "category_id": str(category.id) if category else None,
                "interaction_type": "button",
                "button_style": "primary",
                "button_emoji": "🎫",
                "button_text": "Abrir Ticket",
                "dropdown_placeholder": "Selecione uma opção",
                "dropdown_options": [],
                "creator_id": user_id,
                "guild_id": guild_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Save panel data
            create_panel_data(guild_id, panel_id, panel_data)
            print(f"Quick setup panel created with panel_id: {panel_id}")
            
            # Create panel embed
            color_map = {
                "red": discord.Color.red(),
                "green": discord.Color.green(),
                "blue": discord.Color.blue(),
                "yellow": discord.Color.gold(),
                "purple": discord.Color.purple(),
                "black": discord.Color.dark_grey(),
                "white": discord.Color.light_grey()
            }
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color_map.get(panel_data.get("color"), discord.Color.blue())
            )
            
            # Create panel button
            view = discord.ui.View(timeout=None)
            
            button_style_map = {
                "primary": discord.ButtonStyle.primary,
                "success": discord.ButtonStyle.success,
                "danger": discord.ButtonStyle.danger,
                "secondary": discord.ButtonStyle.secondary
            }
            
            button = discord.ui.Button(
                style=button_style_map.get(panel_data.get("button_style"), discord.ButtonStyle.primary),
                label=panel_data.get("button_text"),
                emoji=panel_data.get("button_emoji"),
                custom_id=f"create_ticket:{panel_id}"
            )
            
            view.add_item(button)
            
            # Send panel to channel
            channel = interaction.channel
            await channel.send(embed=embed, view=view)
            
            logger.info(f"Quick panel setup created in channel {channel.name} ({channel_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error in quick_setup_panel: {e}")
            return False
    
    async def create_ticket(self, interaction: discord.Interaction, panel_id: str, ticket_type: str = None):
        """Create a new ticket from panel interaction"""
        try:
            from utils.config_manager import get_config, get_panel_data, _load_json, delete_ticket_data
            
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            
            # Get panel data
            panel_data = get_panel_data(guild_id, panel_id)
            if not panel_data:
                await interaction.response.send_message("Painel de ticket não encontrado!", ephemeral=True)
                return
            
            # Verificar se o usuário tem tickets antigos cujos canais foram excluídos
            # e remover esses tickets da base de dados
            tickets_file = "data/tickets.json"
            tickets = _load_json(tickets_file)
            
            # Lista para armazenar tickets inválidos
            invalid_tickets = []
            
            # Se o guild existe na base de tickets
            if guild_id in tickets:
                # Verificar cada ticket deste usuário
                for channel_id, ticket in tickets[guild_id].items():
                    if ticket.get("user_id") == user_id and ticket.get("status") == "open":
                        # Verificar se o canal ainda existe
                        try:
                            channel = interaction.guild.get_channel(int(channel_id))
                            if not channel:
                                # Canal não existe mais, marcar para remoção
                                invalid_tickets.append(channel_id)
                                logger.info(f"Ticket {channel_id} não existe mais no servidor, será removido")
                        except Exception as e:
                            logger.error(f"Erro ao verificar canal {channel_id}: {e}")
                            # Em caso de erro, assumir que o canal não existe
                            invalid_tickets.append(channel_id)
            
            # Remover tickets inválidos
            for channel_id in invalid_tickets:
                delete_ticket_data(guild_id, channel_id)
                logger.info(f"Ticket {channel_id} removido da base de dados")
            
            # Avisar o usuário que alguns tickets foram limpos (depois de remover todos)
            if len(invalid_tickets) > 0:
                await interaction.response.send_message(
                    f"Detectamos {len(invalid_tickets)} ticket(s) antigo(s) que não existem mais e foram removidos da sua contagem.",
                    ephemeral=True
                )
                await asyncio.sleep(2)  # Esperar 2 segundos antes de continuar
                
            # Check user ticket limit - usando configuração específica do painel
            max_tickets = panel_data.get("max_tickets_per_user", 1)  # Valor padrão: 1 ticket por usuário
            
            # Count user's open tickets - agora com tickets inválidos já removidos
            from utils.config_manager import count_user_tickets
            user_tickets = count_user_tickets(guild_id, user_id, guild=interaction.guild)
            
            if user_tickets >= max_tickets:
                await interaction.response.send_message(
                    f"Você já atingiu o limite máximo de {max_tickets} ticket(s) aberto(s) para este painel!",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Get or create category
            category_id = panel_data.get("category_id")
            category = None
            
            if category_id:
                try:
                    category = interaction.guild.get_channel(int(category_id))
                except:
                    category = None
            
            if not category:
                # Try to find a "tickets" category or create one
                for guild_category in interaction.guild.categories:
                    if guild_category.name.lower() == "tickets":
                        category = guild_category
                        break
                
                if not category:
                    # Create a new category
                    try:
                        category = await interaction.guild.create_category("Tickets")
                    except Exception as e:
                        logger.error(f"Error creating category: {e}")
                        await interaction.followup.send("Não foi possível criar uma categoria para tickets!", ephemeral=True)
                        return
            
            # Create ticket number
            from utils.config_manager import get_next_ticket_number
            ticket_number = get_next_ticket_number(guild_id)
            
            # Get ticket type label if available
            ticket_type_label = None
            # Inicialização padrão para ticket_name para evitar erro
            ticket_name = f"ticket-{ticket_number}"
            if ticket_type:
                # Find the option label if available
                dropdown_options = panel_data.get("dropdown_options", [])
                for option in dropdown_options:
                    if option.get("value") == ticket_type:
                        ticket_type_label = option.get("label", ticket_type)
                        break
            
            # Format ticket name based on panel-specific config
            # Já carregamos config antes, mas vamos garantir que temos as informações mais recentes
            config = get_config(guild_id)
            
            # Get ticket name format from panel data, fall back to "ticket-{number}"
            ticket_format = panel_data.get("ticket_name_format", "ticket-{number}")
            
            # Clean username for channel name (remove spaces, special chars)
            clean_username = ''.join(c for c in interaction.user.name if c.isalnum() or c == '_').lower()
            if len(clean_username) > 10:
                clean_username = clean_username[:10]
            
            # Replace variables in format
            ticket_name = ticket_format
            # Replace {number} with ticket number
            ticket_name = ticket_name.replace("{number}", str(ticket_number))
            # Replace {user} with cleaned username
            ticket_name = ticket_name.replace("{user}", clean_username)
            # Replace {category} with ticket type if available
            if ticket_type_label:
                # Clean category name
                clean_category = ''.join(c for c in ticket_type_label if c.isalnum() or c == '_').lower()
                if len(clean_category) > 10:
                    clean_category = clean_category[:10]
                ticket_name = ticket_name.replace("{category}", clean_category)
            else:
                ticket_name = ticket_name.replace("{category}", "geral")
            
            # Enforce Discord channel name constraints: lowercase, no spaces, limited length
            ticket_name = ticket_name.lower().replace(' ', '-')
            if len(ticket_name) > 100:
                ticket_name = ticket_name[:100]
            
            print(f"Created ticket with name: {ticket_name}")
            
            # Create permissions for the ticket channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add support role permissions if set
            support_role_id = panel_data.get("support_role_id")
            if support_role_id:
                try:
                    support_role = interaction.guild.get_role(int(support_role_id))
                    if support_role:
                        overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                except Exception as e:
                    logger.error(f"Error getting support role: {e}")
            
            # Create the ticket channel
            try:
                channel = await interaction.guild.create_text_channel(
                    name=ticket_name,
                    category=category,
                    overwrites=overwrites
                )
            except Exception as e:
                logger.error(f"Error creating ticket channel: {e}")
                await interaction.followup.send(f"Não foi possível criar o ticket: {e}", ephemeral=True)
                return
            
            # Create ticket data
            ticket_data = {
                "user_id": user_id,
                "panel_id": panel_id,
                "channel_id": str(channel.id),
                "status": "open",
                "priority": "none",
                "claimed_by": None,
                "created_at": datetime.now().isoformat(),
                "closed_at": None,
                "closed_by": None,
                "close_reason": None,
                "last_activity": datetime.now().isoformat(),
                "added_users": []
            }
            
            # Save ticket data
            from utils.config_manager import create_ticket_data
            create_ticket_data(guild_id, str(channel.id), ticket_data)
            
            # Verificar se há uma mensagem personalizada de boas-vindas configurada para este painel
            welcome_message = panel_data.get("welcome_message", f"Olá {interaction.user.mention}, seu ticket foi criado com sucesso.")
            
            # Substituir variáveis na mensagem personalizada
            welcome_message = welcome_message.replace("{user}", interaction.user.mention)
            welcome_message = welcome_message.replace("{ticket_number}", str(ticket_number))
            welcome_message = welcome_message.replace("{server}", interaction.guild.name)
            
            # Create welcome message com design melhorado
            panel_color = panel_data.get("color", "blue")
            color_value = getattr(discord.Color, panel_color)() if hasattr(discord.Color, panel_color) else discord.Color.blue()
            
            embed = discord.Embed(
                title=f"📋 Ticket #{ticket_number}", 
                description=welcome_message,
                color=color_value
            )
            
            # Criar um rodapé com timestamp
            embed.set_footer(text=f"Criado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
            
            # Adicionar thumbnail do servidor, se disponível
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
                
            # Add panel info to embed
            panel_title = panel_data.get("title", "Painel sem título")
            
            # Campos para informações do ticket em duas colunas
            embed.add_field(
                name="🔍 Informações",
                value=f"**Categoria:** {panel_title}\n**Criado por:** {interaction.user.mention}\n**ID:** `{channel.id}`",
                inline=True
            )
            
            # Adicionar data/hora e status
            embed.add_field(
                name="⏰ Status",
                value="**Estado:** `Aberto`\n**Prioridade:** `Padrão`\n**Atendente:** `Nenhum`",
                inline=True
            )
            
            if ticket_type:
                # Find the option label if available
                dropdown_options = panel_data.get("dropdown_options", [])
                for option in dropdown_options:
                    if option.get("value") == ticket_type:
                        option_label = option.get("label", ticket_type)
                        embed.add_field(
                            name="📝 Assunto",
                            value=f"**{option_label}**",
                            inline=False
                        )
                        break
            
            # Adicionar instruções para o usuário
            instruction_message = panel_data.get("instruction_message", "• Descreva seu problema detalhadamente\n• Aguarde o atendimento da equipe\n• Use o botão `Fechar Ticket` quando finalizar\n• Seja paciente e cortês")
            embed.add_field(
                name="📢 Como utilizar o ticket",
                value=instruction_message,
                inline=False
            )
            
            # Create ticket management buttons com distribuição otimizada
            view = discord.ui.View(timeout=None)
            
            # ROW 0: Botões principais
            # Create close button - sempre visível
            close_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Fechar Ticket",
                emoji=Emoji.LOCK,
                custom_id="close_ticket",
                row=0
            )
            view.add_item(close_button)
            
            # Check which buttons to show based on config
            if config.get("show_claim_button", True):
                claim_button = discord.ui.Button(
                    style=discord.ButtonStyle.success,
                    label="Atender Ticket",
                    emoji=Emoji.WAVE,
                    custom_id="claim_ticket",
                    row=0
                )
                view.add_item(claim_button)
                
            if config.get("show_notify_button", True):
                notify_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Notificar Equipe",
                    emoji=Emoji.BELL,
                    custom_id="notify_ticket",
                    row=0
                )
                view.add_item(notify_button)
            
            # ROW 1: Botões de gerenciamento
            if config.get("show_priority_button", True):
                priority_button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Definir Prioridade",
                    emoji=Emoji.PRIORITY_NONE,
                    custom_id="prioritize_ticket",
                    row=1
                )
                view.add_item(priority_button)
            
            # Add user button
            add_user_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Adicionar Usuário",
                emoji=Emoji.USERS,
                custom_id="add_user_ticket",
                row=1
            )
            view.add_item(add_user_button)
            
            # Remove user button
            remove_user_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Remover Usuário",
                emoji=Emoji.DELETE,
                custom_id="remove_user_ticket",
                row=1
            )
            view.add_item(remove_user_button)
                
            # ROW 2: Botões adicionais
            if config.get("show_archive_button", True):
                archive_button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Arquivar Ticket",
                    emoji=Emoji.ARCHIVE,
                    custom_id="archive_ticket",
                    row=2
                )
                view.add_item(archive_button)
            
            # Transcript button (sempre visível)
            if config.get("show_transcript_button", True):
                transcript_button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Gerar Histórico",
                    emoji=Emoji.TRANSCRIPT,
                    custom_id="transcript_ticket",
                    row=2
                )
                view.add_item(transcript_button)
            
            # Send welcome message
            welcome_msg = await channel.send(
                content=f"{interaction.user.mention}",
                embed=embed,
                view=view
            )
            
            # Pin welcome message
            await welcome_msg.pin()
            
            # Notify support role if configured
            if config.get("notify_on_ticket_open", False) and support_role_id:
                try:
                    await channel.send(f"<@&{support_role_id}> Um novo ticket foi aberto!")
                except Exception as e:
                    logger.error(f"Error notifying support role: {e}")
            
            # Send confirmation to user
            await interaction.followup.send(f"Ticket criado com sucesso! Acesse: {channel.mention}", ephemeral=True)
            
            logger.info(f"Ticket created by {interaction.user.name} ({user_id}) - Channel: {channel.name} ({channel.id})")
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao criar o ticket: {e}", ephemeral=True)
