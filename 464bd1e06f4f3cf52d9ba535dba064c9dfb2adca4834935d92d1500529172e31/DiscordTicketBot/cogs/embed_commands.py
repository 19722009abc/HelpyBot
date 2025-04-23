import discord
from discord.ext import commands
from discord import app_commands
from DiscordTicketBot.utils.emoji_config import Emoji
import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
import json
import tempfile
import io
from discord import ui
from typing import List
from DiscordTicketBot.cogs.embedtemas import EMBED_TEMAS
import google.generativeai as genai
import re

sessions = {}

class EmbedEnvioDropdown(discord.ui.Select):
    def __init__(self, embeds, session_id):
        options = [
            discord.SelectOption(
                label=f"Embed {i+1}",
                description=truncate(f"Título: {embed.title or 'Sem título'} | Descrição: {embed.description or 'Sem descrição'}"),
                value=str(i)
            )
            for i, embed in enumerate(embeds)
        ]
        if len(embeds) > 1:
            options.insert(0, discord.SelectOption(label="Todas as embeds", value="todas"))
        super().__init__(placeholder="Escolha qual embed enviar", options=options, min_values=1, max_values=1)
        self.embeds = embeds
        self.session_id = session_id
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "todas":
            await interaction.response.edit_message(view=EnviarView(self.embeds, self.session_id, todas=True), embeds=self.embeds)
        else:
            index = int(self.values[0])
            await interaction.response.edit_message(view=EnviarView([self.embeds[index]], self.session_id, todas=False), embeds=self.embeds)

class EnviarView(discord.ui.View):
    def __init__(self, embeds, session_id, todas):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.session_id = session_id
        self.todas = todas

    @discord.ui.button(label="Enviar aqui", style=discord.ButtonStyle.gray, emoji=Emoji.SEND)
    async def enviar_aqui(self, interaction: discord.Interaction, button: discord.ui.Button):
        for embed in self.embeds:
            await interaction.channel.send(embed=embed)
        await interaction.response.send_message("As embeds foram enviadas com sucesso", ephemeral=True)

    @discord.ui.button(label="Canal (em breve)", style=discord.ButtonStyle.gray, emoji="<a:SH_Loading_Discord:1362255499864838336>", row=2, disabled=True)
    async def selecionar_canal(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot = interaction.client
        await interaction.response.edit_message(content="Selecione o canal para enviar as embeds:", view=SelecionarCanalView(self.embeds, self.session_id, self.todas, bot))

    @discord.ui.button(label="Webhook", style=discord.ButtonStyle.gray, emoji=Emoji.WEBHOOK)
    async def webhook(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalWebhook(self.embeds))

    @discord.ui.button(emoji=Emoji.BACK, style=discord.ButtonStyle.red, row=2)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=SelecionarEmbedParaEnvioView(self.embeds, self.session_id),
            embeds=self.embeds
        )


class SelecionarCanalView(discord.ui.View):
    def __init__(self, embeds, session_id, todas, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(CanalSelect(embeds, todas, session_id, bot))

class CanalSelect(discord.ui.ChannelSelect):
    def __init__(self, embeds, todas, session_id, bot):
        self.embeds = embeds
        self.todas = todas
        self.session_id = session_id
        super().__init__(
            placeholder="Escolha um canal para enviar",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]  
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        canal_id = self.values[0] 
        canal = self.values[0]
  

        if canal and isinstance(canal, discord.TextChannel): 
            for embed in self.embeds:
                await canal.send(embed=embed)  
            await interaction.response.edit_message(view=None, embeds=[])
        else:
            await interaction.response.send_message("O canal selecionado não é válido para envio de embeds.", ephemeral=True)


    @discord.ui.button(emoji=Emoji.BACK, style=discord.ButtonStyle.red)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Escolha uma forma de envio:",
            view=EnviarView(self.embeds, self.session_id, self.todas),
            embeds=[]
        )

def truncate(text: str, limit: int = 100):
    return text if len(text) <= limit else text[:limit - 3] + "..."




