import discord
from discord import app_commands
from discord.ext import commands
import logging
import datetime
import random
import sqlite3
import asyncio

from utils.database_sqlite import UserService, ShopService
from cogs.level import XPGainManager

# Configuração do logger
logger = logging.getLogger("CartoonBot")

# Chances de ganhar fragmentos nos mini-jogos (percentual %)
FRAGMENT_CHANCES = {
    "facil": {
        "comum": 80,     # 80% de chance
        "incomum": 30,   # 30% de chance
        "raro": 10,      # 10% de chance
        "épico": 0,      # 0% de chance
        "lendário": 0    # 0% de chance
    },
    "medio": {
        "comum": 90,     # 90% de chance
        "incomum": 50,   # 50% de chance
        "raro": 20,      # 20% de chance
        "épico": 5,      # 5% de chance
        "lendário": 0    # 0% de chance
    },
    "dificil": {
        "comum": 100,    # 100% de chance
        "incomum": 70,   # 70% de chance
        "raro": 40,      # 40% de chance
        "épico": 15,     # 15% de chance
        "lendário": 3    # 3% de chance
    }
}

# Lista de perguntas para o quiz
QUIZ_QUESTIONS = [
    {
        "pergunta": "Qual é o planeta mais próximo do Sol?",
        "opcoes": ["Terra", "Mercúrio", "Vênus", "Marte"],
        "resposta": 1,
        "dificuldade": "fácil"
    },
    {
        "pergunta": "Qual é o maior oceano da Terra?",
        "opcoes": ["Atlântico", "Índico", "Pacífico", "Ártico"],
        "resposta": 2,
        "dificuldade": "fácil"
    },
    {
        "pergunta": "Quem escreveu 'Dom Quixote'?",
        "opcoes": ["William Shakespeare", "Miguel de Cervantes", "Machado de Assis", "Charles Dickens"],
        "resposta": 1,
        "dificuldade": "médio"
    },
    {
        "pergunta": "Qual é o elemento químico mais abundante no universo?",
        "opcoes": ["Oxigênio", "Carbono", "Ferro", "Hidrogênio"],
        "resposta": 3,
        "dificuldade": "médio"
    },
    {
        "pergunta": "Qual é a capital da Austrália?",
        "opcoes": ["Sydney", "Melbourne", "Canberra", "Perth"],
        "resposta": 2,
        "dificuldade": "médio"
    },
    {
        "pergunta": "Em que ano ocorreu a Revolução Francesa?",
        "opcoes": ["1789", "1776", "1804", "1649"],
        "resposta": 0,
        "dificuldade": "difícil"
    },
    {
        "pergunta": "Qual é o menor país do mundo em área?",
        "opcoes": ["Mônaco", "San Marino", "Vaticano", "Liechtenstein"],
        "resposta": 2,
        "dificuldade": "difícil"
    },
    {
        "pergunta": "Quantos ossos tem o corpo humano adulto?",
        "opcoes": ["186", "206", "230", "286"],
        "resposta": 1,
        "dificuldade": "médio"
    },
    {
        "pergunta": "Qual destes não é um planeta anão do Sistema Solar?",
        "opcoes": ["Plutão", "Éris", "Ceres", "Titan"],
        "resposta": 3,
        "dificuldade": "difícil"
    },
    {
        "pergunta": "Quem pintou a 'Mona Lisa'?",
        "opcoes": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Michelangelo"],
        "resposta": 2,
        "dificuldade": "fácil"
    }
]

