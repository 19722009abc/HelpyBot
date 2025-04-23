import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from utils.ticket_manager import TicketManager
from utils.emoji_config import Emoji
from utils.config_manager import get_ticket_data, update_ticket_data, get_config, delete_ticket_data, count_user_tickets

logger = logging.getLogger('ticket_bot.buttons')

class TicketButtons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions for ticket system"""
        if not interaction.type == discord.InteractionType.component:
            return
            
        if not hasattr(interaction, 'data') or 'custom_id' not in interaction.data:
            return
        
        custom_id = interaction.data['custom_id']
        
        try:
            # Handle ticket creation button
            if custom_id.startswith('create_ticket:'):
                panel_id = custom_id.split(':')[1]
                await self.ticket_manager.create_ticket(interaction, panel_id)
                
            # Handle close ticket button
            elif custom_id == 'close_ticket':
                await self.handle_close_ticket(interaction)
                
            # Handle claim ticket button
            elif custom_id == 'claim_ticket':
                await self.handle_claim_ticket(interaction)
                
            # Handle prioritize ticket button
            elif custom_id == 'prioritize_ticket':
                await self.handle_prioritize_ticket(interaction)
                
            # Handle notify button
            elif custom_id == 'notify_ticket':
                await self.handle_notify_ticket(interaction)
                
            # Handle archive button
            elif custom_id == 'archive_ticket':
                await self.handle_archive_ticket(interaction)
                
            # Handle add user button
            elif custom_id == 'add_user_ticket':
                await self.handle_add_user(interaction)
                
            # Handle remove user button
            elif custom_id == 'remove_user_ticket':
                await self.handle_remove_user(interaction)
                
            # Handle transcript button
            elif custom_id == 'transcript_ticket':
                await self.handle_transcript(interaction)
                
        except Exception as e:
            logger.error(f"Error handling button interaction: {e}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao processar o botão: {e}", 
                ephemeral=True
            )
    
    async def handle_close_ticket(self, interaction: discord.Interaction):
        """Handle closing a ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
            
        config = get_config(guild_id)
        
        # Check if non-admins can close tickets
        if not interaction.user.guild_permissions.administrator and not config.get("allow_member_close", False):
            if str(interaction.user.id) != ticket_data.get("user_id") and str(interaction.user.id) != ticket_data.get("claimed_by"):
                await interaction.response.send_message("Você não tem permissão para fechar este ticket!", ephemeral=True)
                return
        
        # Check if we need to ask for a reason
        if config.get("require_reason_on_close", False):
            # Criar um select com motivos padrões + opção personalizada
            view = discord.ui.View(timeout=300)
            
            # Motivos padrões para fechamento
            select = discord.ui.Select(
                placeholder="Selecione um motivo para o fechamento",
                custom_id="close_reason_select"
            )
            
            reasons = [
                ("Problema resolvido", "O problema foi resolvido com sucesso."),
                ("Usuário atendido", "O usuário foi atendido com sucesso."),
                ("Solicitação concluída", "A solicitação do usuário foi concluída."),
                ("Inatividade", "O ticket foi fechado por inatividade."),
                ("Duplicado", "Este ticket é um duplicado de outro ticket."),
                ("Spam", "Este ticket foi identificado como spam."),
                ("Outro", "Informar motivo personalizado...")
            ]
            
            for reason_id, reason_text in reasons:
                select.add_option(
                    label=reason_id,
                    value=reason_text,
                    description=f"Motivo: {reason_id}"
                )
                
            async def select_callback(select_interaction: discord.Interaction):
                selected_reason = select_interaction.data["values"][0]
                
                # Se selecionou "Outro", abrir modal para motivo personalizado
                if selected_reason == "Informar motivo personalizado...":
                    modal = discord.ui.Modal(title="Motivo Personalizado")
                    
                    # Add text input for reason
                    custom_reason = discord.ui.TextInput(
                        label="Motivo do Fechamento",
                        placeholder="Informe o motivo para fechar este ticket",
                        style=discord.TextStyle.paragraph,
                        max_length=1000,
                        required=True
                    )
                    modal.add_item(custom_reason)
                    
                    async def modal_callback(modal_interaction: discord.Interaction):
                        await self.close_ticket(modal_interaction, custom_reason.value)
                        
                    modal.on_submit = modal_callback
                    await select_interaction.response.send_modal(modal)
                else:
                    # Usar o motivo selecionado diretamente
                    await self.close_ticket(select_interaction, selected_reason)
            
            select.callback = select_callback
            view.add_item(select)
            
            # Botão para cancelar o fechamento
            cancel_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Cancelar",
                emoji="❌"
            )
            
            async def cancel_callback(cancel_interaction: discord.Interaction):
                await cancel_interaction.response.edit_message(
                    content="Fechamento de ticket cancelado.",
                    view=None,
                    embed=None
                )
                
            cancel_button.callback = cancel_callback
            view.add_item(cancel_button)
            
            # Enviar a mensagem com o select
            embed = discord.Embed(
                title="Fechamento de Ticket",
                description="Selecione o motivo para fechar este ticket:",
                color=discord.Color.orange()
            )
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await self.close_ticket(interaction, "Ticket fechado sem motivo especificado.")
    
    async def close_ticket(self, interaction: discord.Interaction, reason: str):
        """Actually close the ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            try:
                await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            except discord.errors.InteractionResponded:
                await interaction.followup.send("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Get panel data to use panel-specific configuration
        panel_id = ticket_data.get("panel_id")
        from utils.config_manager import get_panel_data
        panel_data = get_panel_data(guild_id, panel_id) or {}
        
        # Update ticket data
        ticket_data["status"] = "closed"
        ticket_data["closed_at"] = datetime.now().isoformat()
        ticket_data["closed_by"] = str(interaction.user.id)
        ticket_data["close_reason"] = reason
        
        update_ticket_data(guild_id, channel_id, ticket_data)
        
        # Create closing embed
        embed = discord.Embed(
            title="Ticket Fechado",
            description=f"Este ticket foi fechado por {interaction.user.mention}\n**Motivo:** {reason}",
            color=discord.Color.red()
        )
        
        # Adicionando informação sobre o que acontecerá com o canal
        embed.add_field(
            name="⏱️ Remoção do Canal", 
            value="Este canal será excluído em 10 segundos. O histórico de mensagens será mantido nos registros do sistema.",
            inline=False
        )
        
        try:
            await interaction.response.send_message(embed=embed)
        except discord.errors.InteractionResponded:
            await interaction.followup.send(embed=embed)
            
        # Fechar o canal atual
        try:
            channel = interaction.channel
            if not channel:
                logger.error("Canal não encontrado ao tentar fechar o ticket")
                return
                
            # Removendo permissões de escrita para todos os usuários envolvidos
            if ticket_data.get("user_id"):
                try:
                    user_id = int(ticket_data.get("user_id"))
                    member = await interaction.guild.fetch_member(user_id)
                    if member:
                        await channel.set_permissions(member, send_messages=False)
                        # Notificar o usuário por DM que o ticket foi fechado
                        try:
                            user_embed = discord.Embed(
                                title="Seu Ticket Foi Fechado",
                                description=f"O ticket `{channel.name}` foi fechado por {interaction.user.name}.\n**Motivo:** {reason}",
                                color=discord.Color.orange()
                            )
                            await member.send(embed=user_embed)
                        except:
                            # Usuário pode ter DMs desativadas
                            pass
                except Exception as e:
                    logger.error(f"Error updating permissions for ticket creator {user_id}: {e}")
                
            # Remover permissões dos usuários adicionados
            added_users = ticket_data.get("added_users", [])
            for added_user_id in added_users:
                try:
                    user_id = int(added_user_id)
                    member = await interaction.guild.fetch_member(user_id)
                    if member:
                        await channel.set_permissions(member, send_messages=False)
                except Exception as e:
                    logger.error(f"Error updating permissions for added user {added_user_id}: {e}")
            
            # Alterar o nome do canal para mostrar que está fechado
            try:
                new_name = f"fechado-{channel.name}"
                if not channel.name.startswith("fechado-"):
                    await channel.edit(name=new_name)
                    logger.info(f"Renamed ticket channel to {new_name}")
            except Exception as e:
                logger.error(f"Error renaming ticket channel: {e}")
            
            # Aguardar alguns segundos antes de excluir o canal
            await asyncio.sleep(10)
            
            # Agora vamos realmente excluir o canal
            try:
                await channel.delete(reason=f"Ticket fechado - {reason}")
                logger.info(f"Ticket channel {channel.name} ({channel_id}) deleted")
                
                # Atualiza os dados do ticket
                ticket_data["channel_deleted"] = True
                ticket_data["deleted_at"] = datetime.now().isoformat()
                update_ticket_data(guild_id, channel_id, ticket_data)
                
            except Exception as e:
                logger.error(f"Error deleting ticket channel: {e}")
                # Se não conseguir deletar, pelo menos arquivar
                try:
                    await channel.edit(archived=True)
                    logger.info(f"Couldn't delete channel, archived instead: {channel.name} ({channel_id})")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error closing ticket channel: {e}")
            try:
                await interaction.followup.send(f"Ocorreu um erro ao fechar o ticket: {e}", ephemeral=True)
            except:
                pass
    
    async def handle_claim_ticket(self, interaction: discord.Interaction):
        """Handle claiming a ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Check if ticket is already claimed
        if ticket_data.get("claimed_by"):
            claimed_user = await self.bot.fetch_user(int(ticket_data.get("claimed_by")))
            claimed_by_name = claimed_user.name if claimed_user else "Desconhecido"
            
            # If claimed by the same user, unclaim
            if str(interaction.user.id) == ticket_data.get("claimed_by"):
                ticket_data["claimed_by"] = None
                update_ticket_data(guild_id, channel_id, ticket_data)
                
                embed = discord.Embed(
                    title="Ticket Liberado",
                    description=f"{interaction.user.mention} liberou este ticket.",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"Este ticket já está sendo atendido por {claimed_by_name}!", 
                    ephemeral=True
                )
        else:
            # Claim the ticket
            ticket_data["claimed_by"] = str(interaction.user.id)
            ticket_data["last_activity"] = datetime.now().isoformat()
            update_ticket_data(guild_id, channel_id, ticket_data)
            
            embed = discord.Embed(
                title="Ticket Atendido",
                description=f"{interaction.user.mention} está atendendo este ticket.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
    
    async def handle_prioritize_ticket(self, interaction: discord.Interaction):
        """Handle setting ticket priority"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Create view with priority options
        view = discord.ui.View(timeout=60)
        
        # Priority buttons with different colors
        priorities = [
            ("none", "Sem Prioridade", discord.ButtonStyle.secondary, Emoji.PRIORITY_NONE),
            ("low", "Prioridade Baixa", discord.ButtonStyle.success, Emoji.PRIORITY_LOW),
            ("medium", "Prioridade Média", discord.ButtonStyle.primary, Emoji.PRIORITY_MEDIUM),
            ("high", "Prioridade Alta", discord.ButtonStyle.danger, Emoji.PRIORITY_HIGH)
        ]
        
        for value, label, style, emoji in priorities:
            button = discord.ui.Button(style=style, label=label, emoji=emoji, custom_id=f"priority:{value}")
            
            async def button_callback(interaction, priority=value):
                ticket_data["priority"] = priority
                ticket_data["last_activity"] = datetime.now().isoformat()
                update_ticket_data(guild_id, channel_id, ticket_data)
                
                # Format priority name
                priority_formatted = {
                    "none": "Sem Prioridade",
                    "low": "Baixa",
                    "medium": "Média",
                    "high": "Alta"
                }.get(priority, "Desconhecida")
                
                # Priority color
                priority_color = {
                    "none": discord.Color.light_grey(),
                    "low": discord.Color.green(),
                    "medium": discord.Color.blue(),
                    "high": discord.Color.red()
                }.get(priority, discord.Color.light_grey())
                
                embed = discord.Embed(
                    title="Prioridade Atualizada",
                    description=f"{interaction.user.mention} definiu a prioridade deste ticket como **{priority_formatted}**.",
                    color=priority_color
                )
                await interaction.response.send_message(embed=embed)
            
            button.callback = lambda i, b=button: button_callback(i, b.custom_id.split(':')[1])
            view.add_item(button)
        
        await interaction.response.send_message(
            "Selecione a prioridade para este ticket:", 
            view=view, 
            ephemeral=True
        )
    
    async def handle_notify_ticket(self, interaction: discord.Interaction):
        """Handle notifying support team about a ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Get panel data to find the support role
        panel_id = ticket_data.get("panel_id")
        from utils.config_manager import get_panel_data
        panel_data = get_panel_data(guild_id, panel_id)
        
        if not panel_data or not panel_data.get("support_role_id"):
            await interaction.response.send_message("Não foi possível encontrar o cargo de suporte para este ticket!", ephemeral=True)
            return
        
        support_role_id = panel_data.get("support_role_id")
        
        # Create notification message
        embed = discord.Embed(
            title="Notificação de Ticket",
            description=f"{interaction.user.mention} solicitou assistência neste ticket.",
            color=discord.Color.gold()
        )
        
        # Add ticket information
        user_id = ticket_data.get("user_id")
        try:
            user = await self.bot.fetch_user(int(user_id))
            embed.add_field(name="Criado por", value=user.mention if user else "Desconhecido")
        except:
            embed.add_field(name="Criado por", value="Usuário não encontrado")
        
        # Add priority if set
        priority = ticket_data.get("priority", "none")
        if priority != "none":
            priority_formatted = {
                "low": "Baixa",
                "medium": "Média",
                "high": "Alta"
            }.get(priority, "Desconhecida")
            embed.add_field(name="Prioridade", value=priority_formatted)
        
        # Update last activity
        ticket_data["last_activity"] = datetime.now().isoformat()
        update_ticket_data(guild_id, channel_id, ticket_data)
        
        # Send notification with support role mention
        await interaction.response.send_message(
            f"<@&{support_role_id}>",
            embed=embed
        )
    
    async def handle_archive_ticket(self, interaction: discord.Interaction):
        """Handle archiving a ticket without closing it"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Update ticket data
        ticket_data["status"] = "archived"
        ticket_data["last_activity"] = datetime.now().isoformat()
        update_ticket_data(guild_id, channel_id, ticket_data)
        
        # Create archive message
        embed = discord.Embed(
            title="Ticket Arquivado",
            description=f"{interaction.user.mention} arquivou este ticket. O canal permanecerá visível, mas o ticket está marcado como arquivado.",
            color=discord.Color.dark_blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def handle_add_user(self, interaction: discord.Interaction):
        """Handle adding a user to the ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Create a user select menu
        view = discord.ui.View(timeout=300)
        
        # Create user select
        user_select = discord.ui.UserSelect(
            placeholder="Selecione o usuário para adicionar",
            custom_id="add_user_select",
            min_values=1, 
            max_values=1
        )
        
        async def select_callback(select_interaction: discord.Interaction):
            user = select_interaction.data["values"][0]
            user_id = int(user)
            
            try:
                user_obj = await self.bot.fetch_user(user_id)
                if not user_obj:
                    await select_interaction.response.send_message("Usuário não encontrado!", ephemeral=True)
                    return
                
                # Check if user already added
                added_users = ticket_data.get("added_users", [])
                if str(user_id) in added_users:
                    await select_interaction.response.send_message(
                        f"O usuário {user_obj.mention} já está adicionado ao ticket!", 
                        ephemeral=True
                    )
                    return
                
                # Add user to ticket
                added_users.append(str(user_id))
                ticket_data["added_users"] = added_users
                ticket_data["last_activity"] = datetime.now().isoformat()
                update_ticket_data(guild_id, channel_id, ticket_data)
                
                # Add user to channel permissions
                try:
                    channel = select_interaction.channel
                    member = await interaction.guild.fetch_member(user_id)
                    await channel.set_permissions(member, read_messages=True, send_messages=True)
                except Exception as e:
                    logger.error(f"Error setting permissions for user {user_id}: {e}")
                    await select_interaction.response.send_message(
                        f"Ocorreu um erro ao definir permissões para {user_obj.mention}: {e}",
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="Usuário Adicionado",
                    description=f"{select_interaction.user.mention} adicionou {user_obj.mention} ao ticket.",
                    color=discord.Color.green()
                )
                await select_interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f"Error adding user to ticket: {e}")
                await select_interaction.response.send_message(
                    f"Ocorreu um erro ao adicionar o usuário: {e}", 
                    ephemeral=True
                )
        
        user_select.callback = select_callback
        view.add_item(user_select)
        
        # Add cancel button
        cancel_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Cancelar",
            custom_id="cancel_add_user"
        )
        
        async def cancel_callback(cancel_interaction: discord.Interaction):
            await cancel_interaction.response.edit_message(
                content="Ação cancelada.",
                view=None
            )
            
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)
        
        await interaction.response.send_message(
            "Selecione o usuário que deseja adicionar ao ticket:",
            view=view,
            ephemeral=True
        )
        
    async def handle_remove_user(self, interaction: discord.Interaction):
        """Handle removing a user from the ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        # Check if there are users to remove
        added_users = ticket_data.get("added_users", [])
        if not added_users:
            await interaction.response.send_message("Não há usuários adicionados a este ticket!", ephemeral=True)
            return
        
        # Create a select menu with added users
        view = discord.ui.View(timeout=300)
        
        # Create user select from added users list
        select = discord.ui.Select(
            placeholder="Selecione o usuário para remover",
            custom_id="remove_user_select"
        )
        
        # Add users to select menu
        for user_id in added_users:
            try:
                user = await self.bot.fetch_user(int(user_id))
                select.add_option(
                    label=f"{user.name}",
                    value=user_id,
                    description=f"ID: {user_id}"
                )
            except Exception as e:
                logger.error(f"Error fetching user {user_id}: {e}")
                select.add_option(
                    label=f"Usuário ID: {user_id}",
                    value=user_id,
                    description=f"Não foi possível carregar o nome do usuário"
                )
        
        async def select_callback(select_interaction: discord.Interaction):
            removed_user_id = select_interaction.data["values"][0]
            
            try:
                # Remove user from ticket data
                if removed_user_id in added_users:
                    added_users.remove(removed_user_id)
                    ticket_data["added_users"] = added_users
                    ticket_data["last_activity"] = datetime.now().isoformat()
                    update_ticket_data(guild_id, channel_id, ticket_data)
                    
                    # Remove user from channel permissions
                    try:
                        channel = select_interaction.channel
                        user = await self.bot.fetch_user(int(removed_user_id))
                        member = await interaction.guild.fetch_member(int(removed_user_id))
                        if member:
                            await channel.set_permissions(member, overwrite=None)
                    except Exception as e:
                        logger.error(f"Error removing permissions for user {removed_user_id}: {e}")
                    
                    user_mention = f"<@{removed_user_id}>"
                    try:
                        user = await self.bot.fetch_user(int(removed_user_id))
                        user_mention = user.mention
                    except:
                        pass
                    
                    embed = discord.Embed(
                        title="Usuário Removido",
                        description=f"{select_interaction.user.mention} removeu {user_mention} do ticket.",
                        color=discord.Color.red()
                    )
                    await select_interaction.response.send_message(embed=embed)
                else:
                    await select_interaction.response.send_message(
                        "Este usuário não está na lista de usuários adicionados!", 
                        ephemeral=True
                    )
                    
            except Exception as e:
                logger.error(f"Error removing user from ticket: {e}")
                await select_interaction.response.send_message(
                    f"Ocorreu um erro ao remover o usuário: {e}", 
                    ephemeral=True
                )
        
        select.callback = select_callback
        view.add_item(select)
        
        # Add cancel button
        cancel_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Cancelar",
            custom_id="cancel_remove_user"
        )
        
        async def cancel_callback(cancel_interaction: discord.Interaction):
            await cancel_interaction.response.edit_message(
                content="Ação cancelada.",
                view=None
            )
            
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)
        
        await interaction.response.send_message(
            "Selecione o usuário que deseja remover do ticket:",
            view=view,
            ephemeral=True
        )
    
    async def handle_transcript(self, interaction: discord.Interaction):
        """Handle creating a transcript of the ticket"""
        guild_id = str(interaction.guild_id)
        channel_id = str(interaction.channel_id)
        
        ticket_data = get_ticket_data(guild_id, channel_id)
        if not ticket_data:
            await interaction.response.send_message("Este canal não é um ticket válido!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.channel
            messages = []
            
            # Collect messages (up to 100 for simplicity)
            async for message in channel.history(limit=100, oldest_first=True):
                messages.append({
                    'author': message.author.name,
                    'content': message.content,
                    'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'attachments': [a.url for a in message.attachments]
                })
            
            # Create transcript embed
            embed = discord.Embed(
                title=f"Transcrição do Ticket: {channel.name}",
                description=f"Transcrição gerada por {interaction.user.mention}",
                color=discord.Color.blue()
            )
            
            # Create transcript text
            transcript_text = f"# Transcrição do Ticket: {channel.name}\n\n"
            transcript_text += f"Ticket aberto por <@{ticket_data.get('user_id')}>\n"
            transcript_text += f"Data de abertura: {ticket_data.get('created_at')}\n\n"
            
            for msg in messages:
                transcript_text += f"**{msg['author']}** ({msg['timestamp']}):\n"
                transcript_text += f"{msg['content']}\n"
                
                if msg['attachments']:
                    transcript_text += "Anexos:\n"
                    for url in msg['attachments']:
                        transcript_text += f"- {url}\n"
                
                transcript_text += "\n"
            
            # Split transcript if too long
            if len(transcript_text) > 2000:
                parts = [transcript_text[i:i+1990] for i in range(0, len(transcript_text), 1990)]
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                for i, part in enumerate(parts):
                    await interaction.followup.send(f"Parte {i+1}/{len(parts)}:\n```{part}```", ephemeral=True)
            else:
                embed.description += f"\n```{transcript_text}```"
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error creating transcript: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao gerar a transcrição: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketButtons(bot))
    logger.info("TicketButtons cog loaded")