class ModalWebhook(discord.ui.Modal, title='Enviar por webhook'):
    link = discord.ui.TextInput(label='Coloque o link do webhook abaixo', placeholder='Link aqui')

    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds

    async def on_submit(self, interaction: discord.Interaction):
        webhook_url = self.link.value

        try:
            webhook = discord.Webhook.from_url(webhook_url, client=interaction.client)
            for embed in self.embeds:
                await webhook.send(embed=embed)
            
            await interaction.response.send_message("As embeds foram enviadas com sucesso pelo webhook", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Erro ao enviar as embeds: {e}", ephemeral=True)


class EmbedDropdown(discord.ui.Select):
    def __init__(self, embeds, session_id):
        options = [
            discord.SelectOption(
                label=f"Embed {i+1}",
                description=truncate(f"Título: {embed.title or 'Sem título'} | Descrição: {embed.description or 'Sem descrição'}"),
                value=str(i)
            )
            for i, embed in enumerate(embeds)
        ]

        super().__init__(placeholder="Escolha uma embed para visualizar", options=options, min_values=1, max_values=1)
        self.embeds = embeds
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        await interaction.response.edit_message(embed=self.embeds[index], view=ViewPrincipal(self.embeds, index, self.session_id))


class EditarCamposView(discord.ui.View):
    def __init__(self, embeds, index, session_id):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

        self.botao_voltar = discord.ui.Button(style=discord.ButtonStyle.red, emoji=Emoji.BACK, row=4)
        self.botao_voltar.callback = self.voltar_callback
        self.add_item(self.botao_voltar)

        self.botao_novo = discord.ui.Button(label="Novo campo", emoji=Emoji.ADD, style=discord.ButtonStyle.success, row=4)
        self.botao_novo.callback = self.novo_callback
        self.add_item(self.botao_novo)

        if embeds[index].fields:
            self.dropdown = CampoDropdown(embeds[index].fields, self)
            self.botao_editar = discord.ui.Button(label="Editar", style=discord.ButtonStyle.gray, disabled=True, emoji=Emoji.EDIT)
            self.botao_excluir = discord.ui.Button(label="Apagar", style=discord.ButtonStyle.gray, disabled=True, emoji=Emoji.DELETE)
            self.label_selecionado = discord.ui.Button(label="Nenhum campo selecionado", style=discord.ButtonStyle.gray, disabled=True)

            self.botao_editar.callback = self.editar_callback
            self.botao_excluir.callback = self.excluir_callback

            self.add_item(self.label_selecionado)
            self.add_item(self.botao_editar)
            self.add_item(self.botao_excluir)
            self.add_item(self.dropdown)

    async def novo_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalNovoCampo(self.embeds, self.index, self.session_id, self))

    async def editar_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalEditarCampo(self.embeds, self.index, self.session_id, self.dropdown.selected_index, self))

    async def excluir_callback(self, interaction: discord.Interaction):
        campo_index = self.dropdown.selected_index
        campos_atuais = self.embeds[self.index].fields
        nova_embed = self.embeds[self.index].copy()
        nova_embed.clear_fields()
        for i, campo in enumerate(campos_atuais):
            if i != campo_index:
                nova_embed.add_field(name=campo.name, value=campo.value, inline=campo.inline)
        self.embeds[self.index] = nova_embed
        sessions[self.session_id]['last_edit'] = datetime.utcnow()

        await interaction.response.edit_message(embed=nova_embed, view=EditarCamposView(self.embeds, self.index, self.session_id))

    async def voltar_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))


class CampoDropdown(discord.ui.Select):
    def __init__(self, campos, parent_view):
        options = [
            discord.SelectOption(label=campo.name[:100], value=str(i))
            for i, campo in enumerate(campos)
        ]
        super().__init__(placeholder="Escolha um campo", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view
        self.selected_index = None

    async def callback(self, interaction: discord.Interaction):
        self.selected_index = int(self.values[0])
        campo_nome = self.parent_view.embeds[self.parent_view.index].fields[self.selected_index].name
        self.parent_view.label_selecionado.label = f"{campo_nome} selecionado"
        self.parent_view.botao_editar.disabled = False
        self.parent_view.botao_excluir.disabled = False
        await interaction.response.edit_message(view=self.parent_view)


class ModalEditarCampo(discord.ui.Modal, title="Editar Campo"):
    def __init__(self, embeds, index, session_id, campo_index, parent_view):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.campo_index = campo_index
        self.parent_view = parent_view

        campo = embeds[index].fields[campo_index]

        self.nome_input = discord.ui.TextInput(label="Nome do campo", default=campo.name, style=discord.TextStyle.short)
        self.valor_input = discord.ui.TextInput(label="Valor do campo", default=campo.value, style=discord.TextStyle.paragraph)
        self.inline_input = discord.ui.TextInput(label="Inline? (Sim/Não)", default="Sim" if campo.inline else "Não", style=discord.TextStyle.short)

        self.add_item(self.nome_input)
        self.add_item(self.valor_input)
        self.add_item(self.inline_input)

    async def on_submit(self, interaction: discord.Interaction):
        inline = self.inline_input.value.strip().lower() in ['sim', 'yes']
        self.embeds[self.index].set_field_at(
            index=self.campo_index,
            name=self.nome_input.value,
            value=self.valor_input.value,
            inline=inline
        )
        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCamposView(self.embeds, self.index, self.session_id))