# Valores já definidos no início do arquivo

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="carteira", description="Veja sua carteira digital ou a de outro usuário")
    @app_commands.describe(
        usuario="Usuário opcional para ver a carteira (deixe em branco para ver a sua)"
    )
    async def carteira(self, interaction: discord.Interaction, usuario: discord.Member = None):
        # Usar ephemeral=True para mensagens privadas
        await interaction.response.defer(ephemeral=True)

        # Se não for especificado um usuário, mostra a carteira do próprio autor
        target_user = usuario or interaction.user
        target_id = target_user.id
        target_name = target_user.name

        # Verificar se está vendo a própria carteira ou de outro usuário
        is_self = target_user.id == interaction.user.id

        try:
            # Verificar se o usuário existe no banco
            user = UserService.ensure_user_exists(target_id, target_name)

            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR CARTEIRA",
                    description="Não foi possível acessar os dados solicitados. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Obter dados do usuário
            user_coins = user[2]
            is_premium = user[3] if len(user) > 3 else False
            premium_until = user[4] if len(user) > 4 else None

            # Criar embed com visual cartoon através de formatação de texto
            embed = discord.Embed(
                title=f"💰 CARTEIRA DIGITAL {'• SEU PERFIL' if is_self else '• PERFIL'} 💰",
                description=f"{'**Sua**' if is_self else f'**{target_name}**'} carteira financeira:",
                color=discord.Color.gold() if is_premium else discord.Color.blue()
            )

            # Adicionar faixa decorativa no topo para aspecto visual
            if is_premium:
                embed.description = f"```ansi\n\u001b[33;1m{'★' * 30}\u001b[0m\n```" + embed.description

            # Campo principal - saldo com visual melhorado
            embed.add_field(
                name=f"💎 {'SEU ' if is_self else ''}SALDO ATUAL",
                value=f"```fix\n{user_coins:,} coins```",
                inline=False
            )

            # Adicionar informações adicionais
            embed.add_field(
                name="👤 Titular",
                value=f"`{target_name}`",
                inline=True
            )

            embed.add_field(
                name="📅 Data de Consulta",
                value=f"`{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}`",
                inline=True
            )

            # Status premium
            if is_premium:
                if premium_until:
                    # Converter premium_until para datetime se for string
                    if isinstance(premium_until, str):
                        try:
                            premium_until = datetime.datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                        except ValueError:
                            premium_until = None

                    # Calcular dias restantes se for datetime
                    if premium_until:
                        days_left = (premium_until - datetime.datetime.now()).days
                        until_str = f"{premium_until.strftime('%d/%m/%Y')} ({days_left} dias restantes)"
                    else:
                        until_str = "Permanente"
                else:
                    until_str = "Permanente"

                embed.add_field(
                    name="✨ STATUS PREMIUM",
                    value=f"```yaml\nATIVO até {until_str}```",
                    inline=False
                )

                # Adicionar campo com benefícios
                embed.add_field(
                    name="🌟 Benefícios Ativos",
                    value="• +50% de coins no daily\n• Visual exclusivo dourado\n• Cooldown reduzido (20h vs 24h)\n• Mais benefícios em breve!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✨ STATUS PREMIUM",
                    value="```\nPADRÃO (Use /premium para melhorar)```",
                    inline=False
                )

            # Adicionar estatísticas se disponíveis
            try:
                transactions_count = 0
                amount_received = 0
                amount_sent = 0

                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()

                # Contar número total de transações
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (str(target_id),))
                transactions_count = cursor.fetchone()[0] or 0

                # Obter total recebido (valores positivos)
                cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND amount > 0", (str(target_id),))
                amount_received = cursor.fetchone()[0] or 0

                # Obter total enviado (valores negativos)
                cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND amount < 0", (str(target_id),))
                amount_sent = abs(cursor.fetchone()[0] or 0)

                cursor.close()
                conn.close()

                # Adicionar campo de estatísticas
                if transactions_count > 0:
                    embed.add_field(
                        name="📊 ESTATÍSTICAS",
                        value=(
                            f"• Transações: **{transactions_count}**\n"
                            f"• Recebido: **{amount_received:,}** coins\n"
                            f"• Enviado: **{amount_sent:,}** coins\n"
                        ),
                        inline=False
                    )
            except Exception as stats_error:
                logger.error(f"Erro ao obter estatísticas: {stats_error}")

            # Adicionar dicas úteis apenas se estiver visualizando a própria carteira
            if is_self:
                dicas = [
                    "Use /daily para receber coins diariamente!",
                    "Premium oferece +50% de coins no daily!",
                    "Transfira coins com /transferir",
                    "Compre premium com suas coins usando /premium",
                    "Veja o ranking do servidor com /top",
                    "Experimente o novo minigame com /jogo",
                    "Ganhe fragmentos respondendo perguntas com /quiz",
                    "Veja seus fragmentos com /fragmentos",
                    "Crie itens com seus fragmentos usando /crafting"
                ]
                embed.set_footer(text=f"💡 {random.choice(dicas)}")
            else:
                # Adicionar nota quando visualizando carteira de outro usuário
                embed.set_footer(text=f"💡 Use /transferir para enviar coins para {target_name}")

            # Adicionar avatar do usuário caso disponível
            if target_user.avatar:
                embed.set_thumbnail(url=target_user.avatar.url)

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Adicionar XP pelo uso do comando (somente se for a própria carteira)
            if is_self:
                try:
                    await XPGainManager.add_command_xp(interaction.user.id, interaction.user.name, "carteira")
                except Exception as xp_error:
                    logger.error(f"Erro ao adicionar XP para carteira: {xp_error}")

        except Exception as e:
            logger.error(f"Erro ao processar carteira: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO PROCESSAR CARTEIRA",
                description="Ocorreu um erro ao acessar a carteira solicitada. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="Resgate seus coins diários")
    async def daily(self, interaction: discord.Interaction):
        # Usar ephemeral=True para mensagens privadas
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        username = interaction.user.name

        try:
            # Verificar se o usuário existe no banco
            user = UserService.ensure_user_exists(user_id, username)
            if not user:
                await interaction.followup.send("❌ Erro ao acessar sua conta. Tente novamente.", ephemeral=True)
                return

            # Verificar se pode resgatar
            try:
                can_claim, result = UserService.check_daily(user_id)

                # Tratar erros de conexão
                if isinstance(result, str) and "SSL connection" in result:
                    logger.warning(f"Problema de conexão SSL: {result}")
                    # Usar um embed para erro de conexão
                    embed = discord.Embed(
                        title="⚠️ PROBLEMAS DE CONEXÃO",
                        description="Estamos enfrentando dificuldades temporárias de conexão.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="📝 O que fazer?",
                        value="Por favor, tente novamente em alguns instantes",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                if not can_claim:
                    if isinstance(result, tuple) and len(result) >= 3:
                        is_premium = bool(result[0])
                        hours = int(result[1]) if result[1] is not None else 24
                        minutes = int(result[2]) if result[2] is not None else 0

                        embed = discord.Embed(
                            title="⏰ DAILY JÁ RESGATADO!",
                            description="Você já coletou suas coins diárias hoje.",
                            color=discord.Color.orange()
                        )

                        embed.add_field(
                            name="⌛ Tempo Restante",
                            value=f"**{hours}h {minutes}m**",
                            inline=False
                        )

                        if is_premium:
                            embed.add_field(
                                name="💎 Lembrete Premium",
                                value="Como usuário premium, você receberá +50% de bônus na próxima coleta!",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name="✨ Dica",
                                value="Usuários premium recebem +50% de coins diariamente!",
                                inline=False
                            )

                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ Erro ao verificar daily: {result}", ephemeral=True)
                    return

                # Processar daily claim
                success, result = UserService.claim_daily(user_id)

                if not success:
                    # Verificar se é um erro de conexão SSL para melhor resposta
                    if isinstance(result, str) and "SSL connection" in result:
                        embed = discord.Embed(
                            title="⚠️ PROBLEMAS DE CONEXÃO",
                            description="Estamos enfrentando dificuldades temporárias de conexão.",
                            color=discord.Color.orange()
                        )
                        embed.add_field(
                            name="📝 O que fazer?",
                            value="Por favor, tente novamente em alguns instantes",
                            inline=False
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ Erro ao processar daily: {result}", ephemeral=True)
                    return

                # Extrair valores com segurança
                if isinstance(result, tuple) and len(result) >= 2:
                    amount = result[0] if result[0] is not None else 1000
                    is_premium = bool(result[1]) if result[1] is not None else False
                else:
                    # Valores padrão
                    amount = 1000
                    is_premium = False

                # Calcular base e bônus
                try:
                    amount = int(amount)
                    if is_premium:
                        base_amount = amount * 2 // 3
                        bonus_amount = amount - base_amount
                    else:
                        base_amount = amount
                        bonus_amount = 0
                except (TypeError, ValueError):
                    # Valores seguros padrão
                    base_amount = 1000
                    bonus_amount = 500 if is_premium else 0
                    amount = base_amount + bonus_amount

                # Criar embed de sucesso
                embed = discord.Embed(
                    title="🎁 DAILY REWARD COLETADO!",
                    description=f"🎉 **PARABÉNS!** Você coletou suas coins diárias!",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="💰 Valor Base",
                    value=f"**{base_amount:,} coins**",
                    inline=True
                )

                if is_premium:
                    embed.add_field(
                        name="✨ Bônus Premium (50%)",
                        value=f"**+{bonus_amount:,} coins**",
                        inline=True
                    )

                embed.add_field(
                    name="🏆 Total Recebido",
                    value=f"**{amount:,} coins**",
                    inline=True
                )

                # Adicionar campos extras
                saldo_atual = user[2] + amount  # Estimativa do saldo atual
                embed.add_field(
                    name="📊 Saldo Atualizado (Estimado)",
                    value=f"**{saldo_atual:,} coins**",
                    inline=False
                )

                # Mensagem aleatória para variar a experiência
                mensagens = [
                    "Volte amanhã para mais coins!",
                    "Não esqueça de coletar suas coins diariamente!",
                    "A constância é a chave para acumular coins!",
                    "Continue coletando todos os dias para maximizar seus ganhos!",
                    "Seu comprometimento diário está rendendo frutos!"
                ]

                embed.set_footer(text=random.choice(mensagens))

                await interaction.followup.send(embed=embed, ephemeral=True)

                # Adicionar XP pelo uso do comando daily (valor maior por ser um comando importante)
                try:
                    await XPGainManager.add_command_xp(interaction.user.id, interaction.user.name, "daily")
                except Exception as xp_error:
                    logger.error(f"Erro ao adicionar XP para daily: {xp_error}")

            except Exception as e:
                logger.error(f"Erro no processamento do daily: {str(e)}")
                await interaction.followup.send("❌ Ocorreu um erro ao processar seu daily. Tente novamente mais tarde.", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro geral no comando daily: {str(e)}")
            await interaction.followup.send("❌ Ocorreu um erro ao processar seu daily. Tente novamente mais tarde.", ephemeral=True)

    @app_commands.command(name="transferir", description="Transfira coins para outro usuário")
    @app_commands.describe(
        usuario="O usuário que receberá os coins",
        quantidade="A quantidade de coins a transferir"
    )
    async def transferir(self, interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
        # Usar ephemeral=True para mensagens privadas
        await interaction.response.defer(ephemeral=True)

        try:
            # Validações básicas
            if quantidade <= 0:
                embed = discord.Embed(
                    title="❌ TRANSFERÊNCIA INVÁLIDA",
                    description="A quantidade de coins deve ser maior que zero!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if usuario.id == interaction.user.id:
                embed = discord.Embed(
                    title="❌ TRANSFERÊNCIA INVÁLIDA",
                    description="Você não pode transferir coins para si mesmo!",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Tente transferir para outro usuário.")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if usuario.bot:
                embed = discord.Embed(
                    title="❌ TRANSFERÊNCIA INVÁLIDA",
                    description="Você não pode transferir coins para um bot!",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Bots não precisam de coins... ainda.")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Verificar se o remetente existe no banco e obter dados
            sender = UserService.ensure_user_exists(interaction.user.id, interaction.user.name)
            if not sender:
                await interaction.followup.send("❌ Erro ao acessar sua conta. Tente novamente.", ephemeral=True)
                return

            # Verificar se tem saldo suficiente
            if sender[2] < quantidade:
                embed = discord.Embed(
                    title="💰 SALDO INSUFICIENTE",
                    description=f"Você não tem coins suficientes para esta transferência!",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="Seu Saldo",
                    value=f"**{sender[2]:,} coins**",
                    inline=True
                )
                embed.add_field(
                    name="Valor da Transferência",
                    value=f"**{quantidade:,} coins**",
                    inline=True
                )
                embed.add_field(
                    name="Faltam",
                    value=f"**{quantidade - sender[2]:,} coins**",
                    inline=True
                )
                embed.set_footer(text="Dica: Use o comando /daily para ganhar mais coins!")

                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Verificar se o destinatário existe no banco
            recipient = UserService.ensure_user_exists(usuario.id, usuario.name)
            if not recipient:
                await interaction.followup.send("❌ Erro ao acessar a conta do destinatário. Tente novamente.", ephemeral=True)
                return

            # Processar a transferência
            success, result = UserService.transfer_coins(
                interaction.user.id, 
                usuario.id, 
                quantidade, 
                f"Transferência para {usuario.name}"
            )

            if not success:
                embed = discord.Embed(
                    title="❌ ERRO NA TRANSFERÊNCIA",
                    description=f"Não foi possível completar a transferência: {result}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Obter dados atualizados
            updated_sender = UserService.get_user(interaction.user.id)

            # Criar embed de sucesso com formato de texto
            embed = discord.Embed(
                title="💸 TRANSFERÊNCIA REALIZADA COM SUCESSO!",
                description=f"Você transferiu coins para {usuario.mention}!",
                color=discord.Color.green()
            )

            # Efeito visual com emojis para representar a transferência
            embed.add_field(
                name="🧾 Comprovante da Transação",
                value=(
                    f"**De:** {interaction.user.mention}\n"
                    f"**Para:** {usuario.mention}\n"
                    f"**Valor:** {quantidade:,} coins\n"
                    f"**Data:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
                ),
                inline=False
            )

            # Adicionar saldo atualizado
            if updated_sender:
                embed.add_field(
                    name="💰 Seu Saldo Atual",
                    value=f"**{updated_sender[2]:,} coins**",
                    inline=True
                )

            # Mensagens aleatórias para o rodapé
            mensagens = [
                "Transferência concluída com sucesso!",
                "Coins transferidos instantaneamente!",
                "Transação processada com segurança!",
                "Transferência executada em tempo recorde!",
                "Seus coins foram entregues com sucesso!"
            ]

            # Adicionar um ID de transação fictício para efeito visual
            transaction_id = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            embed.set_footer(text=f"{random.choice(mensagens)} | ID: {transaction_id}")

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Notificar o destinatário com uma mensagem direta
            try:
                # Criar um embed de notificação para o destinatário com estilo texto
                notify_embed = discord.Embed(
                    title="💰 COINS RECEBIDOS! 💰",
                    description=f"**PARABÉNS!** Você recebeu uma transferência de {interaction.user.mention}!",
                    color=discord.Color.gold()
                )

                # Adicionar detalhes da transação
                notify_embed.add_field(
                    name="💸 Valor Recebido",
                    value=f"**{quantidade:,} coins**",
                    inline=True
                )

                notify_embed.add_field(
                    name="👤 Remetente",
                    value=f"**{interaction.user.name}**",
                    inline=True
                )

                # Obter dados atualizados do destinatário
                updated_recipient = UserService.get_user(usuario.id)
                if updated_recipient:
                    notify_embed.add_field(
                        name="💰 Seu Saldo Atual",
                        value=f"**{updated_recipient[2]:,} coins**",
                        inline=False
                    )

                # Adicionar um efeito visual com emoji "chovendo dinheiro"
                rain_money = "💰 " * 5
                notify_embed.add_field(
                    name=f"{rain_money}",
                    value="Use `/carteira` para ver seu saldo atualizado!",
                    inline=False
                )

                notify_embed.set_footer(text=f"Transferência recebida em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | ID: {transaction_id}")

                # Enviar mensagem direta para o usuário
                if interaction.guild:
                    await usuario.send(embed=notify_embed)
            except Exception as e:
                logger.error(f"Erro ao notificar destinatário: {e}")

        except Exception as e:
            logger.error(f"Erro geral no comando transferir: {str(e)}")
            await interaction.followup.send("❌ Ocorreu um erro ao processar a transferência. Tente novamente mais tarde.", ephemeral=True)

    @app_commands.command(name="top", description="Veja o ranking dos usuários mais ricos do servidor")
    @app_commands.describe(
        tipo="Tipo de ranking para visualizar",
        limite="Número de usuários para mostrar (padrão: 10)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Coins", value="coins"),
        app_commands.Choice(name="Daily Streak", value="streak")
    ])
    async def top(self, interaction: discord.Interaction, 
                 tipo: str = "coins",
                 limite: int = 10):
        """Exibe o ranking dos usuários mais ricos do servidor"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Limitar o número de usuários entre 5 e 25
            limite = max(5, min(limite, 25))

            # Criar título e descrição com base no tipo
            title = ""
            description = ""
            query = ""

            if tipo == "coins":
                title = "💰 RANKING DE COINS 💰"
                description = f"Os {limite} usuários mais ricos do servidor:"
                query = "SELECT user_id, username, coins FROM users ORDER BY coins DESC LIMIT ?"
            elif tipo == "streak":
                title = "🔥 RANKING DE DAILY STREAK 🔥"
                description = "Os usuários mais consistentes do servidor:"
                query = "SELECT user_id, username, coins FROM users ORDER BY coins DESC LIMIT ?"  # Usamos coins como fallback
            else:
                # Tipo desconhecido, usar o padrão
                title = "💰 RANKING DE COINS 💰"
                description = f"Os {limite} usuários mais ricos do servidor:"
                query = "SELECT user_id, username, coins FROM users ORDER BY coins DESC LIMIT ?"

            # Criar embed para o ranking
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.gold()
            )

            # Adicionar faixa decorativa no topo
            embed.description = f"```ansi\n\u001b[36;1m{'=' * 30}\u001b[0m\n```" + embed.description

            # Conectar ao banco e obter dados
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(query, (limite,))
            results = cursor.fetchall()

            # Fechar conexão
            cursor.close()
            conn.close()

            if not results:
                embed.add_field(
                    name="❌ RANKING VAZIO",
                    value="Ainda não há dados suficientes para gerar um ranking.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Adicionar informações do ranking
            formatted_ranking = ""
            medals = ["🥇", "🥈", "🥉"]

            for i, (user_id, username, value) in enumerate(results):
                # Determinar o prefixo (medalha ou número)
                if i < 3:
                    prefix = medals[i]
                else:
                    prefix = f"`{i+1}.`"

                # Tentar obter usuário do Discord para menção
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.mention} ({username})"
                except:
                    # Se falhar, usar apenas o nome
                    user_display = f"**{username}**"

                # Formatar a linha com base no tipo
                if tipo == "coins":
                    formatted_ranking += f"{prefix} {user_display}: **{value:,}** coins\n"
                elif tipo == "streak":
                    formatted_ranking += f"{prefix} {user_display}: **{value}** dias\n"
                else:
                    formatted_ranking += f"{prefix} {user_display}: **{value:,}** coins\n"

            embed.add_field(
                name=f"🏆 TOP {len(results)} USUÁRIOS",
                value=formatted_ranking,
                inline=False
            )

            # Adicionar sua posição no ranking
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()

                # Contar usuários com mais moedas que você
                if tipo == "coins":
                    cursor.execute("SELECT COUNT(*) FROM users WHERE coins > (SELECT coins FROM users WHERE user_id = ?)", 
                                  (str(interaction.user.id),))
                else:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE coins > (SELECT coins FROM users WHERE user_id = ?)", 
                                  (str(interaction.user.id),))

                your_position = cursor.fetchone()[0] + 1  # +1 porque a contagem começa em 0

                # Obter seu valor (moedas ou streak)
                if tipo == "coins":
                    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (str(interaction.user.id),))
                    your_value = cursor.fetchone()[0]
                    value_str = f"{your_value:,} coins"
                else:
                    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (str(interaction.user.id),))
                    your_value = cursor.fetchone()[0]
                    value_str = f"{your_value:,} coins"

                cursor.close()
                conn.close()

                # Adicionar campo com sua posição
                embed.add_field(
                    name="📊 SUA POSIÇÃO",
                    value=f"Você está em **#{your_position}** com **{value_str}**",
                    inline=False
                )
            except Exception as e:
                logger.error(f"Erro ao obter posição do usuário: {e}")

            # Adicionar rodapé com dica
            embed.set_footer(text=f"Use /daily diariamente para subir no ranking! • {datetime.datetime.now().strftime('%d/%m/%Y')}")

            # Enviar mensagem
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao processar ranking: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO GERAR RANKING",
                description="Ocorreu um erro ao processar o ranking. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="jogo", description="Aposte suas coins em um jogo de adivinhação")
    @app_commands.describe(
        aposta="Quantidade de coins para apostar",
        dificuldade="Nível de dificuldade (fácil, médio, difícil)"
    )
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="Fácil (1-5, ganhe 2x)", value="facil"),
        app_commands.Choice(name="Médio (1-10, ganhe 3x)", value="medio"),
        app_commands.Choice(name="Difícil (1-20, ganhe 5x)", value="dificil")
    ])
    async def jogo(self, interaction: discord.Interaction, aposta: int, dificuldade: str = "medio"):
        """Um minigame para apostar coins"""
        await interaction.response.defer(ephemeral=True)

        # Verificar aposta mínima
        if aposta < 10:
            await interaction.followup.send("❌ A aposta mínima é de 10 coins.", ephemeral=True)
            return

        user_id = interaction.user.id
        username = interaction.user.name

        try:
            # Verificar se o usuário existe e tem saldo suficiente
            user = UserService.ensure_user_exists(user_id, username)

            if not user or user[2] < aposta:
                embed = discord.Embed(
                    title="💰 SALDO INSUFICIENTE",
                    description=f"Você não tem coins suficientes para essa aposta.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Seu Saldo",
                    value=f"**{user[2]:,} coins**" if user else "**0 coins**",
                    inline=True
                )
                embed.add_field(
                    name="Aposta",
                    value=f"**{aposta:,} coins**",
                    inline=True
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Configurar parâmetros do jogo com base na dificuldade
            if dificuldade == "facil":
                range_max = 5
                multiplicador = 2
                emoji = "🟢"
                color = discord.Color.green()
            elif dificuldade == "dificil":
                range_max = 20
                multiplicador = 5
                emoji = "🔴"
                color = discord.Color.red()
            else:  # médio (padrão)
                range_max = 10
                multiplicador = 3
                emoji = "🟠"
                color = discord.Color.orange()

            # Gerar número aleatório e criar buttons para seleção
            correct_number = random.randint(1, range_max)

            # Criar botões para cada número
            view = discord.ui.View(timeout=60)

            # Criar embed inicial
            embed = discord.Embed(
                title=f"{emoji} JOGO DE ADIVINHAÇÃO {emoji}",
                description=(
                    f"Você apostou **{aposta:,} coins** na dificuldade **{dificuldade.upper()}**\n\n"
                    f"Escolha um número entre **1** e **{range_max}**.\n"
                    f"Se acertar, você ganha **{aposta * multiplicador:,} coins** e fragmentos!"
                ),
                color=color
            )

            # Adicionar campos de informação
            embed.add_field(
                name="🎯 Como Jogar",
                value="Clique em um dos botões abaixo para escolher um número.",
                inline=False
            )

            embed.add_field(
                name="⏱️ Tempo Restante",
                value="Você tem 60 segundos para fazer sua escolha.",
                inline=False
            )

            # Criar botões para cada número em linhas organizadas
            buttons_per_row = 5
            current_row = 0

            # Criar classe de botão customizada para evitar problemas com o lambda
            class NumberButton(discord.ui.Button):
                def __init__(self, number, row):
                    super().__init__(
                        style=discord.ButtonStyle.primary,
                        label=str(number),
                        row=row
                    )
                    self.number = number

                async def callback(self, button_interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("Este jogo não é seu!", ephemeral=True)
                        return

                    # Desabilitar todos os botões
                    for child in view.children:
                        child.disabled = True

                    # Verificar se acertou
                    if self.number == correct_number:
                        # Ganhou!
                        winnings = aposta * multiplicador
                        
                        # Variável para armazenar o embed
                        embed = None
                        
                        try:
                            # Adicionar coins
                            success, _ = UserService.add_coins(
                                str(user_id),
                                winnings - aposta,  # Desconta a aposta inicial
                                f"Vitória no jogo (dificuldade: {dificuldade})"
                            )
                            
                            # Adicionar fragmentos com base na dificuldade
                            fragment_rewards = []
                            if success:
                                for fragment_type, chance in FRAGMENT_CHANCES[dificuldade].items():
                                    if random.randint(1, 100) <= chance:
                                        # Definir quantidade com base no tipo
                                        if fragment_type == "comum":
                                            qty = random.randint(1, 3)
                                        elif fragment_type == "incomum":
                                            qty = random.randint(1, 2)
                                        else:
                                            qty = 1
                                            
                                        fragment_rewards.append((fragment_type, qty))
                                        # Adicionar ao inventário
                                        ShopService.add_fragments(str(user_id), fragment_type, qty)

                            if success:
                                embed = discord.Embed(
                                    title="🎉 VITÓRIA!",
                                    description=f"Você acertou o número {correct_number}!",
                                    color=discord.Color.green()
                                )
                                
                                # Adicionar recompensas ao embed
                                rewards_text = f"• **+{winnings - aposta:,}** coins\n"
                                
                                if fragment_rewards:
                                    rewards_text += "• Fragmentos:\n"
                                    for fragment_type, qty in fragment_rewards:
                                        # Emojis para cada tipo de fragmento
                                        fragment_emojis = {
                                            "comum": "⚪",
                                            "incomum": "🟢", 
                                            "raro": "🔵",
                                            "épico": "🟣",
                                            "lendário": "🟠"
                                        }
                                        emoji = fragment_emojis.get(fragment_type, "💎")
                                        rewards_text += f"  - {emoji} {qty}x fragmento **{fragment_type}**\n"
                                else:
                                    rewards_text += "• Nenhum fragmento desta vez!"
                                
                                embed.add_field(
                                    name="🏆 RECOMPENSAS",
                                    value=rewards_text,
                                    inline=False
                                )
                            else:
                                embed = discord.Embed(
                                    title="❌ ERRO",
                                    description="Ocorreu um erro ao processar sua vitória.",
                                    color=discord.Color.red()
                                )
                        except Exception as e:
                            logger.error(f"Erro ao processar vitória: {e}")
                            embed = discord.Embed(
                                title="❌ ERRO",
                                description="Ocorreu um erro ao processar sua vitória.",
                                color=discord.Color.red()
                            )
                    
                            # Responder com o resultado
                            await button_interaction.response.edit_message(embed=embed, view=view)
                        except Exception as e2:
                            logger.error(f"Erro ao responder após vitória: {e2}")
                            try:
                                await button_interaction.response.send_message("Ocorreu um erro ao processar o jogo.", ephemeral=True)
                            except:
                                logger.error("Não foi possível responder após falha no jogo.")
                    else:
                        # Perdeu!
                        embed = discord.Embed(
                            title="❌ DERROTA",
                            description=f"Você escolheu {self.number}, mas o número correto era {correct_number}!",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="💸 PERDAS",
                            value=f"• **-{aposta:,}** coins",
                            inline=False
                        )
                        await button_interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Erro no jogo: {e}")
            await interaction.followup.send(f"Ocorreu um erro ao processar o jogo: {e}", ephemeral=True)
    
    @app_commands.command(name="fragmentos", description="Veja os fragmentos que você possui para crafting")
    async def fragmentos(self, interaction: discord.Interaction):
        """Exibe os fragmentos que o usuário possui para usar no crafting"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        try:
            # Verificar se o usuário existe
            user = UserService.ensure_user_exists(user_id, username)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR FRAGMENTOS",
                    description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter fragmentos do usuário
            success, fragments = ShopService.get_user_fragments(user_id)
            
            if not success:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR FRAGMENTOS",
                    description="Ocorreu um erro ao acessar seus fragmentos. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Criar embed com os fragmentos
            embed = discord.Embed(
                title="💎 SEUS FRAGMENTOS 💎",
                description="Fragmentos podem ser usados para craftar itens poderosos!",
                color=discord.Color.blue()
            )
            
            # Adicionar campo para cada tipo de fragmento com emoji
            fragment_emojis = {
                "comum": "⚪",
                "incomum": "🟢",
                "raro": "🔵",
                "épico": "🟣",
                "lendário": "🟠"
            }
            
            fragments_text = ""
            for fragment_type, quantity in fragments.items():
                emoji = fragment_emojis.get(fragment_type, "💎")
                fragments_text += f"{emoji} **{fragment_type.upper()}**: {quantity} unidades\n"
            
            if fragments_text:
                embed.add_field(
                    name="🧰 INVENTÁRIO DE FRAGMENTOS",
                    value=fragments_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="🧰 INVENTÁRIO VAZIO",
                    value="Você ainda não possui fragmentos. Use `/quiz` ou `/jogo` para ganhar fragmentos!",
                    inline=False
                )
            
            # Adicionar instruções
            embed.add_field(
                name="🛠️ COMO USAR",
                value="Use o comando `/crafting` para criar itens utilizando seus fragmentos.",
                inline=False
            )
            
            # Adicionar dicas
            embed.set_footer(text="Dica: Fragmentos mais raros podem ser obtidos em jogos com dificuldade maior!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao processar fragmentos: {e}")
            embed = discord.Embed(
                title="❌ ERRO AO ACESSAR FRAGMENTOS",
                description="Ocorreu um erro ao acessar seus fragmentos. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="crafting", description="Crie itens utilizando fragmentos coletados")
    async def crafting(self, interaction: discord.Interaction):
        """Sistema de crafting para criar itens com fragmentos"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        try:
            # Verificar se o usuário existe
            user = UserService.ensure_user_exists(user_id, username)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR CRAFTING",
                    description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter receitas disponíveis
            success, recipes = ShopService.get_crafting_recipes()
            
            if not success or not recipes:
                embed = discord.Embed(
                    title="🛠️ CRAFTING INDISPONÍVEL",
                    description="Não há receitas disponíveis no momento. Volte mais tarde!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter fragmentos do usuário
            success_fragments, fragments = ShopService.get_user_fragments(user_id)
            
            if not success_fragments:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR FRAGMENTOS",
                    description="Ocorreu um erro ao acessar seus fragmentos. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Criar lista de seleção para as receitas
            options = []
            for recipe in recipes:
                # Criar descrição com requisitos
                description = f"Requer: "
                requirements = []
                
                # Acessar valores com segurança usando tratamento de exceção
                try:
                    common_fragments = int(recipe.get("common_fragments", 0))
                except (TypeError, AttributeError, ValueError):
                    common_fragments = 0 if "common_fragments" not in recipe else int(recipe["common_fragments"])
                
                try:
                    uncommon_fragments = int(recipe.get("uncommon_fragments", 0))
                except (TypeError, AttributeError, ValueError):
                    uncommon_fragments = 0 if "uncommon_fragments" not in recipe else int(recipe["uncommon_fragments"])
                
                try:
                    rare_fragments = int(recipe.get("rare_fragments", 0))
                except (TypeError, AttributeError, ValueError):
                    rare_fragments = 0 if "rare_fragments" not in recipe else int(recipe["rare_fragments"])
                
                try:
                    epic_fragments = int(recipe.get("epic_fragments", 0))
                except (TypeError, AttributeError, ValueError):
                    epic_fragments = 0 if "epic_fragments" not in recipe else int(recipe["epic_fragments"])
                
                try:
                    legendary_fragments = int(recipe.get("legendary_fragments", 0))
                except (TypeError, AttributeError, ValueError):
                    legendary_fragments = 0 if "legendary_fragments" not in recipe else int(recipe["legendary_fragments"])
                
                if common_fragments > 0:
                    requirements.append(f"{common_fragments} comum")
                if uncommon_fragments > 0:
                    requirements.append(f"{uncommon_fragments} incomum")
                if rare_fragments > 0:
                    requirements.append(f"{rare_fragments} raro")
                if epic_fragments > 0:
                    requirements.append(f"{epic_fragments} épico")
                if legendary_fragments > 0:
                    requirements.append(f"{legendary_fragments} lendário")
                # Obter valor de coins_cost com segurança
                try:
                    coins_cost = int(recipe.get("coins_cost", 0)) if hasattr(recipe, "get") else int(recipe["coins_cost"]) if "coins_cost" in recipe else 0
                except (TypeError, ValueError, AttributeError, KeyError):
                    coins_cost = 0
                    
                if coins_cost > 0:
                    requirements.append(f"{coins_cost} coins")
                
                description += ", ".join(requirements)
                
                # Verificar se tem fragmentos e coins suficientes
                can_craft = True
                # Usar os valores já calculados anteriormente
                comum_necessario = common_fragments
                incomum_necessario = uncommon_fragments
                raro_necessario = rare_fragments
                epico_necessario = epic_fragments
                lendario_necessario = legendary_fragments
                coins_necessario = coins_cost
                
                if fragments.get("comum", 0) < comum_necessario:
                    can_craft = False
                if fragments.get("incomum", 0) < incomum_necessario:
                    can_craft = False
                if fragments.get("raro", 0) < raro_necessario:
                    can_craft = False
                if fragments.get("épico", 0) < epico_necessario:
                    can_craft = False
                if fragments.get("lendário", 0) < lendario_necessario:
                    can_craft = False
                if user[2] < coins_necessario:
                    can_craft = False
                
                # Adicionar emoji baseado na raridade
                emoji = "🔷"
                # Obter item_rarity com segurança
                try:
                    item_rarity = recipe.get("item_rarity", "") if hasattr(recipe, "get") else recipe["item_rarity"] if "item_rarity" in recipe else ""
                except (AttributeError, KeyError, TypeError):
                    item_rarity = ""
                    
                if item_rarity:
                    if item_rarity == "comum":
                        emoji = "⚪"
                    elif item_rarity == "incomum":
                        emoji = "🟢"
                    elif item_rarity == "raro":
                        emoji = "🔵"
                    elif item_rarity == "épico":
                        emoji = "🟣"
                    elif item_rarity == "lendário":
                        emoji = "🟠"
                
                # Obter nome do item com segurança
                try:
                    item_name = recipe.get("name", "Item sem nome") if hasattr(recipe, "get") else recipe["name"] if "name" in recipe else "Item sem nome"
                except (AttributeError, KeyError, TypeError):
                    item_name = "Item sem nome"
                
                # Adicionar opção à lista
                option_name = f"{emoji} {item_name}"
                if not can_craft:
                    option_name = f"❌ {item_name} (Recursos insuficientes)"
                
                # Obter id da receita com segurança
                try:
                    recipe_id = str(recipe.get("id", 0)) if hasattr(recipe, "get") else str(recipe["id"]) if "id" in recipe else "0"
                except (AttributeError, KeyError, TypeError):
                    recipe_id = "0"
                
                options.append(
                    discord.SelectOption(
                        label=option_name[:100],  # Limite de 100 caracteres
                        description=description[:100],  # Limite de 100 caracteres
                        value=recipe_id,
                        emoji=None,  # Já incluído no label
                        default=False
                    )
                )
            
            # Criar embed inicial
            embed = discord.Embed(
                title="🛠️ SISTEMA DE CRAFTING 🛠️",
                description=(
                    "Crie itens poderosos com os fragmentos que você coletou!\n\n"
                    "Selecione uma receita abaixo para criar o item:"
                ),
                color=discord.Color.blue()
            )
            
            # Adicionar informações sobre fragmentos disponíveis
            fragments_text = ""
            fragment_emojis = {
                "comum": "⚪",
                "incomum": "🟢",
                "raro": "🔵",
                "épico": "🟣",
                "lendário": "🟠"
            }
            
            for fragment_type, quantity in fragments.items():
                emoji = fragment_emojis.get(fragment_type, "💎")
                fragments_text += f"{emoji} **{fragment_type.upper()}**: {quantity}\n"
            
            embed.add_field(
                name="💎 SEUS FRAGMENTOS",
                value=fragments_text or "Você não possui fragmentos.",
                inline=True
            )
            
            embed.add_field(
                name="💰 SEUS COINS",
                value=f"**{user[2]:,}** coins",
                inline=True
            )
            
            # Criar view com dropdown para seleção de receitas
            class CraftingView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=120)
                    
                    # Adicionar seleção de receitas
                    self.recipe_select = discord.ui.Select(
                        placeholder="Escolha um item para criar...",
                        options=options[:25],  # Limite de 25 opções
                        min_values=1,
                        max_values=1,
                        custom_id="recipe_select"
                    )
                    self.recipe_select.callback = self.recipe_selected
                    self.add_item(self.recipe_select)
                
                async def recipe_selected(self, select_interaction):
                    # Verificar se é o mesmo usuário
                    if select_interaction.user.id != interaction.user.id:
                        await select_interaction.response.send_message("Este crafting não é seu!", ephemeral=True)
                        return
                    
                    # Obter ID da receita selecionada
                    recipe_id = int(select_interaction.data["values"][0])
                    
                    # Tentar criar o item
                    success, result = ShopService.craft_item(user_id, recipe_id)
                    
                    if success:
                        # Item criado com sucesso
                        success_embed = discord.Embed(
                            title="✅ ITEM CRIADO COM SUCESSO!",
                            description=f"Você criou: **{result['item_name']}**",
                            color=discord.Color.green()
                        )
                        
                        success_embed.add_field(
                            name="📝 DESCRIÇÃO",
                            value=result["item_description"],
                            inline=False
                        )
                        
                        # Recursos gastos
                        resources_text = ""
                        for fragment_type, amount in result["fragments_used"].items():
                            if amount > 0:
                                emoji = fragment_emojis.get(fragment_type, "💎")
                                resources_text += f"{emoji} **{amount}x** fragmento {fragment_type}\n"
                        
                        if result["coins_cost"] > 0:
                            resources_text += f"💰 **{result['coins_cost']:,}** coins\n"
                        
                        if resources_text:
                            success_embed.add_field(
                                name="💱 RECURSOS GASTOS",
                                value=resources_text,
                                inline=False
                            )
                        
                        # Enviar mensagem de sucesso
                        await select_interaction.response.edit_message(embed=success_embed, view=None)
                    else:
                        # Falha ao criar item
                        error_embed = discord.Embed(
                            title="❌ FALHA AO CRIAR ITEM",
                            description=str(result),
                            color=discord.Color.red()
                        )
                        
                        error_embed.add_field(
                            name="🔄 TENTAR NOVAMENTE",
                            value="Use o comando `/crafting` para tentar novamente.",
                            inline=False
                        )
                        
                        await select_interaction.response.edit_message(embed=error_embed, view=None)
            
            # Enviar o menu de crafting
            view = CraftingView()
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao processar crafting: {e}")
            embed = discord.Embed(
                title="❌ ERRO NO SISTEMA DE CRAFTING",
                description="Ocorreu um erro ao acessar o sistema de crafting. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="quiz", description="Responda perguntas para ganhar coins e fragmentos")
    @app_commands.describe(dificuldade="Escolha o nível de dificuldade (fácil, médio ou difícil)")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="Fácil", value="facil"),
        app_commands.Choice(name="Médio", value="medio"),
        app_commands.Choice(name="Difícil", value="dificil")
    ])
    async def quiz(self, interaction: discord.Interaction, dificuldade: str = "medio"):
        """Um quiz para ganhar coins e fragmentos"""
        await interaction.response.defer(ephemeral=False)
        
        # Verificar dificuldade
        dificuldades_validas = ["facil", "medio", "dificil"]
        if dificuldade.lower() not in dificuldades_validas:
            dificuldade = "medio"
            
        # Definir configurações com base na dificuldade
        config = {
            "facil": {
                "multiplicador": 1.5,
                "tempo": 20,
                "quantidade_perguntas": 3,
                "recompensa_base": 50,
                "xp_base": 5,
                "fragment_chances": {
                    "comum": 70,
                    "incomum": 30,
                    "raro": 10,
                    "épico": 0,
                    "lendário": 0
                }
            },
            "medio": {
                "multiplicador": 2.0,
                "tempo": 15,
                "quantidade_perguntas": 5,
                "recompensa_base": 100,
                "xp_base": 10,
                "fragment_chances": {
                    "comum": 60,
                    "incomum": 40,
                    "raro": 20,
                    "épico": 5,
                    "lendário": 0
                }
            },
            "dificil": {
                "multiplicador": 3.0,
                "tempo": 10,
                "quantidade_perguntas": 7,
                "recompensa_base": 200,
                "xp_base": 20,
                "fragment_chances": {
                    "comum": 50,
                    "incomum": 40,
                    "raro": 30,
                    "épico": 15,
                    "lendário": 5
                }
            }
        }
        
        # Lista de perguntas
        perguntas = [
            {
                "pergunta": "Qual é a linguagem de programação mais utilizada para desenvolvimento web?",
                "opcoes": ["Python", "JavaScript", "Java", "C#"],
                "resposta": 1
            },
            {
                "pergunta": "Qual destes não é um framework JavaScript?",
                "opcoes": ["React", "Angular", "Django", "Vue"],
                "resposta": 2
            },
            {
                "pergunta": "O que significa API?",
                "opcoes": ["Application Programming Interface", "Automated Programming Interface", "Advanced Programming Interface", "Application Process Integration"],
                "resposta": 0
            },
            {
                "pergunta": "Qual dessas não é uma linguagem de marcação?",
                "opcoes": ["HTML", "XML", "YAML", "Python"],
                "resposta": 3
            },
            {
                "pergunta": "Qual é o principal uso do CSS?",
                "opcoes": ["Estilização", "Programação", "Armazenamento de dados", "Comunicação com servidores"],
                "resposta": 0
            },
            {
                "pergunta": "Em programação orientada a objetos, o que é encapsulamento?",
                "opcoes": ["Herança de classes", "Ocultação de dados", "Polimorfismo", "Abstração de interfaces"],
                "resposta": 1
            },
            {
                "pergunta": "O que é um banco de dados NoSQL?",
                "opcoes": ["Um banco que não usa SQL", "Um banco que usa apenas SQL", "Um banco relacional", "Um banco sem estrutura"],
                "resposta": 0
            },
            {
                "pergunta": "Qual protocolo é mais usado para páginas web?",
                "opcoes": ["HTTP", "FTP", "SMTP", "SSH"],
                "resposta": 0
            },
            {
                "pergunta": "O que significa HTML?",
                "opcoes": ["Hyper Text Markup Language", "High Tech Modern Language", "Hyper Transfer Markup Language", "Hyper Text Modern Links"],
                "resposta": 0
            },
            {
                "pergunta": "Qual é o operador de atribuição em JavaScript?",
                "opcoes": ["==", "===", "=", ":="],
                "resposta": 2
            }
        ]
        
        # Selecionar perguntas aleatoriamente
        selected_questions = random.sample(perguntas, min(config[dificuldade]["quantidade_perguntas"], len(perguntas)))
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        # Verificar se o usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        
        if not user:
            embed = discord.Embed(
                title="❌ ERRO AO INICIAR QUIZ",
                description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🧠 QUIZ DE PROGRAMAÇÃO 🧠",
            description=(
                f"**Dificuldade:** {dificuldade.upper()}\n"
                f"**Perguntas:** {len(selected_questions)}\n"
                f"**Tempo por pergunta:** {config[dificuldade]['tempo']} segundos\n\n"
                "Responda corretamente para ganhar coins e fragmentos!"
            ),
            color=discord.Color.blue()
        )
        
        # Enviar mensagem inicial
        await interaction.followup.send(embed=embed)
        
        # Variáveis para acompanhar o progresso
        correct_answers = 0
        total_questions = len(selected_questions)
        
        # Loop pelas perguntas
        for i, question in enumerate(selected_questions):
            # Criar embed para a pergunta
            question_embed = discord.Embed(
                title=f"Pergunta {i+1}/{total_questions}",
                description=question["pergunta"],
                color=discord.Color.blue()
            )
            
            # Adicionar opções
            for j, option in enumerate(question["opcoes"]):
                question_embed.add_field(
                    name=f"Opção {j+1}",
                    value=option,
                    inline=True
                )
            
            # Adicionar tempo restante
            question_embed.set_footer(text=f"Você tem {config[dificuldade]['tempo']} segundos para responder!")
            
            # Criar botões para as opções
            class AnswerView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=config[dificuldade]['tempo'])
                    self.answered = False
                    self.selected_option = None
            
            view = AnswerView()
            
            # Adicionar botões para cada opção
            for j, option in enumerate(question["opcoes"]):
                button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=f"Opção {j+1}",
                    custom_id=f"option_{j}"
                )
                
                async def answer_callback(button_interaction, button_j=j):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("Este quiz não é seu!", ephemeral=True)
                        return
                    
                    view.answered = True
                    view.selected_option = button_j
                    
                    # Desabilitar todos os botões
                    for child in view.children:
                        child.disabled = True
                    
                    # Atualizar o botão selecionado
                    if button_j == question["resposta"]:
                        button.style = discord.ButtonStyle.success
                    else:
                        button.style = discord.ButtonStyle.danger
                    
                    # Destacar o botão da resposta correta
                    for k, child in enumerate(view.children):
                        if k == question["resposta"]:
                            child.style = discord.ButtonStyle.success
                    
                    await button_interaction.response.edit_message(view=view)
                    view.stop()
                
                button.callback = answer_callback
                view.add_item(button)
            
            # Enviar a pergunta
            question_message = await interaction.followup.send(embed=question_embed, view=view)
            
            # Aguardar resposta ou timeout
            await view.wait()
            
            # Verificar se houve resposta
            if view.answered:
                if view.selected_option == question["resposta"]:
                    correct_answers += 1
            
            # Dar um pequeno intervalo entre as perguntas
            await asyncio.sleep(1.5)
        
        # Calcular recompensas
        coins_reward = int(config[dificuldade]["recompensa_base"] * (correct_answers / total_questions) * config[dificuldade]["multiplicador"])
        xp_reward = int(config[dificuldade]["xp_base"] * correct_answers)
        
        # Atribuir recompensas
        success, _ = UserService.add_coins(
            str(user_id),
            coins_reward,
            f"Recompensa de quiz (dificuldade: {dificuldade}, acertos: {correct_answers}/{total_questions})"
        )
        
        # Atribuir XP
        try:
            UserService.add_xp(user_id, xp_reward)
        except Exception as e:
            logger.error(f"Erro ao adicionar XP: {e}")
        
        # Adicionar fragmentos com base na dificuldade e desempenho
        fragment_rewards = []
        success_rate = correct_answers / total_questions
        
        # Ajustar chances com base no desempenho
        fragment_chances = config[dificuldade]["fragment_chances"].copy()
        
        if success_rate < 0.5:
            # Reduz todas as chances pela metade para desempenho ruim
            for k in fragment_chances:
                fragment_chances[k] = int(fragment_chances[k] * 0.5)
        elif success_rate == 1.0:
            # Aumenta chances para desempenho perfeito
            for k in fragment_chances:
                fragment_chances[k] = min(100, int(fragment_chances[k] * 1.5))
        
        # Atribuir fragmentos com base nas chances
        for fragment_type, chance in fragment_chances.items():
            if random.randint(1, 100) <= chance:
                # Definir quantidade com base no tipo e desempenho
                if fragment_type == "comum":
                    qty = random.randint(1, 3)
                elif fragment_type == "incomum":
                    qty = random.randint(1, 2)
                else:
                    qty = 1
                    
                fragment_rewards.append((fragment_type, qty))
                # Adicionar ao inventário
                try:
                    ShopService.add_fragments(str(user_id), fragment_type, qty)
                except Exception as e:
                    logger.error(f"Erro ao adicionar fragmentos: {e}")
        
        # Criar embed com resultado final
        result_embed = discord.Embed(
            title="🎯 RESULTADO DO QUIZ 🎯",
            description=(
                f"**Acertos:** {correct_answers}/{total_questions}\n"
                f"**Taxa de acerto:** {int(success_rate * 100)}%\n"
                f"**Dificuldade:** {dificuldade.upper()}"
            ),
            color=discord.Color.green() if success_rate >= 0.5 else discord.Color.orange()
        )
        
        # Adicionar recompensas
        rewards_text = f"• **+{coins_reward}** coins\n"
        rewards_text += f"• **+{xp_reward}** XP\n"
        
        if fragment_rewards:
            rewards_text += "• Fragmentos:\n"
            fragment_emojis = {
                "comum": "⚪",
                "incomum": "🟢", 
                "raro": "🔵",
                "épico": "🟣",
                "lendário": "🟠"
            }
            
            for fragment_type, qty in fragment_rewards:
                emoji = fragment_emojis.get(fragment_type, "💎")
                rewards_text += f"  - {emoji} {qty}x fragmento **{fragment_type}**\n"
        else:
            rewards_text += "• Nenhum fragmento desta vez!"
        
        result_embed.add_field(
            name="🏆 RECOMPENSAS",
            value=rewards_text,
            inline=False
        )
        
        # Enviar o resultado final
        await interaction.followup.send(embed=result_embed)


    @app_commands.command(name="forca", description="Jogue o clássico jogo da forca para ganhar coins e fragmentos")
    @app_commands.describe(dificuldade="Escolha o nível de dificuldade (fácil, médio ou difícil)")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="Fácil", value="facil"),
        app_commands.Choice(name="Médio", value="medio"),
        app_commands.Choice(name="Difícil", value="dificil")
    ])
    async def forca(self, interaction: discord.Interaction, dificuldade: str = "medio"):
        """Um jogo da forca para ganhar coins e fragmentos"""
        await interaction.response.defer(ephemeral=False)
        
        # Verificar dificuldade
        dificuldades_validas = ["facil", "medio", "dificil"]
        if dificuldade.lower() not in dificuldades_validas:
            dificuldade = "medio"
        
        # Configurações baseadas na dificuldade
        config = {
            "facil": {
                "vidas": 8,
                "recompensa_base": 150,
                "xp_base": 10,
                "categorias": ["animais", "frutas", "cores"],
                "fragment_chances": {
                    "comum": 80,
                    "incomum": 30,
                    "raro": 10,
                    "épico": 0,
                    "lendário": 0
                }
            },
            "medio": {
                "vidas": 6,
                "recompensa_base": 250,
                "xp_base": 20,
                "categorias": ["países", "esportes", "profissões", "animais"],
                "fragment_chances": {
                    "comum": 90,
                    "incomum": 40,
                    "raro": 20,
                    "épico": 5,
                    "lendário": 0
                }
            },
            "dificil": {
                "vidas": 5,
                "recompensa_base": 400,
                "xp_base": 30,
                "categorias": ["filmes", "objetos", "tecnologia", "mitologia"],
                "fragment_chances": {
                    "comum": 100,
                    "incomum": 60,
                    "raro": 30,
                    "épico": 10,
                    "lendário": 3
                }
            }
        }
        
        # Banco de palavras por categoria
        palavras = {
            "animais": ["gato", "cachorro", "elefante", "girafa", "leao", "tigre", "zebra", "macaco", "hipopotamo", "pinguim"],
            "frutas": ["banana", "maca", "laranja", "uva", "morango", "abacaxi", "melancia", "kiwi", "manga", "pera"],
            "cores": ["vermelho", "azul", "verde", "amarelo", "roxo", "laranja", "preto", "branco", "cinza", "rosa"],
            "países": ["brasil", "argentina", "portugal", "espanha", "italia", "franca", "alemanha", "inglaterra", "china", "japao"],
            "esportes": ["futebol", "basquete", "voleibol", "natacao", "atletismo", "ciclismo", "tenis", "boxe", "golfe", "xadrez"],
            "profissões": ["medico", "professor", "advogado", "engenheiro", "programador", "cozinheiro", "arquiteto", "motorista", "piloto", "jornalista"],
            "filmes": ["matrix", "titanic", "interestelar", "avatar", "gladiador", "vingadores", "inception", "refem", "batman", "frozen"],
            "objetos": ["computador", "teclado", "telefone", "carregador", "controle", "garrafa", "lampada", "guarda-chuva", "relogio", "calendario"],
            "tecnologia": ["algoritmo", "smartphone", "hardware", "software", "internet", "bluetooth", "computacao", "inteligencia", "realidade", "criptografia"],
            "mitologia": ["zeus", "poseidon", "atena", "hercules", "minotauro", "medusa", "pegaso", "aquiles", "fenix", "quimera"]
        }
        
        # Selecionar categoria e palavra aleatória
        categorias_disponiveis = config[dificuldade]["categorias"]
        categoria_escolhida = random.choice(categorias_disponiveis)
        palavra_escolhida = random.choice(palavras[categoria_escolhida])
        
        # Inicializar jogo
        palavra_oculta = ["_" for _ in palavra_escolhida]
        letras_usadas = []
        vidas_restantes = config[dificuldade]["vidas"]
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        # Verificar se usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        
        if not user:
            embed = discord.Embed(
                title="❌ ERRO AO INICIAR JOGO",
                description="Não foi possível acessar sua conta. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Criar emoji para representar vidas (♥)
        vidas_emoji = "♥" * vidas_restantes
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🎮 JOGO DA FORCA 🎮",
            description=(
                f"**Dificuldade:** {dificuldade.upper()}\n"
                f"**Categoria:** {categoria_escolhida.upper()}\n"
                f"**Vidas:** {vidas_emoji} ({vidas_restantes})\n\n"
                f"**Palavra:** {' '.join(palavra_oculta)}\n\n"
                "Digite uma letra no chat para tentar adivinhar!"
            ),
            color=discord.Color.blue()
        )
        
        # Enviar mensagem inicial
        mensagem = await interaction.followup.send(embed=embed)
        
        # Função para criar botão de letras
        def create_letter_buttons():
            # Criar view com botões
            view = discord.ui.View(timeout=180)  # 3 minutos de timeout
            
            # Adicionar botões para cada letra, organizados em 5 linhas (máximo 5 por linha)
            alphabet = "abcdefghijklmnopqrstuvwxyz"
            rows = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4]
            
            for i, letter in enumerate(alphabet):
                button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary if letter not in letras_usadas else (
                        discord.ButtonStyle.success if letter in palavra_escolhida else 
                        discord.ButtonStyle.danger
                    ),
                    label=letter.upper(),
                    custom_id=f"letter_{letter}",
                    row=rows[i],
                    disabled=letter in letras_usadas
                )
                
                async def letter_callback(interaction, button_letter=letter):
                    nonlocal palavra_oculta, letras_usadas, vidas_restantes
                    
                    # Verificar se é o mesmo usuário
                    if interaction.user.id != user_id:
                        await interaction.response.send_message("Este jogo não é seu!", ephemeral=True)
                        return
                    
                    # Se a letra já foi usada, ignorar
                    if button_letter in letras_usadas:
                        await interaction.response.defer()
                        return
                    
                    # Adicionar letra às usadas
                    letras_usadas.append(button_letter)
                    
                    # Verificar se a letra está na palavra
                    if button_letter in palavra_escolhida:
                        # Atualizar palavra oculta
                        for i, letra in enumerate(palavra_escolhida):
                            if letra == button_letter:
                                palavra_oculta[i] = letra
                    else:
                        # Reduzir vidas
                        vidas_restantes -= 1
                    
                    # Verificar fim de jogo
                    jogo_acabou = False
                    vitoria = False
                    
                    if "_" not in palavra_oculta:
                        jogo_acabou = True
                        vitoria = True
                    elif vidas_restantes <= 0:
                        jogo_acabou = True
                        vitoria = False
                    
                    # Atualizar vidas emoji
                    vidas_emoji = "♥" * vidas_restantes
                    
                    if jogo_acabou:
                        if vitoria:
                            # Calcular recompensas
                            recompensa_coins = int(config[dificuldade]["recompensa_base"] * (vidas_restantes / config[dificuldade]["vidas"] + 0.5))
                            recompensa_xp = config[dificuldade]["xp_base"]
                            
                            # Adicionar coins
                            success, _ = UserService.add_coins(
                                str(user_id),
                                recompensa_coins,
                                f"Vitória na Forca (dificuldade: {dificuldade})"
                            )
                            
                            # Adicionar XP
                            try:
                                UserService.add_xp(user_id, recompensa_xp)
                            except Exception as e:
                                logger.error(f"Erro ao adicionar XP: {e}")
                            
                            # Adicionar fragmentos com base na dificuldade
                            fragment_rewards = []
                            
                            # Ajustar chances com base no desempenho (vidas restantes)
                            fragment_chances = config[dificuldade]["fragment_chances"].copy()
                            
                            # Melhorar chances se tiver muitas vidas restantes
                            if vidas_restantes >= config[dificuldade]["vidas"] * 0.7:
                                for k in fragment_chances:
                                    fragment_chances[k] = min(100, int(fragment_chances[k] * 1.3))
                            
                            # Atribuir fragmentos
                            for fragment_type, chance in fragment_chances.items():
                                if random.randint(1, 100) <= chance:
                                    # Quantidade baseada no tipo
                                    if fragment_type == "comum":
                                        qty = random.randint(1, 3)
                                    elif fragment_type == "incomum":
                                        qty = random.randint(1, 2)
                                    else:
                                        qty = 1
                                        
                                    fragment_rewards.append((fragment_type, qty))
                                    
                                    # Adicionar fragmento ao inventário
                                    try:
                                        ShopService.add_fragments(str(user_id), fragment_type, qty)
                                    except Exception as e:
                                        logger.error(f"Erro ao adicionar fragmentos: {e}")
                            
                            # Criar embed de vitória
                            embed = discord.Embed(
                                title="🎉 PARABÉNS, VOCÊ VENCEU! 🎉",
                                description=(
                                    f"**Palavra:** {palavra_escolhida.upper()}\n"
                                    f"**Categoria:** {categoria_escolhida.upper()}\n"
                                    f"**Vidas restantes:** {vidas_emoji} ({vidas_restantes})\n\n"
                                ),
                                color=discord.Color.green()
                            )
                            
                            # Adicionar recompensas
                            rewards_text = f"• **+{recompensa_coins}** coins\n"
                            rewards_text += f"• **+{recompensa_xp}** XP\n"
                            
                            if fragment_rewards:
                                rewards_text += "• Fragmentos:\n"
                                fragment_emojis = {
                                    "comum": "⚪",
                                    "incomum": "🟢", 
                                    "raro": "🔵",
                                    "épico": "🟣",
                                    "lendário": "🟠"
                                }
                                
                                for fragment_type, qty in fragment_rewards:
                                    emoji = fragment_emojis.get(fragment_type, "💎")
                                    rewards_text += f"  - {emoji} {qty}x fragmento **{fragment_type}**\n"
                            else:
                                rewards_text += "• Nenhum fragmento desta vez!"
                            
                            embed.add_field(
                                name="🏆 RECOMPENSAS",
                                value=rewards_text,
                                inline=False
                            )
                        else:
                            # Criar embed de derrota
                            embed = discord.Embed(
                                title="☠️ VOCÊ PERDEU! ☠️",
                                description=(
                                    f"**Palavra correta:** {palavra_escolhida.upper()}\n"
                                    f"**Categoria:** {categoria_escolhida.upper()}\n"
                                    f"**Vidas restantes:** {vidas_emoji} ({vidas_restantes})\n\n"
                                ),
                                color=discord.Color.red()
                            )
                            
                            embed.add_field(
                                name="😔 TENTE NOVAMENTE",
                                value="Use o comando `/forca` para jogar novamente!",
                                inline=False
                            )
                        
                        # Atualizar mensagem final com botões desativados
                        new_view = create_letter_buttons()
                        for child in new_view.children:
                            child.disabled = True
                        
                        await interaction.response.edit_message(embed=embed, view=new_view)
                    else:
                        # Atualizar embed
                        embed = discord.Embed(
                            title="🎮 JOGO DA FORCA 🎮",
                            description=(
                                f"**Dificuldade:** {dificuldade.upper()}\n"
                                f"**Categoria:** {categoria_escolhida.upper()}\n"
                                f"**Vidas:** {vidas_emoji} ({vidas_restantes})\n\n"
                                f"**Palavra:** {' '.join(palavra_oculta)}\n\n"
                                f"**Letras usadas:** {', '.join(sorted([l.upper() for l in letras_usadas]))}"
                            ),
                            color=discord.Color.blue()
                        )
                        
                        # Atualizar mensagem
                        await interaction.response.edit_message(embed=embed, view=create_letter_buttons())
                
                button.callback = letter_callback
                view.add_item(button)
            
            # Adicionar botão de desistir
            desistir = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Desistir",
                custom_id="desistir",
                row=4
            )
            
            async def desistir_callback(interaction):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("Este jogo não é seu!", ephemeral=True)
                    return
                
                # Criar embed de desistência
                embed = discord.Embed(
                    title="❌ JOGO ENCERRADO",
                    description=(
                        f"**Palavra correta:** {palavra_escolhida.upper()}\n"
                        f"**Categoria:** {categoria_escolhida.upper()}\n\n"
                        "Você desistiu do jogo. Use o comando `/forca` para jogar novamente!"
                    ),
                    color=discord.Color.dark_red()
                )
                
                # Desabilitar todos os botões
                view = create_letter_buttons()
                for child in view.children:
                    child.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=view)
            
            desistir.callback = desistir_callback
            view.add_item(desistir)
            
            return view
        
        # Enviar mensagem com botões
        view = create_letter_buttons()
        await mensagem.edit(view=view)

    # Comando de sorteio removido para simplificar o sistema
    @app_commands.command(name="roleta", description="Aposte suas coins na roleta e ganhe grandes prêmios!")
    @app_commands.describe(aposta="Quantidade de coins para apostar (mínimo 10)")
    async def roleta(self, interaction: discord.Interaction, aposta: int):
        """Um jogo de roleta para ganhar coins"""
        await interaction.response.defer(ephemeral=False)
        
        # Verificar aposta
        if aposta < 10:
            embed = discord.Embed(
                title="❌ APOSTA INVÁLIDA",
                description="A aposta mínima é de 10 coins.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        # Verificar se o usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        
        if not user or user[2] < aposta:
            embed = discord.Embed(
                title="💰 SALDO INSUFICIENTE",
                description=f"Você não tem coins suficientes para essa aposta.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Seu Saldo",
                value=f"**{user[2] if user else 0:,} coins**",
                inline=True
            )
            embed.add_field(
                name="Aposta",
                value=f"**{aposta:,} coins**",
                inline=True
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Configuração das apostas
        opcoes_roleta = [
            {"nome": "Vermelho", "cor": discord.Color.red(), "multiplicador": 2, "chance": 45},
            {"nome": "Preto", "cor": discord.Color.dark_gray(), "multiplicador": 2, "chance": 45},
            {"nome": "Verde", "cor": discord.Color.green(), "multiplicador": 14, "chance": 10}
        ]
        
        # Criar view para seleção de cor
        class RoletaView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.resultado = None
            
            @discord.ui.button(label="🔴 Vermelho (2x)", style=discord.ButtonStyle.danger, custom_id="vermelho")
            async def vermelho(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.apostar(interaction, "Vermelho")
            
            @discord.ui.button(label="⚫ Preto (2x)", style=discord.ButtonStyle.secondary, custom_id="preto")
            async def preto(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.apostar(interaction, "Preto")
            
            @discord.ui.button(label="🟢 Verde (14x)", style=discord.ButtonStyle.success, custom_id="verde")
            async def verde(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.apostar(interaction, "Verde")
            
            async def apostar(self, interaction: discord.Interaction, cor_escolhida):
                # Verificar se é o usuário correto
                if interaction.user.id != user_id:
                    await interaction.response.send_message("Esta roleta não é sua!", ephemeral=True)
                    return
                
                # Desativar todos os botões
                for child in self.children:
                    child.disabled = True
                
                # Deduzir a aposta
                success, _ = UserService.remove_coins(
                    str(user_id),
                    aposta,
                    f"Aposta na roleta (cor: {cor_escolhida})"
                )
                
                if not success:
                    embed = discord.Embed(
                        title="❌ ERRO NA APOSTA",
                        description="Não foi possível processar sua aposta. Tente novamente mais tarde.",
                        color=discord.Color.red()
                    )
                    await interaction.response.edit_message(embed=embed, view=self)
                    return
                
                # Selecionar resultado com base nas chances
                numero_aleatorio = random.randint(1, 100)
                limite_acumulado = 0
                
                for opcao in opcoes_roleta:
                    limite_acumulado += opcao["chance"]
                    if numero_aleatorio <= limite_acumulado:
                        self.resultado = opcao
                        break
                
                # Verificar se o jogador ganhou
                ganhou = self.resultado["nome"] == cor_escolhida
                
                # Calcular recompensa
                recompensa = 0
                if ganhou:
                    recompensa = int(aposta * self.resultado["multiplicador"])
                    
                    # Adicionar recompensa
                    success, _ = UserService.add_coins(
                        str(user_id),
                        recompensa,
                        f"Vitória na roleta (cor: {cor_escolhida}, multiplicador: {self.resultado['multiplicador']}x)"
                    )
                
                # Adicionar fragmentos se ganhou em verde (muito raro)
                fragment_rewards = []
                if ganhou and cor_escolhida == "Verde":
                    # Conceder fragmentos raros
                    fragment_types = ["raro", "épico", "lendário"]
                    for fragment_type in fragment_types:
                        # Chance de obter fragmento com base na raridade
                        chance = 100 if fragment_type == "raro" else (40 if fragment_type == "épico" else 15)
                        
                        if random.randint(1, 100) <= chance:
                            qty = 1
                            fragment_rewards.append((fragment_type, qty))
                            
                            try:
                                ShopService.add_fragments(str(user_id), fragment_type, qty)
                            except Exception as e:
                                logger.error(f"Erro ao adicionar fragmentos: {e}")
                
                # Criar embed com resultado
                embed = discord.Embed(
                    title=f"🎰 RESULTADO DA ROLETA: {self.resultado['nome'].upper()} 🎰",
                    description=(
                        f"**Sua escolha:** {cor_escolhida}\n"
                        f"**Resultado:** {self.resultado['nome']}\n\n"
                        f"**{'Parabéns! Você ganhou!' if ganhou else 'Que pena! Você perdeu.'}**\n\n"
                        f"**Aposta:** {aposta:,} coins\n"
                        f"**{'Prêmio' if ganhou else 'Prêmio perdido'}:** {recompensa:,} coins\n\n"
                        f"**Resultado final:** {'+' if ganhou else ''}{(recompensa - aposta):,} coins"
                    ),
                    color=self.resultado["cor"]
                )
                
                # Adicionar informações sobre fragmentos se ganhou no verde
                if fragment_rewards:
                    rewards_text = "• Fragmentos bônus (Aposta Verde):\n"
                    fragment_emojis = {
                        "comum": "⚪",
                        "incomum": "🟢", 
                        "raro": "🔵",
                        "épico": "🟣",
                        "lendário": "🟠"
                    }
                    
                    for fragment_type, qty in fragment_rewards:
                        emoji = fragment_emojis.get(fragment_type, "💎")
                        rewards_text += f"  - {emoji} {qty}x fragmento **{fragment_type}**\n"
                    
                    embed.add_field(
                        name="🏆 RECOMPENSAS EXTRAS",
                        value=rewards_text,
                        inline=False
                    )
                
                await interaction.response.edit_message(embed=embed, view=self)
                
                # Adicionar XP pelo uso do comando
                try:
                    await XPGainManager.add_command_xp(user_id, username, "roleta")
                except Exception as e:
                    logger.error(f"Erro ao adicionar XP: {e}")
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🎰 ROLETA DE APOSTAS 🎰",
            description=(
                f"**Aposta:** {aposta:,} coins\n\n"
                "**Escolha uma cor para apostar:**\n"
                "🔴 **Vermelho** - Multiplicador: 2x (chance: 45%)\n"
                "⚫ **Preto** - Multiplicador: 2x (chance: 45%)\n"
                "🟢 **Verde** - Multiplicador: 14x (chance: 10%)\n\n"
                "**Bônus:** Ganhar na cor verde concede fragmentos raros!"
            ),
            color=discord.Color.blue()
        )
        
        # Enviar mensagem com botões
        view = RoletaView()
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="dados", description="Jogue dados para ganhar coins! Aposte na soma de dois dados.")
    @app_commands.describe(
        aposta="Quantidade de coins para apostar (mínimo 10)",
        previsao="Qual valor você prevê que será a soma dos dados (2-12)"
    )
    async def dados(self, interaction: discord.Interaction, aposta: int, previsao: int):
        """Um jogo de dados para ganhar coins"""
        await interaction.response.defer(ephemeral=False)
        
        # Verificar aposta
        if aposta < 10:
            embed = discord.Embed(
                title="❌ APOSTA INVÁLIDA",
                description="A aposta mínima é de 10 coins.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Verificar previsão
        if previsao < 2 or previsao > 12:
            embed = discord.Embed(
                title="❌ PREVISÃO INVÁLIDA",
                description="A previsão deve ser um número entre 2 e 12 (soma de dois dados).",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        user_id = interaction.user.id
        username = interaction.user.name
        
        # Verificar se o usuário existe
        user = UserService.ensure_user_exists(user_id, username)
        
        if not user or user[2] < aposta:
            embed = discord.Embed(
                title="💰 SALDO INSUFICIENTE",
                description=f"Você não tem coins suficientes para essa aposta.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Seu Saldo",
                value=f"**{user[2] if user else 0:,} coins**",
                inline=True
            )
            embed.add_field(
                name="Aposta",
                value=f"**{aposta:,} coins**",
                inline=True
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Deduzir a aposta
        success, _ = UserService.remove_coins(
            str(user_id),
            aposta,
            f"Aposta nos dados (previsão: {previsao})"
        )
        
        if not success:
            embed = discord.Embed(
                title="❌ ERRO NA APOSTA",
                description="Não foi possível processar sua aposta. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🎲 JOGO DE DADOS 🎲",
            description=(
                f"**Aposta:** {aposta:,} coins\n"
                f"**Sua previsão:** {previsao}\n\n"
                "Lançando os dados..."
            ),
            color=discord.Color.blue()
        )
        
        # Enviar mensagem inicial
        mensagem = await interaction.followup.send(embed=embed)
        
        # Aguardar um pouco para criar suspense
        await asyncio.sleep(2)
        
        # Lançar dados
        dado1 = random.randint(1, 6)
        dado2 = random.randint(1, 6)
        soma = dado1 + dado2
        
        # Verificar resultado
        acertou = soma == previsao
        
        # Calcular multiplicador com base na dificuldade
        # Quanto mais improvável o resultado, maior o multiplicador
        multiplicadores = {
            2: 35,   # 1/36 chance (1,1)
            3: 18,   # 2/36 chance (1,2 ou 2,1)
            4: 12,   # 3/36 chance
            5: 8,    # 4/36 chance
            6: 7,    # 5/36 chance
            7: 6,    # 6/36 chance - mais comum
            8: 7,    # 5/36 chance
            9: 8,    # 4/36 chance
            10: 12,  # 3/36 chance
            11: 18,  # 2/36 chance (5,6 ou 6,5)
            12: 35   # 1/36 chance (6,6)
        }
        
        multiplicador = multiplicadores.get(previsao, 10)
        
        # Calcular recompensa
        recompensa = 0
        if acertou:
            recompensa = int(aposta * multiplicador)
            
            # Adicionar recompensa
            success, _ = UserService.add_coins(
                str(user_id),
                recompensa,
                f"Vitória nos dados (previsão: {previsao}, resultado: {soma}, multiplicador: {multiplicador}x)"
            )
            
            # Adicionar fragmentos para resultados difíceis
            fragment_rewards = []
            if previsao in [2, 12]:  # Resultados mais difíceis
                fragment_types = ["raro", "épico"]
                for fragment_type in fragment_types:
                    # Chance de obter fragmento
                    chance = 80 if fragment_type == "raro" else 30
                    
                    if random.randint(1, 100) <= chance:
                        qty = 1
                        fragment_rewards.append((fragment_type, qty))
                        
                        try:
                            ShopService.add_fragments(str(user_id), fragment_type, qty)
                        except Exception as e:
                            logger.error(f"Erro ao adicionar fragmentos: {e}")
            elif previsao in [3, 11]:  # Resultados difíceis
                if random.randint(1, 100) <= 60:
                    qty = random.randint(1, 2)
                    fragment_rewards.append(("raro", qty))
                    
                    try:
                        ShopService.add_fragments(str(user_id), "raro", qty)
                    except Exception as e:
                        logger.error(f"Erro ao adicionar fragmentos: {e}")
        
        # Emoji para os dados
        emoji_dados = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣"
        }
        
        # Atualizar embed com resultado
        embed = discord.Embed(
            title=f"🎲 RESULTADO DOS DADOS: {soma} ({emoji_dados.get(dado1, '')} + {emoji_dados.get(dado2, '')}) 🎲",
            description=(
                f"**Sua previsão:** {previsao}\n"
                f"**Resultado:** {soma} ({dado1} + {dado2})\n\n"
                f"**{'Parabéns! Você acertou!' if acertou else 'Que pena! Você errou.'}**\n\n"
                f"**Aposta:** {aposta:,} coins\n"
                f"**Multiplicador:** {multiplicador}x\n"
                f"**{'Prêmio' if acertou else 'Prêmio perdido'}:** {recompensa:,} coins\n\n"
                f"**Resultado final:** {'+' if acertou else ''}{(recompensa - aposta):,} coins"
            ),
            color=discord.Color.green() if acertou else discord.Color.red()
        )
        
        # Adicionar informações sobre fragmentos
        if acertou and fragment_rewards:
            rewards_text = "• Fragmentos bônus (Previsão difícil):\n"
            fragment_emojis = {
                "comum": "⚪",
                "incomum": "🟢", 
                "raro": "🔵",
                "épico": "🟣",
                "lendário": "🟠"
            }
            
            for fragment_type, qty in fragment_rewards:
                emoji = fragment_emojis.get(fragment_type, "💎")
                rewards_text += f"  - {emoji} {qty}x fragmento **{fragment_type}**\n"
            
            embed.add_field(
                name="🏆 RECOMPENSAS EXTRAS",
                value=rewards_text,
                inline=False
            )
        
        # Atualizar mensagem com resultado
        await mensagem.edit(embed=embed)
        
        # Adicionar XP pelo uso do comando
        try:
            await XPGainManager.add_command_xp(user_id, username, "dados")
        except Exception as e:
            logger.error(f"Erro ao adicionar XP: {e}")

    # Comando de caça-níquel removido para simplificar o sistema
    @app_commands.command(name="banco", description="Sistema bancário para guardar seus coins com segurança e receber juros")
    async def banco(self, interaction: discord.Interaction):
        """Sistema bancário para guardar seus coins com segurança e receber juros"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        try:
            # Obter dados do usuário
            user = UserService.ensure_user_exists(user_id, username)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO ACESSAR BANCO",
                    description="Ocorreu um erro ao acessar sua conta bancária. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            user_coins = user[2]
            
            # Obter saldo bancário do usuário
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Verificar se as tabelas do sistema bancário existem, se não, criar
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    user_id TEXT PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_interest_time TEXT,
                    total_deposited INTEGER DEFAULT 0,
                    total_withdrawn INTEGER DEFAULT 0,
                    interest_earned INTEGER DEFAULT 0
                )
            ''')
            
            # Tabela para investimentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    amount INTEGER NOT NULL,
                    investment_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    expected_return INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES bank_accounts (user_id)
                )
            ''')
            
            # Tabela para empréstimos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    amount INTEGER NOT NULL,
                    interest_rate REAL NOT NULL,
                    start_time TEXT NOT NULL,
                    due_time TEXT NOT NULL,
                    paid_amount INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES bank_accounts (user_id)
                )
            ''')
            
            conn.commit()
            
            # Obter saldo bancário
            cursor.execute('SELECT balance, last_interest_time FROM bank_accounts WHERE user_id = ?', (user_id,))
            banco_data = cursor.fetchone()
            
            if not banco_data:
                # Criar conta bancária para o usuário
                cursor.execute(
                    'INSERT INTO bank_accounts (user_id, balance, last_interest_time) VALUES (?, ?, ?)',
                    (user_id, 0, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                conn.commit()
                banco_saldo = 0
                last_interest_date = datetime.datetime.now()
            else:
                banco_saldo = banco_data[0]
                last_interest_date = datetime.datetime.strptime(banco_data[1], '%Y-%m-%d %H:%M:%S')
            
            # Verificar se é hora de pagar juros (a cada 24 horas, 1% de juros)
            now = datetime.datetime.now()
            time_diff = now - last_interest_date
            
            if time_diff.total_seconds() >= 86400:  # 24 horas em segundos
                # Calcular quantos períodos de 24h se passaram
                days_passed = time_diff.total_seconds() // 86400
                
                # Calcular juros (1% ao dia)
                interest_amount = int(banco_saldo * 0.01 * days_passed)
                
                if interest_amount > 0:
                    # Adicionar juros ao saldo bancário
                    banco_saldo += interest_amount
                    
                    # Atualizar registro no banco de dados
                    cursor.execute(
                        'UPDATE bank_accounts SET balance = ?, last_interest_time = ? WHERE user_id = ?',
                        (banco_saldo, now.strftime('%Y-%m-%d %H:%M:%S'), user_id)
                    )
                    conn.commit()
                    
                    interest_msg = f"💰 Seus juros de **{interest_amount}** coins foram pagos!"
                else:
                    # Apenas atualizar a data do último pagamento de juros
                    cursor.execute(
                        'UPDATE bank_accounts SET last_interest_time = ? WHERE user_id = ?',
                        (now.strftime('%Y-%m-%d %H:%M:%S'), user_id)
                    )
                    conn.commit()
                    interest_msg = ""
            else:
                # Calcular tempo restante para próximo pagamento de juros
                seconds_left = 86400 - time_diff.total_seconds()
                hours_left = int(seconds_left // 3600)
                minutes_left = int((seconds_left % 3600) // 60)
                
                interest_msg = f"⏱️ Próximo pagamento de juros em: **{hours_left}h {minutes_left}m**"
            
            # Obter estatísticas mais detalhadas
            cursor.execute('SELECT total_deposited, total_withdrawn, interest_earned FROM bank_accounts WHERE user_id = ?', (user_id,))
            stats_data = cursor.fetchone()
            
            total_deposited = 0
            total_withdrawn = 0
            interest_earned = 0
            
            if stats_data:
                total_deposited = stats_data[0] or 0
                total_withdrawn = stats_data[1] or 0
                interest_earned = stats_data[2] or 0
            
            # Verificar investimentos ativos
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM bank_investments WHERE user_id = ? AND status = "active"', (user_id,))
            investment_data = cursor.fetchone()
            active_investments_count = investment_data[0] or 0
            active_investments_amount = investment_data[1] or 0
            
            # Verificar empréstimos ativos
            cursor.execute('SELECT COUNT(*), SUM(amount - paid_amount) FROM bank_loans WHERE user_id = ? AND status = "active"', (user_id,))
            loan_data = cursor.fetchone()
            active_loans_count = loan_data[0] or 0
            active_loans_amount = loan_data[1] or 0
            
            # Criar embed com informações bancárias
            embed = discord.Embed(
                title="🏦 BANCO CENTRAL",
                description=f"{interest_msg}\n\n"
                            f"**Saldo na carteira:** {user_coins:,} coins\n"
                            f"**Saldo no banco:** {banco_saldo:,} coins\n\n"
                            f"**Taxa de juros:** 1% ao dia\n"
                            f"**Juros diários:** {int(banco_saldo * 0.01):,} coins",
                color=discord.Color.blue()
            )
            
            # Adicionar informações sobre investimentos e empréstimos
            if active_investments_count > 0 or active_loans_count > 0:
                status_info = ""
                if active_investments_count > 0:
                    status_info += f"**Investimentos ativos:** {active_investments_count} (Total: {active_investments_amount:,} coins)\n"
                if active_loans_count > 0:
                    status_info += f"**Empréstimos ativos:** {active_loans_count} (Saldo devedor: {active_loans_amount:,} coins)\n"
                
                embed.add_field(
                    name="📊 STATUS ATUAL",
                    value=status_info,
                    inline=False
                )
            
            # Adicionar estatísticas
            embed.add_field(
                name="📈 ESTATÍSTICAS",
                value=f"**Total depositado:** {total_deposited:,} coins\n"
                      f"**Total sacado:** {total_withdrawn:,} coins\n"
                      f"**Juros acumulados:** {interest_earned:,} coins",
                inline=False
            )
            
            # Criar view com opções bancárias
            class BankView(discord.ui.View):
                def __init__(self, user_coins, bank_balance):
                    super().__init__(timeout=60)
                    self.user_coins = user_coins
                    self.bank_balance = bank_balance
                
                @discord.ui.button(label="Depositar", style=discord.ButtonStyle.primary, emoji="💵")
                async def depositar(self, button_interaction, button):
                    # Modal para depósito
                    deposit_modal = discord.ui.Modal(title="Depósito Bancário")
                    
                    amount_input = discord.ui.TextInput(
                        label=f"Quanto depositar? (Máx: {self.user_coins:,})",
                        placeholder="Ex: 1000",
                        min_length=1,
                        max_length=10
                    )
                    
                    deposit_modal.add_item(amount_input)
                    
                    async def deposit_callback(modal_interaction):
                        try:
                            amount = int(modal_interaction.data["components"][0]["components"][0]["value"])
                            
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                return
                                
                            if amount > self.user_coins:
                                await modal_interaction.response.send_message("❌ Saldo insuficiente na carteira!", ephemeral=True)
                                return
                            
                            # Remover coins da carteira
                            result = UserService.remove_coins(
                                user_id,
                                amount,
                                "Depósito bancário"
                            )
                            
                            if not result[0]:
                                await modal_interaction.response.send_message("❌ Erro ao realizar depósito!", ephemeral=True)
                                return
                            
                            # Adicionar ao saldo bancário
                            conn = sqlite3.connect('database.db')
                            cursor = conn.cursor()
                            
                            cursor.execute(
                                'UPDATE bank_accounts SET balance = balance + ? WHERE user_id = ?',
                                (amount, user_id)
                            )
                            conn.commit()
                            conn.close()
                            
                            # Atualizar valores para a próxima interação
                            self.user_coins -= amount
                            self.bank_balance += amount
                            
                            # Criar embed de sucesso
                            success_embed = discord.Embed(
                                title="✅ DEPÓSITO REALIZADO",
                                description=f"Você depositou **{amount:,}** coins no banco com sucesso!",
                                color=discord.Color.green()
                            )
                            
                            success_embed.add_field(
                                name="💰 Novo saldo bancário", 
                                value=f"**{self.bank_balance:,}** coins",
                                inline=True
                            )
                            
                            success_embed.add_field(
                                name="👛 Saldo na carteira", 
                                value=f"**{self.user_coins:,}** coins",
                                inline=True
                            )
                            
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                    
                    deposit_modal.on_submit = deposit_callback
                    await button_interaction.response.send_modal(deposit_modal)
                
                @discord.ui.button(label="Sacar", style=discord.ButtonStyle.primary, emoji="💸")
                async def sacar(self, button_interaction, button):
                    # Modal para saque
                    withdraw_modal = discord.ui.Modal(title="Saque Bancário")
                    
                    amount_input = discord.ui.TextInput(
                        label=f"Quanto sacar? (Máx: {self.bank_balance:,})",
                        placeholder="Ex: 1000",
                        min_length=1,
                        max_length=10
                    )
                    
                    withdraw_modal.add_item(amount_input)
                    
                    async def withdraw_callback(modal_interaction):
                        try:
                            amount = int(modal_interaction.data["components"][0]["components"][0]["value"])
                            
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                return
                                
                            if amount > self.bank_balance:
                                await modal_interaction.response.send_message("❌ Saldo bancário insuficiente!", ephemeral=True)
                                return
                            
                            # Remover do saldo bancário
                            conn = sqlite3.connect('database.db')
                            cursor = conn.cursor()
                            
                            cursor.execute(
                                'UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?',
                                (amount, user_id)
                            )
                            conn.commit()
                            conn.close()
                            
                            # Adicionar coins à carteira
                            result = UserService.add_coins(
                                user_id,
                                amount,
                                "Saque bancário"
                            )
                            
                            if not result[0]:
                                # Reverter a operação bancária em caso de erro
                                conn = sqlite3.connect('database.db')
                                cursor = conn.cursor()
                                cursor.execute(
                                    'UPDATE bank_accounts SET balance = balance + ? WHERE user_id = ?',
                                    (amount, user_id)
                                )
                                conn.commit()
                                conn.close()
                                
                                await modal_interaction.response.send_message("❌ Erro ao realizar saque!", ephemeral=True)
                                return
                            
                            # Atualizar valores para a próxima interação
                            self.user_coins += amount
                            self.bank_balance -= amount
                            
                            # Criar embed de sucesso
                            success_embed = discord.Embed(
                                title="✅ SAQUE REALIZADO",
                                description=f"Você sacou **{amount:,}** coins do banco com sucesso!",
                                color=discord.Color.green()
                            )
                            
                            success_embed.add_field(
                                name="💰 Novo saldo bancário", 
                                value=f"**{self.bank_balance:,}** coins",
                                inline=True
                            )
                            
                            success_embed.add_field(
                                name="👛 Saldo na carteira", 
                                value=f"**{self.user_coins:,}** coins",
                                inline=True
                            )
                            
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                    
                    withdraw_modal.on_submit = withdraw_callback
                    await button_interaction.response.send_modal(withdraw_modal)
                
                @discord.ui.button(label="Investir", style=discord.ButtonStyle.success, emoji="📈", row=1)
                async def investir(self, button_interaction, button):
                    if self.bank_balance < 1000:
                        await button_interaction.response.send_message("❌ Você precisa ter pelo menos 1.000 coins no banco para investir.", ephemeral=True)
                        return
                    
                    # Criar embed com opções de investimento
                    invest_embed = discord.Embed(
                        title="📈 INVESTIMENTOS",
                        description=(
                            "Escolha um plano de investimento:\n\n"
                            "**Conservador**: Baixo risco, retorno de 3-5% em 3 dias\n"
                            "**Moderado**: Risco médio, retorno de 10-15% em 5 dias\n"
                            "**Agressivo**: Alto risco, retorno de 30-50% ou perda parcial em 7 dias\n\n"
                            f"**Saldo bancário disponível**: {self.bank_balance:,} coins"
                        ),
                        color=discord.Color.gold()
                    )
                    
                    # Criar view com opções de investimento
                    class InvestmentView(discord.ui.View):
                        def __init__(self, bank_balance):
                            super().__init__(timeout=60)
                            self.bank_balance = bank_balance
                        
                        @discord.ui.button(label="Conservador (3-5%)", style=discord.ButtonStyle.primary, row=0)
                        async def invest_safe(self, interaction, button):
                            # Modal para valor do investimento conservador
                            await self._show_investment_modal(interaction, "conservador", 3, 5, 3)
                        
                        @discord.ui.button(label="Moderado (10-15%)", style=discord.ButtonStyle.primary, row=0)
                        async def invest_moderate(self, interaction, button):
                            # Modal para valor do investimento moderado
                            await self._show_investment_modal(interaction, "moderado", 10, 15, 5)
                        
                        @discord.ui.button(label="Agressivo (30-50%)", style=discord.ButtonStyle.primary, row=0)
                        async def invest_aggressive(self, interaction, button):
                            # Modal para valor do investimento agressivo
                            await self._show_investment_modal(interaction, "agressivo", 30, 50, 7)
                        
                        async def _show_investment_modal(self, interaction, investment_type, min_return, max_return, days):
                            # Modal para valor do investimento
                            investment_modal = discord.ui.Modal(title=f"Investimento {investment_type.title()}")
                            
                            amount_input = discord.ui.TextInput(
                                label=f"Valor a investir (Máx: {self.bank_balance:,})",
                                placeholder="Ex: 5000",
                                min_length=1,
                                max_length=10
                            )
                            
                            investment_modal.add_item(amount_input)
                            
                            async def investment_callback(modal_interaction):
                                try:
                                    amount = int(modal_interaction.data["components"][0]["components"][0]["value"])
                                    
                                    if amount <= 0:
                                        await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                        return
                                    
                                    if amount > self.bank_balance:
                                        await modal_interaction.response.send_message("❌ Saldo bancário insuficiente!", ephemeral=True)
                                        return
                                    
                                    if amount < 1000:
                                        await modal_interaction.response.send_message("❌ O valor mínimo para investimento é de 1.000 coins!", ephemeral=True)
                                        return
                                    
                                    # Remover do saldo bancário
                                    conn = sqlite3.connect('database.db')
                                    cursor = conn.cursor()
                                    
                                    cursor.execute(
                                        'UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?',
                                        (amount, user_id)
                                    )
                                    
                                    # Calcular data de vencimento
                                    start_time = datetime.datetime.now()
                                    end_time = start_time + datetime.timedelta(days=days)
                                    
                                    # Calcular retorno esperado (valor fixo para cada tipo)
                                    expected_return_rate = random.uniform(min_return, max_return) / 100
                                    expected_return = int(amount * (1 + expected_return_rate))
                                    
                                    # Registrar investimento
                                    cursor.execute('''
                                        INSERT INTO bank_investments 
                                        (user_id, amount, investment_type, start_time, end_time, expected_return, status) 
                                        VALUES (?, ?, ?, ?, ?, ?, 'active')
                                    ''', (
                                        user_id, 
                                        amount, 
                                        investment_type, 
                                        start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                        end_time.strftime('%Y-%m-%d %H:%M:%S'),
                                        expected_return
                                    ))
                                    
                                    conn.commit()
                                    conn.close()
                                    
                                    # Criar embed de confirmação
                                    success_embed = discord.Embed(
                                        title="✅ INVESTIMENTO REALIZADO",
                                        description=(
                                            f"Você investiu **{amount:,}** coins no plano **{investment_type.title()}**!\n\n"
                                            f"**Retorno esperado:** {expected_return:,} coins ({expected_return_rate*100:.1f}%)\n"
                                            f"**Data de vencimento:** {end_time.strftime('%d/%m/%Y às %H:%M')}\n\n"
                                            "Seu investimento será processado automaticamente na data de vencimento."
                                        ),
                                        color=discord.Color.green()
                                    )
                                    
                                    await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                    
                                except ValueError:
                                    await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                            
                            investment_modal.on_submit = investment_callback
                            await interaction.response.send_modal(investment_modal)
                    
                    # Enviar embed com opções de investimento
                    await button_interaction.response.send_message(embed=invest_embed, view=InvestmentView(self.bank_balance), ephemeral=True)
                
                @discord.ui.button(label="Empréstimo", style=discord.ButtonStyle.danger, emoji="💰", row=1)
                async def emprestimo(self, button_interaction, button):
                    # Verificar se já tem empréstimos ativos
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT COUNT(*) FROM bank_loans WHERE user_id = ? AND status = "active"', (user_id,))
                    active_loans = cursor.fetchone()[0] or 0
                    conn.close()
                    
                    if active_loans >= 1:
                        await button_interaction.response.send_message("❌ Você já possui um empréstimo ativo. Pague-o antes de solicitar outro.", ephemeral=True)
                        return
                    
                    # Criar embed com opções de empréstimo
                    loan_embed = discord.Embed(
                        title="💰 EMPRÉSTIMOS",
                        description=(
                            "Escolha um plano de empréstimo:\n\n"
                            "**Pequeno**: Até 5.000 coins, taxa de 5%, prazo de 3 dias\n"
                            "**Médio**: Até 20.000 coins, taxa de 10%, prazo de 5 dias\n"
                            "**Grande**: Até 50.000 coins, taxa de 15%, prazo de 7 dias\n\n"
                            f"**Saldo atual na carteira**: {self.user_coins:,} coins"
                        ),
                        color=discord.Color.red()
                    )
                    
                    # Criar view com opções de empréstimo
                    class LoanView(discord.ui.View):
                        def __init__(self):
                            super().__init__(timeout=60)
                        
                        @discord.ui.button(label="Pequeno (5%)", style=discord.ButtonStyle.primary, row=0)
                        async def loan_small(self, interaction, button):
                            # Modal para valor do empréstimo pequeno
                            await self._show_loan_modal(interaction, "pequeno", 5, 5000, 3)
                        
                        @discord.ui.button(label="Médio (10%)", style=discord.ButtonStyle.primary, row=0)
                        async def loan_medium(self, interaction, button):
                            # Modal para valor do empréstimo médio
                            await self._show_loan_modal(interaction, "medio", 10, 20000, 5)
                        
                        @discord.ui.button(label="Grande (15%)", style=discord.ButtonStyle.primary, row=0)
                        async def loan_large(self, interaction, button):
                            # Modal para valor do empréstimo grande
                            await self._show_loan_modal(interaction, "grande", 15, 50000, 7)
                        
                        async def _show_loan_modal(self, interaction, loan_type, interest_rate, max_amount, days):
                            # Modal para valor do empréstimo
                            loan_modal = discord.ui.Modal(title=f"Empréstimo {loan_type.title()}")
                            
                            amount_input = discord.ui.TextInput(
                                label=f"Valor a solicitar (Máx: {max_amount:,})",
                                placeholder=f"Ex: {max_amount//2:,}",
                                min_length=1,
                                max_length=10
                            )
                            
                            loan_modal.add_item(amount_input)
                            
                            async def loan_callback(modal_interaction):
                                try:
                                    amount = int(modal_interaction.data["components"][0]["components"][0]["value"])
                                    
                                    if amount <= 0:
                                        await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                        return
                                    
                                    if amount > max_amount:
                                        await modal_interaction.response.send_message(f"❌ O valor máximo para este tipo de empréstimo é de {max_amount:,} coins!", ephemeral=True)
                                        return
                                    
                                    if amount < 1000:
                                        await modal_interaction.response.send_message("❌ O valor mínimo para empréstimo é de 1.000 coins!", ephemeral=True)
                                        return
                                    
                                    # Calcular juros e valor total a pagar
                                    interest_amount = int(amount * (interest_rate / 100))
                                    total_to_pay = amount + interest_amount
                                    
                                    # Calcular data de vencimento
                                    start_time = datetime.datetime.now()
                                    due_time = start_time + datetime.timedelta(days=days)
                                    
                                    # Registrar empréstimo no banco de dados
                                    conn = sqlite3.connect('database.db')
                                    cursor = conn.cursor()
                                    
                                    cursor.execute('''
                                        INSERT INTO bank_loans 
                                        (user_id, amount, interest_rate, start_time, due_time, paid_amount, status) 
                                        VALUES (?, ?, ?, ?, ?, 0, 'active')
                                    ''', (
                                        user_id, 
                                        amount, 
                                        interest_rate / 100, 
                                        start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                        due_time.strftime('%Y-%m-%d %H:%M:%S')
                                    ))
                                    
                                    conn.commit()
                                    
                                    # Adicionar o valor do empréstimo à carteira do usuário
                                    result = UserService.add_coins(
                                        user_id,
                                        amount,
                                        f"Empréstimo bancário ({loan_type})"
                                    )
                                    
                                    if not result[0]:
                                        # Reverter a criação do empréstimo em caso de erro
                                        cursor.execute('DELETE FROM bank_loans WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
                                        conn.commit()
                                        conn.close()
                                        
                                        await modal_interaction.response.send_message("❌ Erro ao processar empréstimo!", ephemeral=True)
                                        return
                                    
                                    conn.close()
                                    
                                    # Criar embed de confirmação
                                    success_embed = discord.Embed(
                                        title="✅ EMPRÉSTIMO APROVADO",
                                        description=(
                                            f"Você recebeu **{amount:,}** coins!\n\n"
                                            f"**Taxa de juros:** {interest_rate}%\n"
                                            f"**Valor a pagar:** {total_to_pay:,} coins\n"
                                            f"**Data de vencimento:** {due_time.strftime('%d/%m/%Y às %H:%M')}\n\n"
                                            "Use o comando `/banco` e o botão **Pagar Empréstimo** para quitar sua dívida."
                                        ),
                                        color=discord.Color.green()
                                    )
                                    
                                    await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                    
                                except ValueError:
                                    await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                            
                            loan_modal.on_submit = loan_callback
                            await interaction.response.send_modal(loan_modal)
                    
                    # Enviar embed com opções de empréstimo
                    await button_interaction.response.send_message(embed=loan_embed, view=LoanView(), ephemeral=True)
                
                @discord.ui.button(label="Transferir", style=discord.ButtonStyle.success, emoji="↗️", row=1)
                async def transferir_banco(self, button_interaction, button):
                    if self.bank_balance < 100:
                        await button_interaction.response.send_message("❌ Saldo bancário insuficiente para transferência.", ephemeral=True)
                        return
                    
                    # Modal para transferência bancária
                    transfer_modal = discord.ui.Modal(title="Transferência Bancária")
                    
                    user_id_input = discord.ui.TextInput(
                        label="ID do usuário destinatário",
                        placeholder="Ex: 123456789012345678",
                        min_length=10,
                        max_length=20
                    )
                    
                    amount_input = discord.ui.TextInput(
                        label=f"Valor a transferir (Máx: {self.bank_balance:,})",
                        placeholder="Ex: 1000",
                        min_length=1,
                        max_length=10
                    )
                    
                    transfer_modal.add_item(user_id_input)
                    transfer_modal.add_item(amount_input)
                    
                    async def transfer_callback(modal_interaction):
                        try:
                            dest_user_id = modal_interaction.data["components"][0]["components"][0]["value"].strip()
                            amount = int(modal_interaction.data["components"][1]["components"][0]["value"])
                            
                            # Verificar entradas válidas
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                return
                            
                            if amount > self.bank_balance:
                                await modal_interaction.response.send_message("❌ Saldo bancário insuficiente!", ephemeral=True)
                                return
                            
                            # Verificar se é uma transferência para si mesmo
                            if dest_user_id == user_id:
                                await modal_interaction.response.send_message("❌ Você não pode transferir para você mesmo!", ephemeral=True)
                                return
                            
                            # Verificar se o destinatário existe
                            conn = sqlite3.connect('database.db')
                            cursor = conn.cursor()
                            
                            # Verificar se o destinatário tem conta bancária
                            cursor.execute('SELECT COUNT(*) FROM bank_accounts WHERE user_id = ?', (dest_user_id,))
                            has_account = cursor.fetchone()[0] or 0
                            
                            if has_account == 0:
                                await modal_interaction.response.send_message("❌ O destinatário não possui uma conta bancária!", ephemeral=True)
                                conn.close()
                                return
                            
                            # Verificar se o usuário destinatário existe
                            cursor.execute('SELECT username FROM users WHERE user_id = ?', (dest_user_id,))
                            dest_user = cursor.fetchone()
                            
                            if not dest_user:
                                await modal_interaction.response.send_message("❌ Usuário destinatário não encontrado!", ephemeral=True)
                                conn.close()
                                return
                            
                            dest_username = dest_user[0]
                            
                            # Processar a transferência
                            # 1. Remover do remetente
                            cursor.execute(
                                'UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?',
                                (amount, user_id)
                            )
                            
                            # 2. Adicionar ao destinatário
                            cursor.execute(
                                'UPDATE bank_accounts SET balance = balance + ? WHERE user_id = ?',
                                (amount, dest_user_id)
                            )
                            
                            conn.commit()
                            conn.close()
                            
                            # Atualizar saldo para próxima interação
                            self.bank_balance -= amount
                            
                            # Criar embed de sucesso
                            success_embed = discord.Embed(
                                title="✅ TRANSFERÊNCIA BANCÁRIA REALIZADA",
                                description=f"Você transferiu **{amount:,}** coins para **{dest_username}**!",
                                color=discord.Color.green()
                            )
                            
                            success_embed.add_field(
                                name="💰 Novo saldo bancário", 
                                value=f"**{self.bank_balance:,}** coins",
                                inline=True
                            )
                            
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Por favor, insira valores válidos!", ephemeral=True)
                    
                    transfer_modal.on_submit = transfer_callback
                    await button_interaction.response.send_modal(transfer_modal)
                
                @discord.ui.button(label="Pagar Empréstimo", style=discord.ButtonStyle.danger, emoji="💳", row=2)
                async def pagar_emprestimo(self, button_interaction, button):
                    # Verificar se há empréstimos ativos
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT id, amount, interest_rate, start_time, due_time, paid_amount 
                        FROM bank_loans 
                        WHERE user_id = ? AND status = "active" 
                        ORDER BY due_time ASC
                    ''', (user_id,))
                    
                    loans = cursor.fetchall()
                    conn.close()
                    
                    if not loans:
                        await button_interaction.response.send_message("✅ Você não possui nenhum empréstimo ativo no momento.", ephemeral=True)
                        return
                    
                    loan = loans[0]  # Pegar o primeiro empréstimo (mais antigo)
                    loan_id = loan[0]
                    loan_amount = loan[1]
                    interest_rate = loan[2]
                    start_time = datetime.datetime.strptime(loan[3], '%Y-%m-%d %H:%M:%S')
                    due_time = datetime.datetime.strptime(loan[4], '%Y-%m-%d %H:%M:%S')
                    paid_amount = loan[5]
                    
                    # Calcular valor total a pagar
                    total_amount = int(loan_amount * (1 + interest_rate))
                    remaining_amount = total_amount - paid_amount
                    
                    # Criar modal para pagamento
                    payment_modal = discord.ui.Modal(title="Pagamento de Empréstimo")
                    
                    payment_input = discord.ui.TextInput(
                        label=f"Valor a pagar (Máx: {min(self.user_coins, remaining_amount):,})",
                        placeholder=f"Ex: {min(1000, remaining_amount):,}",
                        min_length=1,
                        max_length=10
                    )
                    
                    payment_modal.add_item(payment_input)
                    
                    async def payment_callback(modal_interaction):
                        try:
                            amount = int(modal_interaction.data["components"][0]["components"][0]["value"])
                            
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ O valor deve ser positivo!", ephemeral=True)
                                return
                            
                            if amount > self.user_coins:
                                await modal_interaction.response.send_message("❌ Saldo insuficiente na carteira!", ephemeral=True)
                                return
                            
                            if amount > remaining_amount:
                                amount = remaining_amount  # Limitar ao valor restante
                            
                            # Atualizar saldo na carteira
                            result = UserService.remove_coins(
                                user_id,
                                amount,
                                "Pagamento de empréstimo"
                            )
                            
                            if not result[0]:
                                await modal_interaction.response.send_message("❌ Erro ao processar pagamento!", ephemeral=True)
                                return
                            
                            # Atualizar empréstimo
                            conn = sqlite3.connect('database.db')
                            cursor = conn.cursor()
                            
                            # Atualizar valor pago
                            cursor.execute(
                                'UPDATE bank_loans SET paid_amount = paid_amount + ? WHERE id = ?',
                                (amount, loan_id)
                            )
                            
                            # Verificar se o empréstimo foi totalmente pago
                            cursor.execute('SELECT paid_amount FROM bank_loans WHERE id = ?', (loan_id,))
                            new_paid_amount = cursor.fetchone()[0]
                            
                            # Se totalmente pago, marcar como concluído
                            if new_paid_amount >= total_amount:
                                cursor.execute(
                                    'UPDATE bank_loans SET status = "paid", paid_amount = ? WHERE id = ?',
                                    (total_amount, loan_id)
                                )
                                
                                # Adicionar bônus de crédito ao usuário
                                cursor.execute(
                                    'UPDATE users SET credit_score = credit_score + ? WHERE user_id = ?',
                                    (int(loan_amount * 0.01), user_id)  # 1% do valor como pontos de crédito
                                )
                                
                                loan_fully_paid = True
                            else:
                                loan_fully_paid = False
                            
                            conn.commit()
                            conn.close()
                            
                            # Atualizar saldo para próxima interação
                            self.user_coins -= amount
                            
                            # Criar embed de sucesso
                            if loan_fully_paid:
                                success_embed = discord.Embed(
                                    title="✅ EMPRÉSTIMO QUITADO",
                                    description=(
                                        f"Você pagou **{amount:,}** coins e quitou seu empréstimo!\n\n"
                                        f"**Bônus de crédito:** +{int(loan_amount * 0.01)} pontos\n"
                                        "Ter um bom histórico de crédito aumenta seus limites futuros."
                                    ),
                                    color=discord.Color.green()
                                )
                            else:
                                new_remaining = total_amount - new_paid_amount
                                success_embed = discord.Embed(
                                    title="✅ PAGAMENTO REALIZADO",
                                    description=(
                                        f"Você pagou **{amount:,}** coins do seu empréstimo!\n\n"
                                        f"**Valor restante:** {new_remaining:,} coins\n"
                                        f"**Data de vencimento:** {due_time.strftime('%d/%m/%Y às %H:%M')}"
                                    ),
                                    color=discord.Color.gold()
                                )
                            
                            success_embed.add_field(
                                name="👛 Saldo na carteira", 
                                value=f"**{self.user_coins:,}** coins",
                                inline=True
                            )
                            
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                    
                    payment_modal.on_submit = payment_callback
                    await button_interaction.response.send_modal(payment_modal)
                
                @discord.ui.button(label="Histórico", style=discord.ButtonStyle.secondary, emoji="📜", row=2)
                async def historico(self, button_interaction, button):
                    try:
                        # Buscar histórico de transações
                        conn = sqlite3.connect('database.db')
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            SELECT description, amount, timestamp 
                            FROM transactions 
                            WHERE user_id = ? AND (description LIKE '%banco%' OR description LIKE '%depósito%' OR description LIKE '%saque%' OR description LIKE '%empréstimo%')
                            ORDER BY timestamp DESC LIMIT 10
                        ''', (user_id,))
                        
                        transactions = cursor.fetchall()
                        conn.close()
                        
                        if not transactions:
                            await button_interaction.response.send_message("❌ Não há transações bancárias no histórico.", ephemeral=True)
                            return
                        
                        # Criar embed com histórico
                        history_embed = discord.Embed(
                            title="📜 HISTÓRICO BANCÁRIO",
                            description="Suas últimas 10 transações bancárias:",
                            color=discord.Color.blue()
                        )
                        
                        for desc, amount, timestamp in transactions:
                            # Formatar data e hora
                            date_obj = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                            
                            # Formatar valor com símbolo baseado no tipo de transação
                            if "depósito" in desc.lower():
                                value_str = f"➖ {amount:,} coins"  # Saiu da carteira
                            elif "saque" in desc.lower():
                                value_str = f"➕ {amount:,} coins"  # Entrou na carteira
                            elif "empréstimo" in desc.lower():
                                value_str = f"➕ {amount:,} coins"  # Entrou na carteira
                            else:
                                value_str = f"{amount:,} coins"
                            
                            history_embed.add_field(
                                name=f"📝 {date_str}",
                                value=f"**{desc}**\n{value_str}",
                                inline=False
                            )
                        
                        await button_interaction.response.send_message(embed=history_embed, ephemeral=True)
                        
                    except Exception as e:
                        logger.error(f"Erro ao buscar histórico bancário: {e}")
                        await button_interaction.response.send_message("❌ Erro ao buscar histórico de transações.", ephemeral=True)
            
            # Criar e enviar a view
            bank_view = BankView(user_coins, banco_saldo)
            await interaction.followup.send(embed=embed, view=bank_view, ephemeral=True)
            
            # Fechar conexão com o banco de dados
            conn.close()
            
            # Adicionar XP pelo uso do comando
            await XPGainManager.add_command_xp(user_id, username, "banco")
            
        except Exception as e:
            logger.error(f"Erro no comando banco: {e}")
            embed = discord.Embed(
                title="❌ ERRO NO BANCO",
                description="Ocorreu um erro ao acessar o sistema bancário. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="rifa", description="Participe da rifa e concorra a um prêmio!")
    async def rifa(self, interaction: discord.Interaction):
        """Comando de rifa para ganhar coins"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        try:
            # Obter dados do usuário
            user = UserService.ensure_user_exists(user_id, username)
            
            if not user:
                embed = discord.Embed(
                    title="❌ ERRO AO PARTICIPAR DA RIFA",
                    description="Ocorreu um erro ao acessar sua conta. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            user_coins = user[2]
            
            # Verificar se a tabela raffle existe, se não, criar
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raffle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    active INTEGER DEFAULT 1,
                    prize INTEGER DEFAULT 0,
                    end_time TEXT,
                    winner_id TEXT DEFAULT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raffle_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raffle_id INTEGER,
                    user_id TEXT,
                    tickets INTEGER DEFAULT 1,
                    purchase_time TEXT,
                    FOREIGN KEY (raffle_id) REFERENCES raffle (id)
                )
            ''')
            conn.commit()
            
            # Verificar se existe uma rifa ativa
            cursor.execute('SELECT id, prize, end_time FROM raffle WHERE active = 1 ORDER BY id DESC LIMIT 1')
            rifa_atual = cursor.fetchone()
            
            now = datetime.datetime.now()
            
            if not rifa_atual:
                # Criar nova rifa
                premio_inicial = 5000
                end_time = now + datetime.timedelta(days=1)
                
                cursor.execute(
                    'INSERT INTO raffle (prize, end_time) VALUES (?, ?)',
                    (premio_inicial, end_time.strftime('%Y-%m-%d %H:%M:%S'))
                )
                conn.commit()
                
                # Pegar ID da rifa criada
                cursor.execute('SELECT last_insert_rowid()')
                rifa_id = cursor.fetchone()[0]
                
                embed = discord.Embed(
                    title="🎫 NOVA RIFA CRIADA!",
                    description=f"Uma nova rifa foi iniciada com prêmio inicial de **{premio_inicial:,}** coins!",
                    color=discord.Color.gold()
                )
                
                end_time_str = end_time.strftime('%d/%m/%Y às %H:%M')
                
                embed.add_field(
                    name="⏱️ Termina em",
                    value=f"{end_time_str}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎟️ Preço do bilhete",
                    value="50 coins",
                    inline=True
                )
                
                # Criar view para comprar bilhetes
                class FirstRaffleView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=60)
                    
                    @discord.ui.button(label="Comprar Bilhete", style=discord.ButtonStyle.success, emoji="🎟️")
                    async def comprar_bilhete(self, button_interaction, button):
                        # Modal para comprar bilhetes
                        ticket_modal = discord.ui.Modal(title="Comprar Bilhetes da Rifa")
                        
                        quantity_input = discord.ui.TextInput(
                            label=f"Quantos bilhetes? (50 coins cada)",
                            placeholder="Ex: 5",
                            min_length=1,
                            max_length=3,
                            default="1"
                        )
                        
                        ticket_modal.add_item(quantity_input)
                        
                        async def ticket_callback(modal_interaction):
                            try:
                                quantity = int(modal_interaction.data["components"][0]["components"][0]["value"])
                                
                                if quantity <= 0:
                                    await modal_interaction.response.send_message("❌ A quantidade deve ser positiva!", ephemeral=True)
                                    return
                                
                                # Calcular custo total
                                custo_total = quantity * 50
                                
                                # Verificar saldo
                                user_data = UserService.get_user(user_id)
                                current_coins = user_data[2]
                                
                                if current_coins < custo_total:
                                    await modal_interaction.response.send_message(f"❌ Saldo insuficiente! Você precisa de {custo_total:,} coins.", ephemeral=True)
                                    return
                                
                                # Remover coins
                                result = UserService.remove_coins(
                                    user_id, 
                                    custo_total,
                                    f"Compra de {quantity} bilhete(s) de rifa"
                                )
                                
                                if not result[0]:
                                    await modal_interaction.response.send_message("❌ Erro ao processar pagamento!", ephemeral=True)
                                    return
                                
                                # Registrar bilhetes comprados
                                conn = sqlite3.connect('database.db')
                                cursor = conn.cursor()
                                
                                # Verificar se já tem bilhetes
                                cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, rifa_id))
                                existing = cursor.fetchone()
                                
                                if existing:
                                    # Adicionar mais bilhetes
                                    cursor.execute(
                                        'UPDATE raffle_tickets SET tickets = tickets + ? WHERE user_id = ? AND raffle_id = ?',
                                        (quantity, user_id, rifa_id)
                                    )
                                else:
                                    # Registrar novos bilhetes
                                    cursor.execute(
                                        'INSERT INTO raffle_tickets (raffle_id, user_id, tickets, purchase_time) VALUES (?, ?, ?, ?)',
                                        (rifa_id, user_id, quantity, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                    )
                                
                                # Aumentar o prêmio em 80% do valor gasto
                                adicional_premio = int(custo_total * 0.8)
                                cursor.execute(
                                    'UPDATE raffle SET prize = prize + ? WHERE id = ?',
                                    (adicional_premio, rifa_id)
                                )
                                
                                conn.commit()
                                
                                # Obter informações atualizadas
                                cursor.execute('SELECT prize FROM raffle WHERE id = ?', (rifa_id,))
                                premio_atual = cursor.fetchone()[0]
                                
                                cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                                total_bilhetes = cursor.fetchone()[0] or 0
                                
                                cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, rifa_id))
                                meus_bilhetes = cursor.fetchone()[0]
                                
                                conn.close()
                                
                                # Calcular probabilidade de ganhar
                                chance = (meus_bilhetes / total_bilhetes) * 100 if total_bilhetes > 0 else 0
                                
                                # Criar embed de sucesso
                                success_embed = discord.Embed(
                                    title="✅ BILHETES COMPRADOS COM SUCESSO",
                                    description=f"Você comprou **{quantity}** bilhete(s) por **{custo_total:,}** coins!",
                                    color=discord.Color.green()
                                )
                                
                                success_embed.add_field(
                                    name="🎫 Seus bilhetes", 
                                    value=f"**{meus_bilhetes}** bilhete(s)",
                                    inline=True
                                )
                                
                                success_embed.add_field(
                                    name="🍀 Chance de ganhar", 
                                    value=f"**{chance:.2f}%**",
                                    inline=True
                                )
                                
                                success_embed.add_field(
                                    name="🏆 Prêmio atual", 
                                    value=f"**{premio_atual:,}** coins",
                                    inline=True
                                )
                                
                                await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                
                            except ValueError:
                                await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                        
                        ticket_modal.on_submit = ticket_callback
                        await button_interaction.response.send_modal(ticket_modal)
                    
                    @discord.ui.button(label="Ver Participantes", style=discord.ButtonStyle.secondary, emoji="👥")
                    async def ver_participantes(self, button_interaction, button):
                        conn = sqlite3.connect('database.db')
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            SELECT user_id, tickets FROM raffle_tickets 
                            WHERE raffle_id = ? 
                            ORDER BY tickets DESC LIMIT 10
                        ''', (rifa_id,))
                        
                        participantes = cursor.fetchall()
                        
                        cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                        total_bilhetes = cursor.fetchone()[0] or 0
                        
                        conn.close()
                        
                        if not participantes:
                            await button_interaction.response.send_message("Ainda não há participantes nesta rifa!", ephemeral=True)
                            return
                        
                        # Criar embed com participantes
                        participants_embed = discord.Embed(
                            title="👥 PARTICIPANTES DA RIFA",
                            description=f"Total de **{total_bilhetes}** bilhetes vendidos",
                            color=discord.Color.blue()
                        )
                        
                        for i, (participant_id, tickets) in enumerate(participantes, 1):
                            # Tentar obter username
                            try:
                                user = await interaction.client.fetch_user(int(participant_id))
                                name = user.name
                            except:
                                name = f"Usuário {participant_id}"
                            
                            # Calcular chance
                            chance = (tickets / total_bilhetes) * 100 if total_bilhetes > 0 else 0
                            
                            participants_embed.add_field(
                                name=f"#{i} {name}",
                                value=f"**{tickets}** bilhetes ({chance:.2f}% de chance)",
                                inline=False
                            )
                        
                        await button_interaction.response.send_message(embed=participants_embed, ephemeral=True)
                
                await interaction.followup.send(embed=embed, view=FirstRaffleView(), ephemeral=True)
                
            else:
                # Rifa existente
                rifa_id, premio, end_time_str = rifa_atual
                end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                
                # Verificar se a rifa já acabou
                if now > end_time:
                    # Processo de sorteio
                    cursor.execute('SELECT user_id, tickets FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                    participantes = cursor.fetchall()
                    
                    if not participantes:
                        # Sem participantes, estender a rifa
                        new_end_time = now + datetime.timedelta(days=1)
                        cursor.execute(
                            'UPDATE raffle SET end_time = ? WHERE id = ?',
                            (new_end_time.strftime('%Y-%m-%d %H:%M:%S'), rifa_id)
                        )
                        conn.commit()
                        
                        embed = discord.Embed(
                            title="🎫 RIFA ESTENDIDA",
                            description=f"A rifa foi estendida por mais 24h pois não houve participantes!\nPrêmio atual: **{premio:,}** coins",
                            color=discord.Color.gold()
                        )
                        
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        # Criar lista com bilhetes (quanto mais bilhetes, mais entradas na lista)
                        ticket_pool = []
                        
                        for p_user_id, p_tickets in participantes:
                            ticket_pool.extend([p_user_id] * p_tickets)
                        
                        # Sortear ganhador
                        winner_id = random.choice(ticket_pool)
                        
                        # Atualizar rifa como finalizada e definir ganhador
                        cursor.execute(
                            'UPDATE raffle SET active = 0, winner_id = ? WHERE id = ?',
                            (winner_id, rifa_id)
                        )
                        conn.commit()
                        
                        # Pagar o prêmio
                        UserService.add_coins(
                            winner_id,
                            premio,
                            "Premiação de rifa"
                        )
                        
                        # Iniciar nova rifa
                        premio_inicial = 5000
                        new_end_time = now + datetime.timedelta(days=1)
                        
                        cursor.execute(
                            'INSERT INTO raffle (prize, end_time) VALUES (?, ?)',
                            (premio_inicial, new_end_time.strftime('%Y-%m-%d %H:%M:%S'))
                        )
                        conn.commit()
                        
                        # Obter ID da nova rifa
                        cursor.execute('SELECT last_insert_rowid()')
                        novo_rifa_id = cursor.fetchone()[0]
                        
                        # Tentar obter username do ganhador
                        try:
                            winner = await interaction.client.fetch_user(int(winner_id))
                            winner_name = winner.name
                        except:
                            winner_name = f"Usuário {winner_id}"
                        
                        # Enviar resultado e nova rifa
                        embed = discord.Embed(
                            title="🎉 RESULTADO DA RIFA",
                            description=f"🏆 **{winner_name}** ganhou **{premio:,}** coins!",
                            color=discord.Color.gold()
                        )
                        
                        embed.add_field(
                            name="🎫 NOVA RIFA",
                            value=f"Uma nova rifa já foi iniciada com prêmio de **{premio_inicial:,}** coins!",
                            inline=False
                        )
                        
                        class NewRaffleView(discord.ui.View):
                            def __init__(self):
                                super().__init__(timeout=60)
                            
                            @discord.ui.button(label="Comprar Bilhetes", style=discord.ButtonStyle.success, emoji="🎟️")
                            async def comprar_bilhete(self, button_interaction, button):
                                # Modal para comprar bilhetes
                                ticket_modal = discord.ui.Modal(title="Comprar Bilhetes da Rifa")
                                
                                quantity_input = discord.ui.TextInput(
                                    label=f"Quantos bilhetes? (50 coins cada)",
                                    placeholder="Ex: 5",
                                    min_length=1,
                                    max_length=3,
                                    default="1"
                                )
                                
                                ticket_modal.add_item(quantity_input)
                                
                                async def ticket_callback(modal_interaction):
                                    try:
                                        quantity = int(modal_interaction.data["components"][0]["components"][0]["value"])
                                        
                                        if quantity <= 0:
                                            await modal_interaction.response.send_message("❌ A quantidade deve ser positiva!", ephemeral=True)
                                            return
                                        
                                        # Calcular custo total
                                        custo_total = quantity * 50
                                        
                                        # Verificar saldo
                                        user_data = UserService.get_user(user_id)
                                        current_coins = user_data[2]
                                        
                                        if current_coins < custo_total:
                                            await modal_interaction.response.send_message(f"❌ Saldo insuficiente! Você precisa de {custo_total:,} coins.", ephemeral=True)
                                            return
                                        
                                        # Remover coins
                                        result = UserService.remove_coins(
                                            user_id, 
                                            custo_total,
                                            f"Compra de {quantity} bilhete(s) de rifa"
                                        )
                                        
                                        if not result[0]:
                                            await modal_interaction.response.send_message("❌ Erro ao processar pagamento!", ephemeral=True)
                                            return
                                        
                                        # Registrar bilhetes comprados
                                        conn = sqlite3.connect('database.db')
                                        cursor = conn.cursor()
                                        
                                        # Verificar se já tem bilhetes
                                        cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, novo_rifa_id))
                                        existing = cursor.fetchone()
                                        
                                        if existing:
                                            # Adicionar mais bilhetes
                                            cursor.execute(
                                                'UPDATE raffle_tickets SET tickets = tickets + ? WHERE user_id = ? AND raffle_id = ?',
                                                (quantity, user_id, novo_rifa_id)
                                            )
                                        else:
                                            # Registrar novos bilhetes
                                            cursor.execute(
                                                'INSERT INTO raffle_tickets (raffle_id, user_id, tickets, purchase_time) VALUES (?, ?, ?, ?)',
                                                (novo_rifa_id, user_id, quantity, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                            )
                                        
                                        # Aumentar o prêmio em 80% do valor gasto
                                        adicional_premio = int(custo_total * 0.8)
                                        cursor.execute(
                                            'UPDATE raffle SET prize = prize + ? WHERE id = ?',
                                            (adicional_premio, novo_rifa_id)
                                        )
                                        
                                        conn.commit()
                                        
                                        # Obter informações atualizadas
                                        cursor.execute('SELECT prize FROM raffle WHERE id = ?', (novo_rifa_id,))
                                        premio_atual = cursor.fetchone()[0]
                                        
                                        cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (novo_rifa_id,))
                                        total_bilhetes = cursor.fetchone()[0] or 0
                                        
                                        cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, novo_rifa_id))
                                        meus_bilhetes = cursor.fetchone()[0]
                                        
                                        conn.close()
                                        
                                        # Calcular probabilidade de ganhar
                                        chance = (meus_bilhetes / total_bilhetes) * 100 if total_bilhetes > 0 else 0
                                        
                                        # Criar embed de sucesso
                                        success_embed = discord.Embed(
                                            title="✅ BILHETES COMPRADOS COM SUCESSO",
                                            description=f"Você comprou **{quantity}** bilhete(s) por **{custo_total:,}** coins!",
                                            color=discord.Color.green()
                                        )
                                        
                                        success_embed.add_field(
                                            name="🎫 Seus bilhetes", 
                                            value=f"**{meus_bilhetes}** bilhete(s)",
                                            inline=True
                                        )
                                        
                                        success_embed.add_field(
                                            name="🍀 Chance de ganhar", 
                                            value=f"**{chance:.2f}%**",
                                            inline=True
                                        )
                                        
                                        success_embed.add_field(
                                            name="🏆 Prêmio atual", 
                                            value=f"**{premio_atual:,}** coins",
                                            inline=True
                                        )
                                        
                                        await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                        
                                    except ValueError:
                                        await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                                
                                ticket_modal.on_submit = ticket_callback
                                await button_interaction.response.send_modal(ticket_modal)
                        
                        await interaction.followup.send(embed=embed, view=NewRaffleView(), ephemeral=True)
                else:
                    # Rifa em andamento
                    # Obter dados da rifa
                    cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                    total_bilhetes = cursor.fetchone()[0] or 0
                    
                    cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, rifa_id))
                    meus_bilhetes = cursor.fetchone()[0] if cursor.fetchone() else 0
                    
                    # Calcular tempo restante
                    time_left = end_time - now
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    
                    # Calcular chance de ganhar
                    chance = (meus_bilhetes / total_bilhetes) * 100 if total_bilhetes > 0 and meus_bilhetes else 0
                    
                    # Criar embed
                    embed = discord.Embed(
                        title="🎫 RIFA EM ANDAMENTO",
                        description=f"Prêmio atual: **{premio:,}** coins\n\n",
                        color=discord.Color.gold()
                    )
                    
                    embed.add_field(
                        name="⏱️ Tempo restante",
                        value=f"**{hours_left}h {minutes_left}m**",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎟️ Total de bilhetes",
                        value=f"**{total_bilhetes}** bilhetes",
                        inline=True
                    )
                    
                    if meus_bilhetes:
                        embed.add_field(
                            name="🎫 Seus bilhetes",
                            value=f"**{meus_bilhetes}** bilhetes",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="🍀 Sua chance",
                            value=f"**{chance:.2f}%**",
                            inline=True
                        )
                    
                    # Criar view para comprar bilhetes
                    class SecondRaffleView(discord.ui.View):
                        def __init__(self):
                            super().__init__(timeout=60)
                        
                        @discord.ui.button(label="Comprar Bilhete", style=discord.ButtonStyle.success, emoji="🎟️")
                        async def comprar_bilhete(self, button_interaction, button):
                            # Modal para comprar bilhetes
                            ticket_modal = discord.ui.Modal(title="Comprar Bilhetes da Rifa")
                            
                            quantity_input = discord.ui.TextInput(
                                label=f"Quantos bilhetes? (50 coins cada)",
                                placeholder="Ex: 5",
                                min_length=1,
                                max_length=3,
                                default="1"
                            )
                            
                            ticket_modal.add_item(quantity_input)
                            
                            async def ticket_callback(modal_interaction):
                                try:
                                    quantity = int(modal_interaction.data["components"][0]["components"][0]["value"])
                                    
                                    if quantity <= 0:
                                        await modal_interaction.response.send_message("❌ A quantidade deve ser positiva!", ephemeral=True)
                                        return
                                    
                                    # Calcular custo total
                                    custo_total = quantity * 50
                                    
                                    # Verificar saldo
                                    user_data = UserService.get_user(user_id)
                                    current_coins = user_data[2]
                                    
                                    if current_coins < custo_total:
                                        await modal_interaction.response.send_message(f"❌ Saldo insuficiente! Você precisa de {custo_total:,} coins.", ephemeral=True)
                                        return
                                    
                                    # Remover coins
                                    result = UserService.remove_coins(
                                        user_id, 
                                        custo_total,
                                        f"Compra de {quantity} bilhete(s) de rifa"
                                    )
                                    
                                    if not result[0]:
                                        await modal_interaction.response.send_message("❌ Erro ao processar pagamento!", ephemeral=True)
                                        return
                                    
                                    # Registrar bilhetes comprados
                                    conn = sqlite3.connect('database.db')
                                    cursor = conn.cursor()
                                    
                                    # Verificar se já tem bilhetes
                                    cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, rifa_id))
                                    existing = cursor.fetchone()
                                    
                                    if existing:
                                        # Adicionar mais bilhetes
                                        cursor.execute(
                                            'UPDATE raffle_tickets SET tickets = tickets + ? WHERE user_id = ? AND raffle_id = ?',
                                            (quantity, user_id, rifa_id)
                                        )
                                    else:
                                        # Registrar novos bilhetes
                                        cursor.execute(
                                            'INSERT INTO raffle_tickets (raffle_id, user_id, tickets, purchase_time) VALUES (?, ?, ?, ?)',
                                            (rifa_id, user_id, quantity, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                        )
                                    
                                    # Aumentar o prêmio em 80% do valor gasto
                                    adicional_premio = int(custo_total * 0.8)
                                    cursor.execute(
                                        'UPDATE raffle SET prize = prize + ? WHERE id = ?',
                                        (adicional_premio, rifa_id)
                                    )
                                    
                                    conn.commit()
                                    
                                    # Obter informações atualizadas
                                    cursor.execute('SELECT prize FROM raffle WHERE id = ?', (rifa_id,))
                                    premio_atual = cursor.fetchone()[0]
                                    
                                    cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                                    total_bilhetes = cursor.fetchone()[0] or 0
                                    
                                    cursor.execute('SELECT tickets FROM raffle_tickets WHERE user_id = ? AND raffle_id = ?', (user_id, rifa_id))
                                    meus_bilhetes = cursor.fetchone()[0]
                                    
                                    conn.close()
                                    
                                    # Calcular probabilidade de ganhar
                                    chance = (meus_bilhetes / total_bilhetes) * 100 if total_bilhetes > 0 else 0
                                    
                                    # Criar embed de sucesso
                                    success_embed = discord.Embed(
                                        title="✅ BILHETES COMPRADOS COM SUCESSO",
                                        description=f"Você comprou **{quantity}** bilhete(s) por **{custo_total:,}** coins!",
                                        color=discord.Color.green()
                                    )
                                    
                                    success_embed.add_field(
                                        name="🎫 Seus bilhetes", 
                                        value=f"**{meus_bilhetes}** bilhete(s)",
                                        inline=True
                                    )
                                    
                                    success_embed.add_field(
                                        name="🍀 Chance de ganhar", 
                                        value=f"**{chance:.2f}%**",
                                        inline=True
                                    )
                                    
                                    success_embed.add_field(
                                        name="🏆 Prêmio atual", 
                                        value=f"**{premio_atual:,}** coins",
                                        inline=True
                                    )
                                    
                                    await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                    
                                except ValueError:
                                    await modal_interaction.response.send_message("❌ Por favor, insira um valor válido!", ephemeral=True)
                            
                            ticket_modal.on_submit = ticket_callback
                            await button_interaction.response.send_modal(ticket_modal)
                        
                        @discord.ui.button(label="Ver Participantes", style=discord.ButtonStyle.secondary, emoji="👥")
                        async def ver_participantes(self, button_interaction, button):
                            conn = sqlite3.connect('database.db')
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                SELECT user_id, tickets FROM raffle_tickets 
                                WHERE raffle_id = ? 
                                ORDER BY tickets DESC LIMIT 10
                            ''', (rifa_id,))
                            
                            participantes = cursor.fetchall()
                            
                            cursor.execute('SELECT SUM(tickets) FROM raffle_tickets WHERE raffle_id = ?', (rifa_id,))
                            total_bilhetes = cursor.fetchone()[0] or 0
                            
                            conn.close()
                            
                            if not participantes:
                                await button_interaction.response.send_message("Ainda não há participantes nesta rifa!", ephemeral=True)
                                return
                            
                            # Criar embed com participantes
                            participants_embed = discord.Embed(
                                title="👥 PARTICIPANTES DA RIFA",
                                description=f"Total de **{total_bilhetes}** bilhetes vendidos",
                                color=discord.Color.blue()
                            )
                            
                            for i, (participant_id, tickets) in enumerate(participantes, 1):
                                # Tentar obter username
                                try:
                                    user = await interaction.client.fetch_user(int(participant_id))
                                    name = user.name
                                except:
                                    name = f"Usuário {participant_id}"
                                
                                # Calcular chance
                                chance = (tickets / total_bilhetes) * 100 if total_bilhetes > 0 else 0
                                
                                participants_embed.add_field(
                                    name=f"#{i} {name}",
                                    value=f"**{tickets}** bilhetes ({chance:.2f}% de chance)",
                                    inline=False
                                )
                            
                            await button_interaction.response.send_message(embed=participants_embed, ephemeral=True)
                    
                    await interaction.followup.send(embed=embed, view=SecondRaffleView(), ephemeral=True)
            
            # Fechar conexão com o banco de dados
            conn.close()
            
            # Adicionar XP pelo uso do comando
            await XPGainManager.add_command_xp(user_id, username, "rifa")
            
        except Exception as e:
            logger.error(f"Erro no comando rifa: {e}")
            embed = discord.Embed(
                title="❌ ERRO NA RIFA",
                description="Ocorreu um erro ao acessar o sistema de rifa. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="roubar", description="Tente roubar coins de outro usuário, mas cuidado com a polícia!")
    @app_commands.describe(usuario="Usuário que você deseja roubar")
    async def roubar(self, interaction: discord.Interaction, usuario: discord.Member):
        """Sistema de roubo com polícia e prisão"""
        await interaction.response.defer(ephemeral=True)
        
        if usuario.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ ERRO",
                description="Você não pode roubar a si mesmo!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        target_id = str(usuario.id)
        username = interaction.user.name
        
        try:
            # Verificar se a tabela para prisão existe, se não, criar
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jail (
                    user_id TEXT PRIMARY KEY,
                    release_time TEXT,
                    reason TEXT
                )
            ''')
            conn.commit()
            
            # Verificar se o usuário está preso
            cursor.execute('SELECT release_time, reason FROM jail WHERE user_id = ?', (user_id,))
            jail_info = cursor.fetchone()
            
            if jail_info:
                release_time = datetime.datetime.strptime(jail_info[0], '%Y-%m-%d %H:%M:%S')
                now = datetime.datetime.now()
                
                if now < release_time:
                    # Ainda está preso
                    time_left = release_time - now
                    minutes_left = int(time_left.total_seconds() // 60)
                    seconds_left = int(time_left.total_seconds() % 60)
                    
                    embed = discord.Embed(
                        title="🚔 VOCÊ ESTÁ PRESO",
                        description=f"Você não pode roubar enquanto está na prisão!\nMotivo: **{jail_info[1]}**",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="⏱️ Tempo restante",
                        value=f"**{minutes_left}m {seconds_left}s**"
                    )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    conn.close()
                    return
                else:
                    # Liberar da prisão
                    cursor.execute('DELETE FROM jail WHERE user_id = ?', (user_id,))
                    conn.commit()
            
            # Verificar se o alvo está preso (não pode roubar quem está preso)
            cursor.execute('SELECT 1 FROM jail WHERE user_id = ?', (target_id,))
            target_jailed = cursor.fetchone() is not None
            
            if target_jailed:
                embed = discord.Embed(
                    title="❌ FALHA NO ROUBO",
                    description=f"Você não pode roubar {usuario.name}, pois esta pessoa está na prisão!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                conn.close()
                return
            
            # Verificar cooldown (para evitar spam)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS robbery_cooldowns (
                    user_id TEXT PRIMARY KEY,
                    last_attempt TEXT
                )
            ''')
            conn.commit()
            
            cursor.execute('SELECT last_attempt FROM robbery_cooldowns WHERE user_id = ?', (user_id,))
            last_attempt = cursor.fetchone()
            
            now = datetime.datetime.now()
            
            if last_attempt:
                last_time = datetime.datetime.strptime(last_attempt[0], '%Y-%m-%d %H:%M:%S')
                time_diff = now - last_time
                
                if time_diff.total_seconds() < 300:  # 5 minutos de cooldown
                    # Ainda em cooldown
                    seconds_left = 300 - int(time_diff.total_seconds())
                    minutes_left = seconds_left // 60
                    seconds_remain = seconds_left % 60
                    
                    embed = discord.Embed(
                        title="⏳ AGUARDE",
                        description=f"Você precisa esperar mais **{minutes_left}m {seconds_remain}s** para tentar roubar novamente!",
                        color=discord.Color.orange()
                    )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    conn.close()
                    return
            
            # Obter dados dos usuários
            user = UserService.ensure_user_exists(user_id, username)
            target = UserService.ensure_user_exists(target_id, usuario.name)
            
            if not user or not target:
                embed = discord.Embed(
                    title="❌ ERRO AO PROCESSAR ROUBO",
                    description="Ocorreu um erro ao acessar as contas envolvidas. Tente novamente mais tarde.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                conn.close()
                return
            
            user_coins = user[2]
            target_coins = target[2]
            
            # Verificar se o alvo tem pelo menos 100 coins
            if target_coins < 100:
                embed = discord.Embed(
                    title="❌ FALHA NO ROUBO",
                    description=f"{usuario.name} não tem coins suficientes para valer a pena roubar!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                conn.close()
                return
            
            # Atualizar tempo de último roubo
            cursor.execute(
                'INSERT OR REPLACE INTO robbery_cooldowns (user_id, last_attempt) VALUES (?, ?)',
                (user_id, now.strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            
            # Calcular chance de sucesso (40% base)
            success_chance = 40
            
            # Modificadores de chance
            if user_coins < 1000:
                # Bônus para jogadores pobres
                success_chance += 10
            
            if target_coins > 10000:
                # Bônus para alvos ricos
                success_chance += 5
            
            # Chance de ser pego pela polícia (independente do sucesso do roubo)
            police_chance = 30
            
            # Decidir resultado do roubo
            robbery_success = random.randint(1, 100) <= success_chance
            caught_by_police = random.randint(1, 100) <= police_chance
            
            if robbery_success and not caught_by_police:
                # Roubo bem-sucedido
                # Calcular quantidade roubada (10-20% do saldo do alvo)
                stolen_percent = random.uniform(0.1, 0.2)
                stolen_amount = int(target_coins * stolen_percent)
                
                # Limitar o valor máximo que pode ser roubado
                max_steal = 5000
                if stolen_amount > max_steal:
                    stolen_amount = max_steal
                
                # Transferir coins
                UserService.remove_coins(
                    target_id,
                    stolen_amount,
                    f"Vítima de roubo por {username}"
                )
                
                UserService.add_coins(
                    user_id,
                    stolen_amount,
                    f"Roubo bem-sucedido de {usuario.name}"
                )
                
                # Embed de sucesso
                embed = discord.Embed(
                    title="💰 ROUBO BEM-SUCEDIDO",
                    description=f"Você roubou **{stolen_amount:,}** coins de {usuario.mention}!",
                    color=discord.Color.green()
                )
                
                # Registrar o roubo para estatísticas (opcional)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS robbery_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        robber_id TEXT,
                        victim_id TEXT,
                        amount INTEGER,
                        timestamp TEXT,
                        success INTEGER,
                        caught INTEGER
                    )
                ''')
                
                cursor.execute(
                    'INSERT INTO robbery_stats (robber_id, victim_id, amount, timestamp, success, caught) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, target_id, stolen_amount, now.strftime('%Y-%m-%d %H:%M:%S'), 1, 0)
                )
                conn.commit()
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            elif caught_by_police:
                # Preso pela polícia
                # Calcular multa (30-50% do valor que tentou roubar ou 10-20% do próprio saldo, o que for maior)
                potential_steal = int(target_coins * random.uniform(0.1, 0.2))
                max_steal = 5000
                if potential_steal > max_steal:
                    potential_steal = max_steal
                
                fine_percent = random.uniform(0.3, 0.5)
                fine_from_steal = int(potential_steal * fine_percent)
                
                user_fine_percent = random.uniform(0.1, 0.2)
                fine_from_balance = int(user_coins * user_fine_percent)
                
                fine = max(fine_from_steal, fine_from_balance)
                
                # Limitar a multa ao saldo do usuário
                if fine > user_coins:
                    fine = user_coins
                
                # Aplicar multa
                if fine > 0:
                    UserService.remove_coins(
                        user_id,
                        fine,
                        "Multa por tentativa de roubo"
                    )
                
                # Calcular tempo de prisão (5-15 minutos)
                jail_time = random.randint(5, 15)
                release_time = now + datetime.timedelta(minutes=jail_time)
                
                # Registrar na prisão
                cursor.execute(
                    'INSERT OR REPLACE INTO jail (user_id, release_time, reason) VALUES (?, ?, ?)',
                    (user_id, release_time.strftime('%Y-%m-%d %H:%M:%S'), "Tentativa de roubo")
                )
                
                # Registrar o roubo para estatísticas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS robbery_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        robber_id TEXT,
                        victim_id TEXT,
                        amount INTEGER,
                        timestamp TEXT,
                        success INTEGER,
                        caught INTEGER
                    )
                ''')
                
                cursor.execute(
                    'INSERT INTO robbery_stats (robber_id, victim_id, amount, timestamp, success, caught) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, target_id, 0, now.strftime('%Y-%m-%d %H:%M:%S'), 0, 1)
                )
                conn.commit()
                
                # Embed da prisão
                embed = discord.Embed(
                    title="🚔 PRESO EM FLAGRANTE",
                    description=(
                        f"Você foi pego pela polícia enquanto tentava roubar {usuario.mention}!\n\n"
                        f"**Multa:** {fine:,} coins\n"
                        f"**Tempo de prisão:** {jail_time} minutos"
                    ),
                    color=discord.Color.red()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            else:
                # Falha no roubo, mas não foi pego
                # Registrar o roubo para estatísticas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS robbery_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        robber_id TEXT,
                        victim_id TEXT,
                        amount INTEGER,
                        timestamp TEXT,
                        success INTEGER,
                        caught INTEGER
                    )
                ''')
                
                cursor.execute(
                    'INSERT INTO robbery_stats (robber_id, victim_id, amount, timestamp, success, caught) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, target_id, 0, now.strftime('%Y-%m-%d %H:%M:%S'), 0, 0)
                )
                conn.commit()
                
                # Embed de falha
                embed = discord.Embed(
                    title="💨 ROUBO FALHOU",
                    description=f"Você tentou roubar {usuario.mention}, mas falhou! Felizmente, você conseguiu fugir sem ser pego pela polícia.",
                    color=discord.Color.orange()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Fechar conexão com o banco de dados
            conn.close()
            
            # Adicionar XP pelo uso do comando
            await XPGainManager.add_command_xp(user_id, username, "roubar")
            
        except Exception as e:
            logger.error(f"Erro no comando roubar: {e}")
            embed = discord.Embed(
                title="❌ ERRO NO ROUBO",
                description="Ocorreu um erro ao processar o roubo. Tente novamente mais tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Garantir que a conexão com o banco seja fechada
            try:
                conn.close()
            except:
                pass

async def setup(bot):
    await bot.add_cog(Economy(bot))