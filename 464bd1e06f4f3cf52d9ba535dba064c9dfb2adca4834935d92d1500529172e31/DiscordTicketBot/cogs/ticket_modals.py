import discord
from discord.ext import commands
import logging
from datetime import datetime
from utils.ticket_manager import TicketManager
from utils.config_manager import get_edit_session, update_edit_session

logger = logging.getLogger('ticket_bot.modals')

class TicketModals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle modal interactions for ticket system"""
        if not interaction.type == discord.InteractionType.modal_submit:
            return
            
        if not hasattr(interaction, 'data') or 'custom_id' not in interaction.data:
            return
        
        custom_id = interaction.data['custom_id']
        
        try:
            # Panel name configuration (identificação)
            if custom_id == 'panel_name_modal':
                await self.handle_panel_name(interaction)
                
            # Panel title configuration
            elif custom_id == 'panel_title_modal':
                await self.handle_panel_title(interaction)
                
            # Panel description configuration
            elif custom_id == 'panel_description_modal':
                await self.handle_panel_description(interaction)
                
            # Button text configuration
            elif custom_id == 'button_text_modal':
                await self.handle_button_text(interaction)
                
            # Button emoji configuration
            elif custom_id == 'button_emoji_modal':
                await self.handle_button_emoji(interaction)
                
            # Dropdown placeholder configuration
            elif custom_id == 'dropdown_placeholder_modal':
                await self.handle_dropdown_placeholder(interaction)
                
            # Add dropdown option
            elif custom_id == 'add_dropdown_option_modal':
                await self.handle_add_dropdown_option(interaction)
                
            # Max tickets per user configuration
            elif custom_id == 'max_tickets_modal':
                await self.handle_max_tickets(interaction)
                
            # Inactivity time configuration
            elif custom_id == 'inactivity_time_modal':
                await self.handle_inactivity_time(interaction)
                
        except Exception as e:
            logger.error(f"Error handling modal interaction: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao processar o formulário: {e}", 
                ephemeral=True
            )
    
    async def handle_panel_name(self, interaction: discord.Interaction):
        """Handle setting panel name (identificação) from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter nome de identificação do painel!", ephemeral=True)
            return
            
        panel_name = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update panel_name in session
        session["panel_name"] = panel_name
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_panel_title(self, interaction: discord.Interaction):
        """Handle setting panel title from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter título do painel!", ephemeral=True)
            return
            
        title = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update title in session
        session["title"] = title
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_panel_description(self, interaction: discord.Interaction):
        """Handle setting panel description from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter descrição do painel!", ephemeral=True)
            return
            
        description = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update description in session
        session["description"] = description
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_button_text(self, interaction: discord.Interaction):
        """Handle setting button text from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter texto do botão!", ephemeral=True)
            return
            
        button_text = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update button text in session
        session["button_text"] = button_text
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel appearance
        await self.ticket_manager.show_panel_appearance_settings(interaction, updated=True)
    
    async def handle_button_emoji(self, interaction: discord.Interaction):
        """Handle setting button emoji from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter emoji do botão!", ephemeral=True)
            return
            
        button_emoji = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update button emoji in session
        session["button_emoji"] = button_emoji
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel appearance
        await self.ticket_manager.show_panel_appearance_settings(interaction, updated=True)
    
    async def handle_dropdown_placeholder(self, interaction: discord.Interaction):
        """Handle setting dropdown placeholder from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter placeholder do dropdown!", ephemeral=True)
            return
            
        placeholder = components[0]['components'][0].get('value', '')
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update dropdown placeholder in session
        session["dropdown_placeholder"] = placeholder
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel appearance
        await self.ticket_manager.show_panel_appearance_settings(interaction, updated=True)
    
    async def handle_add_dropdown_option(self, interaction: discord.Interaction):
        """Handle adding dropdown option from modal"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Get components from the modal
        components = interaction.data.get('components', [])
        if len(components) < 3:
            await interaction.response.send_message("Erro ao obter dados da opção do dropdown!", ephemeral=True)
            return
            
        label = components[0]['components'][0].get('value', '')
        value = components[1]['components'][0].get('value', '')
        description = components[2]['components'][0].get('value', '')
        emoji = components[3]['components'][0].get('value', '') if len(components) > 3 else None
        
        # Get edit session
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Create the new option
        new_option = {
            "label": label,
            "value": value,
            "description": description
        }
        
        if emoji:
            new_option["emoji"] = emoji
        
        # Add to dropdown options
        dropdown_options = session.get("dropdown_options", [])
        dropdown_options.append(new_option)
        session["dropdown_options"] = dropdown_options
        update_edit_session(user_id, guild_id, session)
        
        # Show updated dropdown options
        await self.ticket_manager.show_dropdown_options(interaction, updated=True)
    
    async def handle_max_tickets(self, interaction: discord.Interaction):
        """Handle setting max tickets per user"""
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter o valor máximo de tickets!", ephemeral=True)
            return
            
        try:
            max_tickets = int(components[0]['components'][0].get('value', '1'))
            
            # Validate range
            if max_tickets < 1:
                max_tickets = 1
            elif max_tickets > 10:
                max_tickets = 10
                
            # Update config
            from utils.config_manager import update_config
            guild_id = str(interaction.guild_id)
            update_config(guild_id, "max_tickets_per_user", max_tickets)
            
            # Return to advanced settings
            await self.ticket_manager.show_advanced_settings(interaction, updated=True)
            
        except ValueError:
            await interaction.response.send_message("Valor inválido! Digite um número de 1 a 10.", ephemeral=True)
    
    async def handle_inactivity_time(self, interaction: discord.Interaction):
        """Handle setting inactivity time for ticket auto-close"""
        # Get components from the modal
        components = interaction.data.get('components', [])
        if not components or not components[0].get('components', []):
            await interaction.response.send_message("Erro ao obter o tempo de inatividade!", ephemeral=True)
            return
            
        try:
            hours = int(components[0]['components'][0].get('value', '72'))
            
            # Validate range
            if hours < 0:
                hours = 0
            elif hours > 720:
                hours = 720
                
            # Update config
            from utils.config_manager import update_config
            guild_id = str(interaction.guild_id)
            update_config(guild_id, "inactivity_close_time", hours)
            
            # Return to advanced settings
            await self.ticket_manager.show_advanced_settings(interaction, updated=True)
            
        except ValueError:
            await interaction.response.send_message("Valor inválido! Digite um número de 0 a 720.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketModals(bot))
    logger.info("TicketModals cog loaded")
