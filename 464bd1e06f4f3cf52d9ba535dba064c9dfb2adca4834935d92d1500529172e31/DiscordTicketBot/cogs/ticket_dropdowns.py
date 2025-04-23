import discord
from discord.ext import commands
import logging
from datetime import datetime
from utils.ticket_manager import TicketManager
from utils.config_manager import get_panel_data, get_ticket_data, update_ticket_data

logger = logging.getLogger('ticket_bot.dropdowns')

class TicketDropdowns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle dropdown interactions for ticket system"""
        if not interaction.type == discord.InteractionType.component:
            return
        
        if not hasattr(interaction, 'data'):
            return
        
        # Check if it's a select menu interaction
        if 'component_type' not in interaction.data or interaction.data['component_type'] != 3:  # 3 is SelectMenu
            return
        
        if 'custom_id' not in interaction.data or 'values' not in interaction.data:
            return
        
        custom_id = interaction.data['custom_id']
        selected_values = interaction.data['values']
        
        if not selected_values:
            return
        
        try:
            # Handle ticket creation from dropdown
            if custom_id.startswith('create_ticket_dropdown:'):
                panel_id = custom_id.split(':')[1]
                selected_option = selected_values[0]
                
                await self.ticket_manager.create_ticket(
                    interaction, 
                    panel_id, 
                    ticket_type=selected_option
                )
                
            # Handle panel selection for editing
            elif custom_id == 'edit_panel_select':
                panel_id = selected_values[0]
                await self.ticket_manager.show_panel_editor(interaction, panel_id)
                
            # Handle panel selection for deletion
            elif custom_id == 'delete_panel_select':
                panel_id = selected_values[0]
                await self.ticket_manager.confirm_delete_panel(interaction, panel_id)
                
            # Handle color selection for panel
            elif custom_id == 'panel_color_select':
                color = selected_values[0]
                await self.handle_panel_color_selection(interaction, color)
                
            # Handle role selection for panel
            elif custom_id == 'panel_role_select':
                role_id = selected_values[0]
                await self.handle_panel_role_selection(interaction, role_id)
                
            # Handle category selection for panel
            elif custom_id == 'panel_category_select':
                category_id = selected_values[0]
                await self.handle_panel_category_selection(interaction, category_id)
                
            # Handle button style selection
            elif custom_id == 'button_style_select':
                style = selected_values[0]
                await self.handle_button_style_selection(interaction, style)
                
            # Handle dropdown option edit selection
            elif custom_id == 'edit_dropdown_option_select':
                option_id = selected_values[0]
                await self.handle_dropdown_option_edit(interaction, option_id)
                
            # Handle dropdown option delete selection
            elif custom_id == 'delete_dropdown_option_select':
                option_id = selected_values[0]
                await self.handle_dropdown_option_delete(interaction, option_id)
                
        except Exception as e:
            logger.error(f"Error handling dropdown interaction: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao processar a seleção: {e}", 
                ephemeral=True
            )
    
    async def handle_panel_color_selection(self, interaction: discord.Interaction, color: str):
        """Handle color selection for panel"""
        from utils.config_manager import get_edit_session, update_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update color in session
        session["color"] = color
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_panel_role_selection(self, interaction: discord.Interaction, role_id: str):
        """Handle role selection for panel"""
        from utils.config_manager import get_edit_session, update_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update role in session
        session["support_role_id"] = role_id
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_panel_category_selection(self, interaction: discord.Interaction, category_id: str):
        """Handle category selection for panel"""
        from utils.config_manager import get_edit_session, update_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update category in session
        session["category_id"] = category_id
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_editor(interaction, session.get("panel_id"), updated=True)
    
    async def handle_button_style_selection(self, interaction: discord.Interaction, style: str):
        """Handle button style selection for panel"""
        from utils.config_manager import get_edit_session, update_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Update button style in session
        session["button_style"] = style
        update_edit_session(user_id, guild_id, session)
        
        # Show updated panel preview
        await self.ticket_manager.show_panel_appearance_settings(interaction, updated=True)
    
    async def handle_dropdown_option_edit(self, interaction: discord.Interaction, option_id: str):
        """Handle selecting a dropdown option to edit"""
        from utils.config_manager import get_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Find the option data
        dropdown_options = session.get("dropdown_options", [])
        selected_option = None
        
        for option in dropdown_options:
            if option.get("value") == option_id:
                selected_option = option
                break
        
        if not selected_option:
            await interaction.response.send_message("Opção não encontrada!", ephemeral=True)
            return
        
        # Create modal for editing option
        modal = discord.ui.Modal(title="Editar Opção do Dropdown")
        
        label_input = discord.ui.TextInput(
            label="Título da Opção",
            placeholder="Título que aparece no dropdown",
            default=selected_option.get("label", ""),
            required=True,
            max_length=100
        )
        
        value_input = discord.ui.TextInput(
            label="Valor da Opção (ID interno)",
            placeholder="ID interno da opção (não altere se possível)",
            default=selected_option.get("value", ""),
            required=True,
            max_length=100
        )
        
        description_input = discord.ui.TextInput(
            label="Descrição da Opção",
            placeholder="Descrição que aparece no dropdown",
            default=selected_option.get("description", ""),
            required=True,
            max_length=100
        )
        
        emoji_input = discord.ui.TextInput(
            label="Emoji da Opção",
            placeholder="Emoji para exibir (opcional)",
            default=selected_option.get("emoji", ""),
            required=False,
            max_length=5
        )
        
        modal.add_item(label_input)
        modal.add_item(value_input)
        modal.add_item(description_input)
        modal.add_item(emoji_input)
        
        async def modal_callback(interaction):
            from utils.config_manager import update_edit_session
            
            # Get the updated option data
            updated_option = {
                "label": label_input.value,
                "value": value_input.value,
                "description": description_input.value
            }
            
            if emoji_input.value:
                updated_option["emoji"] = emoji_input.value
            
            # Update the option in the session
            for i, option in enumerate(dropdown_options):
                if option.get("value") == option_id:
                    dropdown_options[i] = updated_option
                    break
            
            session["dropdown_options"] = dropdown_options
            update_edit_session(user_id, guild_id, session)
            
            # Show updated dropdown options
            await self.ticket_manager.show_dropdown_options(interaction, updated=True)
        
        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)
    
    async def handle_dropdown_option_delete(self, interaction: discord.Interaction, option_id: str):
        """Handle deleting a dropdown option"""
        from utils.config_manager import get_edit_session, update_edit_session
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        session = get_edit_session(user_id, guild_id)
        if not session:
            await interaction.response.send_message("Sessão de edição expirada. Inicie novamente.", ephemeral=True)
            return
        
        # Remove the option from the list
        dropdown_options = session.get("dropdown_options", [])
        session["dropdown_options"] = [opt for opt in dropdown_options if opt.get("value") != option_id]
        update_edit_session(user_id, guild_id, session)
        
        # Show updated dropdown options
        await self.ticket_manager.show_dropdown_options(interaction, updated=True)

async def setup(bot):
    await bot.add_cog(TicketDropdowns(bot))
    logger.info("TicketDropdowns cog loaded")