class ModalNovoCampo(discord.ui.Modal, title="Novo Campo"):
    def __init__(self, embeds, index, session_id, parent_view):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.parent_view = parent_view

        self.nome_input = discord.ui.TextInput(label="Nome do campo", style=discord.TextStyle.short)
        self.valor_input = discord.ui.TextInput(label="Valor do campo", style=discord.TextStyle.paragraph)
        self.inline_input = discord.ui.TextInput(label="Inline? (Sim/Não)", style=discord.TextStyle.short)

        self.add_item(self.nome_input)
        self.add_item(self.valor_input)
        self.add_item(self.inline_input)

    async def on_submit(self, interaction: discord.Interaction):
        inline = self.inline_input.value.strip().lower() in ['sim', 'yes']
        self.embeds[self.index].add_field(
            name=self.nome_input.value,
            value=self.valor_input.value,
            inline=inline
        )
        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCamposView(self.embeds, self.index, self.session_id))

class ImportJSONModal(discord.ui.Modal, title='Cole o arquivo JSON aqui.'):
    json_input = discord.ui.TextInput(label='Cole seu JSON aqui', style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        json_content = self.json_input.value.strip()
        if not json_content:
            await interaction.response.send_message('> O JSON não pode estar vazio.', ephemeral=True)
            return
        try:
            data = json.loads(json_content)
            embed = discord.Embed.from_dict(data)
            await interaction.response.edit_message(embed=embed)
            await interaction.followup.send('> JSON importado com sucesso.', ephemeral=True)
        except json.JSONDecodeError:
            await interaction.response.send_message('> JSON inválido.', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'> Ocorreu um erro: `{e}`', ephemeral=True)


class HexModal(ui.Modal, title='Digite o código hexadecimal'):
    hex_input = ui.TextInput(label='Hex', placeholder='#7289DA', max_length=7)

    def __init__(self, embeds, index, session_id):
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        hex_code = self.hex_input.value.strip().lstrip('#')
        if len(hex_code) != 6:
            await interaction.response.send_message('> Código hexadecimal inválido.', ephemeral=True)
            return
        try:
            color = discord.Color(int(hex_code, 16))
            self.embeds[self.index].color = color
            await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCorView(self.embeds, self.index, self.session_id))
        except:
            await interaction.response.send_message('> Falha ao aplicar a cor.', ephemeral=True)

class CorDropdown(ui.Select):
    def __init__(self, embeds, index, session_id):
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

        options = [
            discord.SelectOption(label='Cor hexadecimal', description='Digite um código HEX personalizado'),
            discord.SelectOption(label='Vermelho', value='#FF0000'),
            discord.SelectOption(label='Verde', value='#00FF00'),
            discord.SelectOption(label='Azul', value='#0000FF'),
            discord.SelectOption(label='Amarelo', value='#FFFF00'),
            discord.SelectOption(label='Roxo', value='#800080'),
            discord.SelectOption(label='Laranja', value='#FFA500'),
            discord.SelectOption(label='Ciano', value='#00FFFF'),
            discord.SelectOption(label='Rosa', value='#FF69B4'),
            discord.SelectOption(label='Branco', value='#FFFFFF'),
            discord.SelectOption(label='Cinza', value='#808080'),
            discord.SelectOption(label='Preto', value='#000000'),
            discord.SelectOption(label='Marrom', value='#8B4513'),
            discord.SelectOption(label='Dourado', value='#FFD700'),
        ]
        super().__init__(placeholder='Escolha uma cor ou misture várias...', min_values=1, max_values=len(options), options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if 'Cor hexadecimal' in self.values:
            await interaction.response.send_modal(HexModal(self.embeds, self.index, self.session_id))
            return

        hexes = [int(v.lstrip('#'), 16) for v in self.values if v.startswith('#')]

        if not hexes:
            await interaction.response.send_message('❌ Nenhuma cor válida selecionada.', ephemeral=True)
            return

        r = sum((c >> 16) & 0xFF for c in hexes) // len(hexes)
        g = sum((c >> 8) & 0xFF for c in hexes) // len(hexes)
        b = sum(c & 0xFF for c in hexes) // len(hexes)

        color = discord.Color.from_rgb(r, g, b)
        self.embeds[self.index].color = color

        await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCorView(self.embeds, self.index, self.session_id))

