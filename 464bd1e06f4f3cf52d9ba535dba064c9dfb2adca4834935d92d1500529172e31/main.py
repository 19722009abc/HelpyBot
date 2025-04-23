import os
import sys
import discord
import logging
from discord.ext import commands
from discord import app_commands

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'DiscordTicketBot')))

from DiscordTicketBot.utils.database_sqlite import init_db, ShopService

init_db()
ShopService.initialize_default_items()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ticket_bot')

os.makedirs('data', exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = "MTM0ODAxNzczOTUzMjQ3MjM2Mg.GYMLqO.lsfzd8hOi5M9d8eJt7zQQHk5ughIzBQ3M0dfc8"
if not TOKEN:
    logger.error("Token não encontrado!")
    exit(1)

@bot.event
async def on_ready():
    logger.info(f'Bot conectado como {bot.user} (ID: {bot.user.id})')
    print(f'✅ Bot conectado como {bot.user} (ID: {bot.user.id})')
    try:
        print("🔍 Verificando tickets para canais inexistentes...")
        await verify_ticket_channels()
        print("✅ Verificação de tickets concluída")
    except Exception as e:
        logger.error(f"Erro ao verificar tickets: {e}")
        print(f"❌ Erro ao verificar tickets: {e}")
    try:
        print("📦 Carregando cogs...")
        await bot.load_extension("cogs.ticket_commands")
        print("- ticket_commands carregado")
        await bot.load_extension("cogs.ticket_buttons")
        print("- ticket_buttons carregado")
        await bot.load_extension("DiscordTicketBot.cogs.embed_commands")
        print("- embed_comandos carregado")
        await bot.load_extension("cogs.ticket_dropdowns")
        print("- ticket_dropdowns carregado")
        await bot.load_extension("cogs.ticket_modals")
        print("- ticket_modals carregado")
        await bot.load_extension("cogs.channel_manager")
        await bot.load_extension("cogs.premium")
        await bot.load_extension("cogs.economy")
        await bot.load_extension("cogs.level")
        logger.info("Todas as cogs carregadas com sucesso")
        print("✅ Todas as cogs carregadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao carregar cogs: {e}")
        print(f"❌ Erro ao carregar cogs: {e}")
    try:
        print("🔄 Sincronizando comandos...")
        synced = await bot.tree.sync()
        logger.info(f"{len(synced)} comando(s) sincronizado(s)")
        print(f"✅ {len(synced)} comando(s) sincronizado(s)")
    except Exception as e:
        logger.error(f"Falha ao sincronizar comandos: {e}")
        print(f"❌ Falha ao sincronizar comandos: {e}")
    activity = discord.Game(name="Gerenciando Tickets 🎟️")
    await bot.change_presence(status=discord.Status.online, activity=activity)

async def verify_ticket_channels():
    from DiscordTicketBot.utils.config_manager import _load_json, delete_ticket_data
    tickets_file = "data/tickets.json"
    tickets = _load_json(tickets_file)
    removed_count = 0
    for guild_id, guild_tickets in list(tickets.items()):
        try:
            guild = bot.get_guild(int(guild_id))
            if not guild:
                logger.warning(f"Guild {guild_id} não encontrada")
                continue
            for channel_id in list(guild_tickets.keys()):
                try:
                    channel = guild.get_channel(int(channel_id))
                    if not channel:
                        delete_ticket_data(guild_id, channel_id)
                        logger.info(f"Ticket removido: canal {channel_id} não existe mais no servidor {guild_id}")
                        removed_count += 1
                except Exception as e:
                    logger.error(f"Erro ao verificar canal {channel_id}: {e}")
        except Exception as e:
            logger.error(f"Erro ao verificar tickets do servidor {guild_id}: {e}")
    if removed_count > 0:
        logger.info(f"{removed_count} ticket(s) removido(s)")
        print(f"🗑️ {removed_count} ticket(s) removido(s)")

@bot.event
async def on_guild_join(guild):
    logger.info(f"Entrou em um novo servidor: {guild.name} (ID: {guild.id})")
    from DiscordTicketBot.utils.config_manager import initialize_guild_config
    initialize_guild_config(guild.id)

@bot.event
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("Você não tem permissão para usar este comando!", ephemeral=True)
    else:
        logger.error(f"Erro no comando: {error}")
        await interaction.response.send_message(f"Ocorreu um erro ao executar o comando: {error}", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
