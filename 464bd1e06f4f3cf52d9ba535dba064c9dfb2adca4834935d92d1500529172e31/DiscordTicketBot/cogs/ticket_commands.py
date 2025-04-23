import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
from utils.ticket_manager import TicketManager
from utils.embed_creator import create_config_embed
from utils.emoji_config import Emoji

logger = logging.getLogger('ticket_bot.commands')

class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)
    
    @app_commands.command(name="ticket-config", description="Configura o sistema de tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_config(self, interaction: discord.Interaction):
        """Abre o painel de configuração do sistema de tickets"""
        try:
            logger.info(f"User {interaction.user.name} ({interaction.user.id}) used /ticket-config in {interaction.guild.name}")
            
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
            create_button.callback = self.ticket_manager.create_panel_callback
            
            # Edit Panel button
            edit_button = discord.ui.Button(
                style=discord.ButtonStyle.primary, 
                label="Editar Painel", 
                emoji=Emoji.EDIT
            )
            edit_button.callback = self.ticket_manager.edit_panel_callback
            
            # Delete Panel button
            delete_button = discord.ui.Button(
                style=discord.ButtonStyle.danger, 
                label="Excluir Painel", 
                emoji=Emoji.DELETE
            )
            delete_button.callback = self.ticket_manager.delete_panel_callback
            
            # Add buttons to view
            view.add_item(create_button)
            view.add_item(edit_button)
            view.add_item(delete_button)
            
            # Nota: O botão de configurações avançadas foi movido para o painel de edição
            
            # Send the config message
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in ticket_config command: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao abrir o painel de configuração: {e}", 
                ephemeral=True
            )

    @app_commands.command(name="ticket-setup", description="Envia um painel de tickets para o canal selecionado")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(
        self, 
        interaction: discord.Interaction,
        canal: Optional[discord.TextChannel] = None
    ):
        """Envia um painel de tickets configurado para o canal especificado"""
        try:
            logger.info(f"User {interaction.user.name} ({interaction.user.id}) used /ticket-setup in {interaction.guild.name}")
            print(f"User {interaction.user.name} ({interaction.user.id}) used /ticket-setup in {interaction.guild.name}")
            
            # Se nenhum canal foi especificado, use o canal atual
            if not canal:
                canal = interaction.channel
                print(f"No channel specified, using current channel: {canal.name}")
            else:
                print(f"Channel specified: {canal.name}")
                
            # Obter os painéis configurados pelo usuário
            from utils.config_manager import get_all_panels
            guild_id = str(interaction.guild.id)
            panels = get_all_panels(guild_id)
            print(f"Found {len(panels)} panels for guild {guild_id}")
            
            if not panels:
                print("No panels found, instructing user to create one first")
                await interaction.response.send_message(
                    "Você ainda não configurou nenhum painel de tickets. Use `/ticket-config` para criar um painel primeiro.",
                    ephemeral=True
                )
                return
                
            # Criar view com seletor de painéis
            view = discord.ui.View(timeout=300)
            
            # Adicionar seletor de painéis
            panel_select = discord.ui.Select(
                placeholder="Selecione um painel para enviar",
                custom_id="select_panel_to_send"
            )
            
            for panel_id, panel in panels.items():
                title = panel.get("title", "Painel sem título")
                panel_name = panel.get("panel_name", f"Painel #{panel_id[:8]}")
                panel_select.add_option(
                    label=panel_name,
                    value=panel_id,
                    description=f"{title[:30]}... | Criado: {panel.get('created_at', '')[:10]}"
                )
            
            async def panel_select_callback(panel_interaction: discord.Interaction):
                # Obter o painel selecionado
                selected_panel_id = panel_interaction.data["values"][0]
                print(f"Selected panel ID: {selected_panel_id}")
                panel_data = panels.get(selected_panel_id)
                panel_name = panel_data.get("panel_name", f"Painel #{selected_panel_id[:8]}")
                print(f"Panel data found: {panel_name}")
                
                if not panel_data:
                    print(f"Panel data not found for ID: {selected_panel_id}")
                    await panel_interaction.response.send_message(
                        "Painel selecionado não encontrado.",
                        ephemeral=True
                    )
                    return
                
                # Enviar o painel para o canal especificado
                print(f"Sending panel to channel: {canal.name}")
                success = await self.ticket_manager.send_panel_to_channel(
                    panel_interaction, 
                    selected_panel_id, 
                    canal
                )
                
                if success:
                    print(f"Panel successfully sent to channel: {canal.name}")
                    await panel_interaction.response.send_message(
                        f"Painel de tickets '{panel_name}' enviado com sucesso para {canal.mention}!",
                        ephemeral=True
                    )
                else:
                    print(f"Failed to send panel to channel: {canal.name}")
                    await panel_interaction.response.send_message(
                        f"Não foi possível enviar o painel '{panel_name}' para {canal.mention}.",
                        ephemeral=True
                    )
            
            panel_select.callback = panel_select_callback
            view.add_item(panel_select)
            
            # Adicionar botão de cancelar
            cancel_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Cancelar",
                emoji="❌"
            )
            
            async def cancel_callback(cancel_interaction: discord.Interaction):
                await cancel_interaction.response.edit_message(
                    content="Operação cancelada.",
                    embed=None,
                    view=None
                )
                
            cancel_button.callback = cancel_callback
            view.add_item(cancel_button)
            
            # Criar embed de seleção
            embed = create_config_embed(
                title="Enviar Painel de Tickets",
                description=f"Selecione um painel para enviar para o canal {canal.mention}.",
                color=discord.Color.blue()
            )
            
            # Enviar a mensagem com o seletor de painéis
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
                
        except Exception as e:
            logger.error(f"Error in ticket_setup command: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao criar o painel de tickets: {e}", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(TicketCommands(bot))
    logger.info("TicketCommands cog loaded")