class EditarCorView(ui.View):
    def __init__(self, embeds, index, session_id):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

        self.add_item(CorDropdown(embeds, index, session_id))
        row_botoes = BotoesSecundarios(embeds, index, session_id)
        for btn in row_botoes.children:
            self.add_item(btn)

class BotoesSecundarios(ui.View):
    def __init__(self, embeds, index, session_id):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label='Encontrar cores', style=discord.ButtonStyle.link, url='https://colorhunt.co/', row=1))
        self.add_item(VoltarButton(embeds, index, session_id))

class VoltarButton(ui.Button):
    def __init__(self, embeds, index, session_id):
        super().__init__(emoji=Emoji.BACK, style=discord.ButtonStyle.gray, row=1)
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))


class AutorUserSelect(discord.ui.UserSelect):
    def __init__(self, embeds, index, session_id):
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

        super().__init__(placeholder='Escolha um usuário para ser o autor da embed...', min_values=1, max_values=1, row=0)

    async def callback(self, interaction: discord.Interaction):
        user = self.values[0]
        self.embeds[self.index].set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else None)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=AutorView(self.embeds, self.index, self.session_id))


class VoltarButtonAutor(ui.Button):
    def __init__(self, embeds, index, session_id):
        super().__init__(emoji=Emoji.BACK, style=discord.ButtonStyle.gray, row=1)
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))



genai.configure(api_key="AIzaSyCv3TjOZfLvuylSnl5oa8GaDXWNnXNIn8g")
model = genai.GenerativeModel(
    'models/gemini-1.5-flash-001',
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)


