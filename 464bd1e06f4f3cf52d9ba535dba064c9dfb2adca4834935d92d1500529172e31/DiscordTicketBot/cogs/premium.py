import discord
from discord import app_commands
from discord.ext import commands
import logging
import datetime
import random

from utils.database_sqlite import UserService
# Removido import do ImageService para evitar dependência do Pillow

# Configuração do logger
logger = logging.getLogger("CartoonBot")

class PremiumPackageView(discord.ui.View):
    """View específica para exibir os pacotes premium com imagens"""
    def __init__(self, user_coins):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.user_coins = user_coins

    @discord.ui.button(label="Bronze 🥉 (10k)", style=discord.ButtonStyle.secondary)
    async def premium_bronze(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_package_details(interaction, 15, 10000, 1)

    @discord.ui.button(label="Prata 🥈 (20k)", style=discord.ButtonStyle.primary)
    async def premium_silver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_package_details(interaction, 15, 20000, 2)

    @discord.ui.button(label="Ouro 🥇 (35k)", style=discord.ButtonStyle.success)
    async def premium_gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_package_details(interaction, 15, 35000, 3)

    async def _show_package_details(self, interaction: discord.Interaction, days, price, tier=None):
        """Exibe detalhes do pacote premium usando somente texto formatado"""
        await interaction.response.defer(ephemeral=True)

        # Verificar se o usuário tem saldo suficiente
        can_afford = self.user_coins >= price

        # Criar embed detalhado com formatação visual rica
        embed = discord.Embed(
            title=f"✨ Pacote Premium de {days} Dias",
            description=f"Aproveite todos os benefícios exclusivos por {days} dias!",
            color=discord.Color.gold()
        )

        # Criar uma representação em texto do badge premium (ASCII art estilizado)
        badge_ascii = f"```ansi\n"
        badge_ascii += f"\u001b[33;1m╔══════════════════════╗\u001b[0m\n"
        badge_ascii += f"\u001b[33;1m║  \u001b[37;1m⭐ PREMIUM BADGE ⭐\u001b[33;1m  ║\u001b[0m\n"
        badge_ascii += f"\u001b[33;1m║  \u001b[37;1m{days} DIAS DE ACESSO\u001b[33;1m  ║\u001b[0m\n"
        badge_ascii += f"\u001b[33;1m║  \u001b[37;1m✨ CERTIFICADO ✨\u001b[33;1m  ║\u001b[0m\n"
        badge_ascii += f"\u001b[33;1m╚══════════════════════╝\u001b[0m\n```"

        # Adicionar o badge texto no lugar da imagem
        embed.add_field(
            name="🏆 Seu Badge Premium",
            value=badge_ascii,
            inline=False
        )

        # Detalhes do pacote
        embed.add_field(
            name="💰 Preço",
            value=f"**{price:,} coins**" + (" ✅" if can_afford else " ❌ (Saldo insuficiente)"),
            inline=True
        )

        embed.add_field(
            name="⏱️ Duração",
            value=f"**{days} dias**",
            inline=True
        )

        # Adicionar valor diário economizado
        daily_bonus = 750  # Estimativa média de bônus diário
        total_bonus = daily_bonus * days
        embed.add_field(
            name="💎 Economia Estimada",
            value=f"**+{total_bonus:,} coins** em bônus de daily",
            inline=True
        )

        # Calcular economia para pacotes maiores (desconto)
        if days == 90:
            savings = 9000  # (3 * 18000) - 45000
            embed.add_field(
                name="🏷️ Desconto",
                value=f"**Economize {savings:,} coins** (17% de desconto)",
                inline=False
            )

        # Benefícios
        embed.add_field(
            name="✨ Benefícios Inclusos",
            value=(
                "• **+50%** de coins em recompensas diárias\n"
                "• Carteira com design exclusivo\n"
                "• Efeitos visuais únicos\n"
                "• Badge premium em seu perfil\n"
                "• Acesso antecipado a novos recursos"
            ),
            inline=False
        )

        # Botão para comprar
        view = discord.ui.View(timeout=180)

        # Botão para voltar
        view.add_item(discord.ui.Button(
            label="Voltar", style=discord.ButtonStyle.secondary, custom_id="back_to_packages"))

        # Botão para comprar (desabilitado se não tem saldo)
        buy_button = discord.ui.Button(
            label="Comprar Agora", 
            style=discord.ButtonStyle.success, 
            custom_id=f"buy_premium_{days}",
            disabled=not can_afford,
            emoji="✨"
        )
        view.add_item(buy_button)

        # Enviar mensagem com detalhes (sem arquivo de imagem)
        message = await interaction.followup.send(
            embed=embed,
            view=view, 
            ephemeral=True
        )

        # Capturar interação com os botões
        def check(i):
            return i.user.id == interaction.user.id and i.data and "custom_id" in i.data

        try:
            button_interaction = await interaction.client.wait_for("interaction", check=check, timeout=180)

            if button_interaction.data["custom_id"] == "back_to_packages":
                # Voltar para o menu principal
                await button_interaction.response.defer()
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="✨ Escolha um Pacote Premium",
                        description="Selecione um dos pacotes para ver mais detalhes:",
                        color=discord.Color.gold()
                    ),
                    view=PremiumPackageView(self.user_coins),
                    attachments=[]
                )

            elif button_interaction.data["custom_id"].startswith("buy_premium_"):
                # Processar a compra
                await button_interaction.response.send_modal(
                    ConfirmPurchaseModal(days, price, interaction.user.id)
                )

        except Exception as e:
            logger.error(f"Erro na interação com botões premium: {e}")