class EmbedComIa(discord.ui.Modal):
    def __init__(self, embeds, index, session_id):
        super().__init__(title='Gerar embed com IA')
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

    tema = discord.ui.TextInput(
        label='Digite o tema da embed',
        placeholder='Ex: Regras do servidor, Dicas úteis',
        style=discord.TextStyle.paragraph
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == interaction.user

    async def on_submit(self, interaction: discord.Interaction):
        tema_text = self.tema.value
        await interaction.response.defer()
        await interaction.followup.send(content="A embed está sendo gerada, por favor, aguarde...", ephemeral=True)
        prompt = f"Crie apenas uma descrição para uma embed no Discord. Não coloque o tema no titulo, crie um titulo para a embed. Não destaque o tema. Não use formatação como negrito, emojis, markdown ou quebras de linha desnecessárias. Seja direto, crie embeds avançadas e fantasticas, com linguagem simples e objetiva. Tema '{tema_text}'."

        response = model.generate_content(prompt)
        generated_text = response.text
        generated_text = re.sub(r'\b(?:embed|cor):', '', generated_text, flags=re.IGNORECASE).strip()
        embed = discord.Embed(
            description=generated_text
        )
        self.embeds[self.index] = embed
        await interaction.edit_original_response(
            embed=embed,
            view=ViewPrincipal(self.embeds, self.index, self.session_id)
        )




class AutorView(ui.View):
    def __init__(self, embeds, index, session_id):
        super().__init__(timeout=None)
        self.add_item(AutorUserSelect(embeds, index, session_id))
        self.add_item(VoltarButtonAutor(embeds, index, session_id))

class ViewPrincipal(discord.ui.View):
    def __init__(self, embeds, index, session_id):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.index = index
        self.session_id = session_id

    @discord.ui.button(label='Titulo', emoji=Emoji.EDIT, style=discord.ButtonStyle.gray)
    async def titulo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalTitulo(self.embeds, self.index, self.session_id))

    @discord.ui.button(label='Descrição',emoji=Emoji.TEXT, style=discord.ButtonStyle.gray)
    async def descricao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalDescricao(self.embeds, self.index, self.session_id))



    @discord.ui.button(label='Cor',emoji=Emoji.COLOR, style=discord.ButtonStyle.gray)
    async def cor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCorView(self.embeds, self.index, self.session_id))

    @discord.ui.button(label='Importar Json',emoji=Emoji.IMPORT, style=discord.ButtonStyle.gray)
    async def importjson(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ImportJSONModal())


    @discord.ui.button(label='Imagem & Thumbnail',emoji=Emoji.FRAME, style=discord.ButtonStyle.gray, row=2)
    async def imagem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalImagemThumbnail(self.embeds, self.index, self.session_id))

    @discord.ui.button(label='Editar campos', emoji=Emoji.CAMPOS, style=discord.ButtonStyle.gray, row=2)
    async def campos(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        novo_campo = discord.ui.Button(label="Novo campo", emoji=Emoji.ADD)
        novo_campo.callback = lambda i: i.response.send_modal(ModalNovoCampo(self.embeds, self.index, self.session_id))
        view.add_item(novo_campo)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=EditarCamposView(self.embeds, self.index, self.session_id))

    @discord.ui.button(label='Exportar Json', emoji=Emoji.EXPORT, style=discord.ButtonStyle.gray, row=2)
    async def exportarjson(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.message.embeds:
            await interaction.response.send_message("> Nenhuma embed para exportar.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed_para_exportar = embed.to_dict()
        if embed.description:
            embed_para_exportar['description'] = embed.description
        embed_json_content = json.dumps(embed_para_exportar, ensure_ascii=False, indent=4)

        if len(embed_json_content) > 1900:
            file = discord.File(io.BytesIO(embed_json_content.encode()), filename="embed_exportada.json")
            await interaction.response.send_message(content="> **Aqui está a exportação da embed como arquivo:**", file=file, ephemeral=True)
        else:
            formatted_content = f"```json\n{embed_json_content}\n```"
            await interaction.response.send_message(content=f"> **Aqui está a exportação da embed:**\n{formatted_content}", ephemeral=True)

    @discord.ui.button(label='Autor',emoji=Emoji.USER, style=discord.ButtonStyle.gray, row=4)
    async def autor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=AutorView(self.embeds, self.index, self.session_id))

    @discord.ui.button(label='Rodapé',emoji=Emoji.FLAG, style=discord.ButtonStyle.gray, row=4)
    async def rodape(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalRodape(self.embeds, self.index, self.session_id))

    @discord.ui.button(emoji=Emoji.IA, row=4)
    async def ia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedComIa(self.embeds, self.index, self.session_id))

    

    @discord.ui.button(style=discord.ButtonStyle.red, emoji=Emoji.BACK, row=4)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EmbedView(self.embeds, self.session_id)
        await interaction.response.edit_message(view=view, embeds=self.embeds)


class ModalTitulo(discord.ui.Modal, title="Editar Título"):
    def __init__(self, embeds, index, session_id):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.titulo_input = discord.ui.TextInput(label="Novo título", default=embeds[index].title or "", style=discord.TextStyle.short)
        self.add_item(self.titulo_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.embeds[self.index].title = self.titulo_input.value
        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))

class ModalDescricao(discord.ui.Modal, title="Editar Descrição"):
    def __init__(self, embeds, index, session_id):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.desc_input = discord.ui.TextInput(label="Nova descrição", default=embeds[index].description or "", style=discord.TextStyle.paragraph)
        self.add_item(self.desc_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.embeds[self.index].description = self.desc_input.value
        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))

class ModalRodape(discord.ui.Modal, title="Editar Rodapé"):
    def __init__(self, embeds, index, session_id):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.footer_input = discord.ui.TextInput(label="Novo rodapé", default=embeds[index].footer.text if embeds[index].footer else "", style=discord.TextStyle.short)
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.embeds[self.index].set_footer(text=self.footer_input.value)
        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=ViewPrincipal(self.embeds, self.index, self.session_id))


class ModalImagemThumbnail(discord.ui.Modal, title="Editar Imagem e Thumbnail"):
    def __init__(self, embeds, index, session_id):
        super().__init__()
        self.embeds = embeds
        self.index = index
        self.session_id = session_id
        self.image_input = discord.ui.TextInput(
            label="URL da imagem", 
            default=embeds[index].image.url if embeds[index].image else "", 
            style=discord.TextStyle.short,
            required=False
        )
        self.thumb_input = discord.ui.TextInput(
            label="URL do thumbnail", 
            default=embeds[index].thumbnail.url if embeds[index].thumbnail else "", 
            style=discord.TextStyle.short,
            required=False
        )
        self.add_item(self.image_input)
        self.add_item(self.thumb_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.image_input.value:
            self.embeds[self.index].set_image(url=self.image_input.value)
        if self.thumb_input.value:
            self.embeds[self.index].set_thumbnail(url=self.thumb_input.value)

        sessions[self.session_id]['last_edit'] = datetime.utcnow()

        await interaction.response.edit_message(
            embed=self.embeds[self.index], 
            view=ViewPrincipal(self.embeds, self.index, self.session_id)
        )



class ExcluirEmbedDropdown(discord.ui.Select):
    def __init__(self, embeds, session_id):
        options = [
            discord.SelectOption(
                label=f"Embed {i+1}",
                description=truncate(f"Título: {embed.title or 'Sem título'} | Descrição: {embed.description or 'Sem descrição'}"),
                value=str(i)
            )
            for i, embed in enumerate(embeds)
        ]

        if len(embeds) > 1:
            options.insert(0, discord.SelectOption(label="Todas as embeds", value="todas"))

        super().__init__(placeholder="Escolha a embed para excluir", options=options)
        self.embeds = embeds
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "todas":
            self.embeds.clear()
        else:
            index = int(self.values[0])
            del self.embeds[index]

        sessions[self.session_id]['last_edit'] = datetime.utcnow()
        if not self.embeds:
            self.embeds.append(discord.Embed(title="Personaliza o titulo", description="Este é um modelo inicial. Use os botões para personalizar.", color=discord.Color.dark_embed()))

        await interaction.response.edit_message(
            view=EmbedView(self.embeds, self.session_id),
            embeds=self.embeds
        )


class ExcluirEmbedView(discord.ui.View):
    def __init__(self, embeds, session_id):
        super().__init__(timeout=None)
        self.add_item(ExcluirEmbedDropdown(embeds, session_id))
        self.embeds = embeds
        self.session_id = session_id

    @discord.ui.button(emoji=Emoji.BACK, style=discord.ButtonStyle.secondary, row=2)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=EmbedView(self.embeds, self.session_id),
            embeds=self.embeds
            )


class SelecionarEmbedParaEnvioView(discord.ui.View):
    def __init__(self, embeds, session_id):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.session_id = session_id
        self.add_item(EmbedEnvioDropdown(embeds, session_id))

    @discord.ui.button(emoji=Emoji.BACK, style=discord.ButtonStyle.secondary, row=2)
    async def voltar3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=EmbedView(self.embeds, self.session_id),
            embeds=self.embeds
        )










class TemaDropdown(discord.ui.Select):
    def __init__(self, index):
        options = [
            discord.SelectOption(label=f"Tema {index + 1}", description=f"Tema {index + 1}", value=str(index))
        ]
        super().__init__(placeholder="Visualizando tema...", options=options, disabled=True, row=0)

class NavegarTemasView(discord.ui.View):
    def __init__(self, original_embeds, current_index, session_id):
        super().__init__(timeout=None)
        self.original_embeds = original_embeds  
        self.index = current_index
        self.session_id = session_id
        self.temas = EMBED_TEMAS  
        self.add_item(TemaDropdown(self.index))
        self.add_item(VoltarTemaButton(self.original_embeds, self.session_id))
        self.add_item(SetaEsquerdaButton(self))
        self.add_item(SetaDireitaButton(self))

    async def atualizar_view(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(TemaDropdown(self.index))
        self.add_item(VoltarTemaButton(self.original_embeds, self.session_id))
        self.add_item(SetaEsquerdaButton(self))
        self.add_item(SetaDireitaButton(self))
        await interaction.response.edit_message(embed=self.temas[self.index], view=self)


class SetaEsquerdaButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(emoji='<:leftarrow:1362213437417066677>', style=discord.ButtonStyle.gray)
        self.viewref = view

    async def callback(self, interaction: discord.Interaction):
        self.viewref.index = (self.viewref.index - 1) % len(self.viewref.temas)
        await self.viewref.atualizar_view(interaction)


class SetaDireitaButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(emoji='<:rightarrow:1362213443251474522>', style=discord.ButtonStyle.gray)
        self.viewref = view

    async def callback(self, interaction: discord.Interaction):
        self.viewref.index = (self.viewref.index + 1) % len(self.viewref.temas)
        await self.viewref.atualizar_view(interaction)



class VoltarTemaButton(discord.ui.Button):
    def __init__(self, embeds, session_id):
        super().__init__(emoji=Emoji.BACK, style=discord.ButtonStyle.gray, row=2)
        self.embeds = embeds
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=EmbedEscolhaDropdown(self.embeds, self.session_id))