class ConfirmPurchaseModal(discord.ui.Modal):
    """Modal para confirmar uma compra premium"""
    def __init__(self, days, price, user_id):
        super().__init__(title=f"Confirmar Compra - {days} dias")
        self.days = days
        self.price = price
        self.user_id = user_id

        self.confirm = discord.ui.TextInput(
            label=f"Digite 'CONFIRMAR' ({price:,} coins)",
            placeholder="CONFIRMAR",
            required=True,
            max_length=10
        )
        self.add_item(self.confirm)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value.upper() != "CONFIRMAR":
            await interaction.response.send_message("❌ Compra cancelada.", ephemeral=True)
            return

        # Remover coins
        success, result = UserService.remove_coins(
            self.user_id, 
            self.price, 
            f"Compra de Premium ({self.days} dias)"
        )

        if not success:
            await interaction.response.send_message(f"❌ Erro ao processar pagamento: {result}", ephemeral=True)
            return

        # Ativar premium
        success, result = UserService.update_premium_status(self.user_id, True, self.days)

        if not success:
            # Em caso de erro, devolver os coins
            UserService.add_coins(self.user_id, self.price, "Estorno: Falha na ativação premium")
            await interaction.response.send_message(f"❌ Erro ao ativar premium: {result}", ephemeral=True)
            return

        # Verificar o formato da data de expiração
        expiry_date = None
        if isinstance(result, tuple) and len(result) > 4 and result[4]:
            # SQLite pode retornar uma string ISO
            if isinstance(result[4], str):
                try:
                    expiry_date = datetime.datetime.fromisoformat(result[4].replace('Z', '+00:00'))
                except ValueError:
                    expiry_date = datetime.datetime.now() + datetime.timedelta(days=self.days)
            else:
                expiry_date = result[4]
        else:
            # Usar data estimada se não conseguir extrair
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=self.days)

        # Criar embed de sucesso com visual cartoon
        embed = discord.Embed(
            title="✨ PREMIUM ATIVADO! ✨",
            description=f"🎉 **PARABÉNS!** 🎉\nVocê agora é um usuário premium por **{self.days} dias**!",
            color=discord.Color.gold()
        )

        # Informações da compra
        embed.add_field(name="⏱️ Duração", value=f"{self.days} dias", inline=True)
        embed.add_field(name="💰 Valor Pago", value=f"{self.price:,} coins", inline=True)

        # Formatar data de expiração
        expiry_str = expiry_date.strftime("%d/%m/%Y") if expiry_date else f"Hoje + {self.days} dias"
        embed.add_field(name="📅 Expira em", value=expiry_str, inline=True)

        # Adicionar mensagem aleatória de celebração
        celebrations = [
            "Você acabou de desbloquear todo o poder premium!",
            "Prepare-se para uma experiência VIP incrível!",
            "Seu status premium foi ativado com sucesso!",
            "Bem-vindo ao clube dos membros premium!",
            "Você agora tem acesso aos recursos exclusivos!"
        ]

        embed.add_field(
            name="🌟 BENEFÍCIOS ATIVOS",
            value=(
                f"→ {random.choice(celebrations)}\n\n"
                "• **+50%** de bônus nos daily rewards\n"
                "• Carteira com visual exclusivo premium\n"
                "• Badge premium no seu perfil\n"
                "• Acesso antecipado a novos recursos\n"
                "• Efeitos visuais exclusivos"
            ),
            inline=False
        )

        embed.set_footer(text="✨ Obrigado por apoiar o bot! ✨")

        # Criar badge premium em texto formatado em vez de imagem
        badge_text = f"```ansi\n"
        badge_text += f"\u001b[33;1m╔═══════════════════════════╗\u001b[0m\n"
        badge_text += f"\u001b[33;1m║  \u001b[37;1m🎖️ PREMIUM CONFIRMADO 🎖️\u001b[33;1m  ║\u001b[0m\n"
        badge_text += f"\u001b[33;1m║  \u001b[37;1m✨ {self.days} DIAS ATIVADOS ✨\u001b[33;1m  ║\u001b[0m\n"
        badge_text += f"\u001b[33;1m╚═══════════════════════════╝\u001b[0m\n```"

        embed.add_field(
            name="🏆 Seu Badge Premium",
            value=badge_text,
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class PremiumInfoView(discord.ui.View):
    """View com informações sobre o premium"""
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.select(
        placeholder="Selecione para mais informações...",
        options=[
            discord.SelectOption(label="Benefícios Premium", value="benefits", emoji="✨",
                                description="Descubra as vantagens exclusivas"),
            discord.SelectOption(label="Comparar Planos", value="plans", emoji="📊",
                                description="Compare os diferentes pacotes"),
            discord.SelectOption(label="Perguntas Frequentes", value="faq", emoji="❓",
                                description="Respostas para suas dúvidas")
        ]
    )
    async def premium_info_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "benefits":
            embed = discord.Embed(
                title="✨ Benefícios Premium",
                description="Descubra todas as vantagens exclusivas de ser um usuário premium:",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="🎁 Daily Rewards Turbinados",
                value="Receba **+50%** de coins em todos os seus resgates diários",
                inline=False
            )

            embed.add_field(
                name="💎 Carteira Premium",
                value="Tenha acesso a um design exclusivo de carteira com efeitos visuais especiais",
                inline=False
            )

            embed.add_field(
                name="🏆 Badge Exclusivo",
                value="Mostre a todos que você é um membro VIP com seu badge premium",
                inline=False
            )

            embed.add_field(
                name="🚀 Acesso Antecipado",
                value="Experimente os novos recursos antes de todos",
                inline=False
            )

            # Removida a referência ao thumbnail externo
            # Em vez disso, adicionamos um texto formatado que se parece com um badge
            badge_text = f"```ansi\n"
            badge_text += f"\u001b[33;1m★\u001b[0m\u001b[37;1m PREMIUM VIP \u001b[33;1m★\u001b[0m\n"
            badge_text += f"```"

            embed.add_field(
                name="🎖️ Seu Badge Exclusivo",
                value=badge_text,
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif select.values[0] == "plans":
            embed = discord.Embed(
                title="📊 Comparação de Planos Premium",
                description="Escolha o plano que melhor se adapta às suas necessidades:",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="🥉 Pacote Bronze",
                value="• **15 dias** de premium\n• **10,000 coins**\n• ~**11,250 coins** de bônus daily\n• Ideal para testar os recursos",
                inline=True
            )

            embed.add_field(
                name="🥈 Pacote Prata",
                value="• **30 dias** de premium\n• **18,000 coins**\n• ~**22,500 coins** de bônus daily\n• Melhor custo-benefício",
                inline=True
            )

            embed.add_field(
                name="🥇 Pacote Ouro",
                value="• **90 dias** de premium\n• **45,000 coins (17% de desconto)**\n• ~**67,500 coins** de bônus daily\n• Maior economia a longo prazo",
                inline=True
            )

            embed.set_footer(text="Bônus daily estimados baseados em uso diário")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif select.values[0] == "faq":
            embed = discord.Embed(
                title="❓ Perguntas Frequentes sobre Premium",
                description="Respostas para as dúvidas mais comuns:",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="O que acontece quando meu premium expira?",
                value="Você mantém todas as suas coins e itens, mas perde os benefícios premium como o bônus de 50% nos dailies.",
                inline=False
            )

            embed.add_field(
                name="Posso transferir meu status premium?",
                value="Não, o status premium é vinculado à sua conta e não pode ser transferido para outros usuários.",
                inline=False
            )

            embed.add_field(
                name="Como renovo meu premium?",
                value="Basta comprar um novo pacote antes do seu atual expirar. O período será adicionado ao seu tempo restante.",
                inline=False
            )

            embed.add_field(
                name="Posso obter reembolso?",
                value="Não oferecemos reembolsos para compras premium, todas as compras são finais.",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

class PremiumMainView(discord.ui.View):
    """View principal do sistema premium com múltiplos botões de ação"""
    def __init__(self, user, is_premium, premium_until):
        super().__init__(timeout=300)
        self.user = user
        self.is_premium = is_premium
        self.premium_until = premium_until

    @discord.ui.button(label="Ver Pacotes Premium", style=discord.ButtonStyle.primary, emoji="🛒", row=0)
    async def view_packages(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Exibe os pacotes premium disponíveis"""
        embed = discord.Embed(
            title="✨ Escolha um Pacote Premium",
            description="Selecione um dos pacotes para ver mais detalhes:",
            color=discord.Color.gold()
        )

        if self.is_premium and self.premium_until:
            days_left = (self.premium_until - datetime.datetime.now()).days
            embed.set_footer(text=f"Você já possui premium ativo: {days_left} dias restantes")

        await interaction.response.send_message(
            embed=embed, 
            view=PremiumPackageView(self.user[2]),
            ephemeral=True
        )

    @discord.ui.button(label="Informações Premium", style=discord.ButtonStyle.secondary, emoji="ℹ️", row=0)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Exibe o menu de informações premium"""
        embed = discord.Embed(
            title="ℹ️ Informações Premium",
            description="Selecione uma opção abaixo para saber mais sobre o sistema premium:",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PremiumInfoView(),
            ephemeral=True
        )

    @discord.ui.button(label="Verificar Status", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def check_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Verifica o status premium atual do usuário"""

        if not self.is_premium:
            embed = discord.Embed(
                title="📊 Status Premium",
                description="Você não possui um plano premium ativo no momento.",
                color=discord.Color.light_grey()
            )
            embed.add_field(
                name="💰 Seu Saldo",
                value=f"{self.user[2]:,} coins",
                inline=False
            )
            embed.add_field(
                name="Plano Recomendado",
                value="Com seu saldo atual, recomendamos o seguinte plano:",
                inline=False
            )

            # Recomendar o melhor plano de acordo com o saldo
            if self.user[2] >= 45000:
                plan = "🥇 **Pacote Ouro** (90 dias)"
            elif self.user[2] >= 18000:
                plan = "🥈 **Pacote Prata** (30 dias)"
            elif self.user[2] >= 10000:
                plan = "🥉 **Pacote Bronze** (15 dias)"
            else:
                plan = "❌ Saldo insuficiente para qualquer plano"

            embed.add_field(
                name="Recomendação",
                value=plan,
                inline=False
            )

        else:
            days_left = (self.premium_until - datetime.datetime.now()).days
            embed = discord.Embed(
                title="📊 Status Premium",
                description="Seu plano premium está **ATIVO**! ✨",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="⏱️ Tempo Restante",
                value=f"**{days_left} dias** (Expira em {self.premium_until.strftime('%d/%m/%Y')})",
                inline=False
            )
            embed.add_field(
                name="💰 Seu Saldo",
                value=f"{self.user[2]:,} coins",
                inline=False
            )

            # Sugerir extensão
            embed.add_field(
                name="Lembrete",
                value="Você pode estender seu plano a qualquer momento comprando outro pacote.",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Como Funciona", style=discord.ButtonStyle.secondary, emoji="❓", row=1)
    async def how_it_works(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Exibe informações sobre como funciona o sistema premium"""
        embed = discord.Embed(
            title="❓ Como Funciona o Premium",
            description="Tudo o que você precisa saber sobre o sistema premium:",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="1️⃣ Escolha um Pacote",
            value="Selecione o pacote premium que melhor se adapta às suas necessidades: 15, 30 ou 90 dias.",
            inline=False
        )

        embed.add_field(
            name="2️⃣ Faça o Pagamento",
            value="O pagamento é feito com as coins que você acumulou. Use `/daily` diariamente para acumular mais.",
            inline=False
        )

        embed.add_field(
            name="3️⃣ Aproveite os Benefícios",
            value="Após a compra, todos os benefícios são ativados automaticamente em sua conta.",
            inline=False
        )

        embed.add_field(
            name="4️⃣ Renovação",
            value="Seu status premium expira após o período contratado. Você pode renovar a qualquer momento.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="premium", description="Acesse o sistema premium e seus benefícios exclusivos")
    async def premium(self, interaction: discord.Interaction):
        # Usar ephemeral=True para mensagens privadas
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        username = interaction.user.name

        # Verificar se o usuário existe no banco
        user = UserService.ensure_user_exists(user_id, username)

        if not user:
            await interaction.followup.send("❌ Ocorreu um erro ao acessar seus dados. Tente novamente.", ephemeral=True)
            return

        # Verificar se já é premium
        is_premium = user[3]
        premium_until = user[4]

        # Criar embed com visual cartoon mais atrativo
        embed = discord.Embed(
            title="✨ SISTEMA PREMIUM ✨",
            description=(
                "🌟 **Torne-se um usuário PREMIUM e desbloqueie benefícios exclusivos!** 🌟\n\n"
                "Escolha uma das opções abaixo para começar:"
            ),
            color=discord.Color.gold()
        )

        # Exibir status atual com destaque
        if is_premium and premium_until:
            if isinstance(premium_until, str):
                premium_until = datetime.datetime.fromisoformat(premium_until)  # ou use strptime se for outro formato

            days_left = (premium_until - datetime.datetime.now()).days
            embed.add_field(
                name="🏆 STATUS PREMIUM ATIVO!",
                value=(
                    f"✅ **Você já é um usuário VIP!**\n"
                    f"⏱️ Expira em: **{premium_until.strftime('%d/%m/%Y')}**\n"
                    f"📊 Dias restantes: **{days_left}**"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="📢 OFERTA ESPECIAL!",
                value=(
                    "✨ **Compre agora e ganhe acesso a recursos exclusivos!** ✨\n"
                    "• Bônus de **50%** em todos os daily rewards\n"
                    "• Visual exclusivo para sua carteira\n"
                    "• E muito mais!"
                ),
                inline=False
            )

        # Exibir saldo atual
        embed.add_field(
            name="💰 Seu Saldo Atual",
            value=f"**{user[2]:,} coins**",
            inline=False
        )

        # Criar view com botões interativos
        view = PremiumMainView(user, is_premium, premium_until)

        # Enviar resposta
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Premium(bot))