class EmbedEscolhaDropdown(discord.ui.View):
    def __init__(self, embeds, session_id):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.session_id = session_id
        self.add_item(SelecionarEmbedTema(self.embeds, self.session_id))
        self.add_item(VoltarButtonTemas(self.embeds, self.session_id))

class VoltarButtonTemas(discord.ui.Button):
    def __init__(self, embeds, session_id):
        super().__init__(emoji=Emoji.BACK, style=discord.ButtonStyle.gray, row=2)
        self.embeds = embeds
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        view = EmbedView(self.embeds, self.session_id)
        await interaction.response.edit_message(view=view)


class SelecionarEmbedTema(discord.ui.Select):
    def __init__(self, embeds, session_id):
        options = [
            discord.SelectOption(
                label=f"Embed {i + 1}",
                description=f"Título: {embed.title or 'Sem título'} | Desc: {embed.description or 'Sem desc'}",
                value=str(i)
            ) for i, embed in enumerate(embeds)
        ]
        super().__init__(placeholder="Escolha uma embed para aplicar um tema", options=options)
        self.embeds = embeds
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        await interaction.response.edit_message(embed=self.embeds[index], view=NavegarTemasView(self.embeds, index, self.session_id))

class EmbedView(discord.ui.View):
    def __init__(self, embeds=None, session_id=None, index=0):  
        super().__init__(timeout=None)
        self.embeds = embeds or [self.create_embed(1)]
        self.session_id = session_id or str(uuid.uuid4())
        sessions[self.session_id] = {'embeds': self.embeds, 'last_edit': datetime.utcnow()}
        self.dropdown = EmbedDropdown(self.embeds, self.session_id)
        self.add_item(self.dropdown)
        self.add_embed_button()
        self.add_enviar_button()
        self.add_excluir_button()
       


        asyncio.create_task(self.expire_session())

    def create_embed(self, number):
        return discord.Embed(title=f"Titulo", description=f"Descrição", color=discord.Color.random())

    def add_embed_button(self):
        button = discord.ui.Button(label="Adicionar Embed", emoji=Emoji.ADD, style=discord.ButtonStyle.gray)

        async def callback(interaction: discord.Interaction):
            if len(self.embeds) >= 10:
                await interaction.response.send_message("Você atingiu o limite de 10 embeds!", ephemeral=True)
                return
            new_embed = self.create_embed(len(self.embeds) + 1)
            self.embeds.append(new_embed)
            sessions[self.session_id]['last_edit'] = datetime.utcnow()
            self.clear_items()
            self.dropdown = EmbedDropdown(self.embeds, self.session_id)
            self.add_item(self.dropdown)
            self.add_embed_button()
            self.add_enviar_button()
            self.add_excluir_button()
            
          
            await interaction.response.edit_message(view=self, embeds=self.embeds)

        button.callback = callback
        self.add_item(button)


    def add_enviar_button(self):
        button = discord.ui.Button(emoji=Emoji.SEND, style=discord.ButtonStyle.gray)

        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                view=SelecionarEmbedParaEnvioView(self.embeds, self.session_id),
                embeds=self.embeds
            )

        button.callback = callback
        self.add_item(button)

    def add_excluir_button(self):
        button = discord.ui.Button(emoji=Emoji.DELETE, style=discord.ButtonStyle.gray)

        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                view=ExcluirEmbedView(self.embeds, self.session_id),
                embeds=self.embeds
            )

        button.callback = callback
        self.add_item(button)


    def add_tema_button(self):
        button = discord.ui.Button(label='Temas', emoji=Emoji.COLOR, style=discord.ButtonStyle.gray)

        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                embed=self.embeds[0],
                view=EmbedEscolhaDropdown(self.embeds, self.session_id)
            )

        button.callback = callback
        self.add_item(button)



    async def expire_session(self):
        while True:
            await asyncio.sleep(60)
            if datetime.utcnow() - sessions[self.session_id]['last_edit'] > timedelta(minutes=20):
                sessions.pop(self.session_id, None)
                await self.message.edit(content="⏰ Sessão expirada! As embeds foram apagadas.", embed=None, view=None)
                break




from PIL import Image, ImageDraw, ImageFont, ImageFilter
import discord
from discord.ext import commands
from discord import app_commands
import io
import sqlite3
import asyncio
import random

def init_db():
    with sqlite3.connect("updates.db") as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS updates (
            user_id INTEGER PRIMARY KEY,
            updated BOOLEAN DEFAULT 0
        )""")
        con.commit()

def has_updated(user_id: int):
    with sqlite3.connect("updates.db") as con:
        cur = con.cursor()
        cur.execute("SELECT updated FROM updates WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        return result is not None and result[0] == 1

def set_updated(user_id: int):
    with sqlite3.connect("updates.db") as con:
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO updates (user_id, updated) VALUES (?, 1)", (user_id,))
        con.commit()

class AtualizarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.text_dots = 0

    @discord.ui.button(label="Atualizar", style=discord.ButtonStyle.blurple)
    async def atualizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        porcentagem = 0
        cor = (0, 122, 255)
        msg = await interaction.edit_original_response(attachments=[self.gerar_imagem(porcentagem, cor)], embed=None, view=None)
        tempo_total = random.uniform(23, 30)
        inicio = discord.utils.utcnow().timestamp()
        while porcentagem < 100:
            agora = discord.utils.utcnow().timestamp()
            tempo_passado = agora - inicio
            porcentagem = int((tempo_passado / tempo_total) * 100)
            porcentagem = min(porcentagem, 100)
            if porcentagem > 70:
                cor = (255, 213, 0)
            self.text_dots = (self.text_dots + 1) % 4
            await msg.edit(attachments=[self.gerar_imagem(porcentagem, cor)])
            await asyncio.sleep(random.uniform(1.5, 2.5))

        cor = (50, 205, 50)
        set_updated(interaction.user.id)
        await msg.edit(content=None, attachments=[self.gerar_imagem(100, cor, finalizada=True)])
        view = EmbedView()
        follow = await interaction.followup.send(view=view, embeds=view.embeds, ephemeral=True)
        view.message = follow

    def gerar_imagem(self, porcentagem, cor, finalizada=False):
        img = Image.new("RGBA", (300, 80), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        borda_ext = Image.new("RGBA", (300, 80), (255, 255, 255, 0))
        draw_ext = ImageDraw.Draw(borda_ext)
        draw_ext.rounded_rectangle((10, 20, 290, 55), 14, fill=(255, 255, 255, 255))
        glow = borda_ext.filter(ImageFilter.GaussianBlur(4))
        img.paste(glow, (0, 0), glow)

        draw.rounded_rectangle((15, 25, 285, 50), 10, fill=(40, 40, 40, 255))
        draw.rounded_rectangle((15, 25, 15 + (270 * porcentagem // 100), 50), 10, fill=cor)

        try:
            fonte = ImageFont.truetype("arial.ttf", 16)
        except:
            fonte = ImageFont.load_default()

        if finalizada:
            texto = "✅ Atualizado com sucesso!"
        else:
            pontos = "." * self.text_dots
            texto = f"Atualizando: {porcentagem}%{pontos}"

        draw.text((80, 55), texto, fill=(255, 255, 255), font=fonte)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="atualizando.png")

from DiscordTicketBot.utils.database_sqlite import UserService

class EmbedComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    @app_commands.command(name="embed-criar", description="Abra um criador de embeds avançado")
    async def embed(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Permissão Negada",
                description="> Você precisa ter a permissão de **Administrador** para usar esse comando.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Verifica se o usuário é premium
        user = UserService.ensure_user_exists(interaction.user.id, interaction.user.name)
        if not user or not user[3]:  # Índice 3 = is_premium
            embed = discord.Embed(
                title="Acesso Restrito",
                description="> Este recurso está disponível apenas para usuários **Premium**.\nAdquira o Premium na loja para desbloquear!",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            embed.set_footer(text="Exclusivo para usuários Premium")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if not has_updated(interaction.user.id):
            embed = discord.Embed(
                title="Comando Desatualizado",
                description="> Esse comando foi atualizado recentemente e precisa de uma rápida sincronização antes de continuar.\n\nClique no botão abaixo para iniciar a atualização.",
                color=discord.Color.from_rgb(30, 30, 30)
            )
            embed.set_footer(text="Atualização obrigatória • Leva menos de 2 minutos")
            await interaction.followup.send(embed=embed, view=AtualizarView(), ephemeral=True)
            return

        view = EmbedView()
        msg = await interaction.followup.send(view=view, embeds=view.embeds, ephemeral=True)
        view.message = msg

async def setup(bot):
    await bot.add_cog(EmbedComandos(bot))
