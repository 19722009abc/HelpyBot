from discord import Embed, Color

EMBED_TEMAS = [
    Embed(
        title="📜 **Regras do Servidor**",
        description="**Bem-vindo ao nosso servidor!**\nAqui você encontrará todas as regras importantes para garantir um ambiente saudável e respeitoso para todos os membros. 🛑\n\n🔹 **Respeite os outros membros:** Trate todos com educação e respeito. Não serão tolerados comportamentos ofensivos.\n\n🔸 **Evite spam e flood:** Não envie mensagens repetitivas ou fora de contexto.\n\n⚠️ **Punições:** O descumprimento das regras pode resultar em advertências ou banimento.",
        color=Color.blue()
    ),
    Embed(
        title="📝 **Termos de Serviço**",
        description="**Leia atentamente nossos Termos de Serviço antes de usar o servidor.**📚\n\n🔸 **Responsabilidade:** Ao participar, você concorda em respeitar todos os termos estabelecidos, incluindo nossas políticas de privacidade.\n\n🔹 **Uso adequado:** O servidor deve ser usado para fins de diversão e interação social. Qualquer uso inadequado será punido.\n\n🔑 **Direitos de autor:** Respeite a propriedade intelectual dos outros, não compartilhe conteúdo protegido sem a permissão adequada.",
        color=Color.dark_grey()
    ),
    Embed(
        title="🎮 **Guia do Usuário**",
        description="**Tudo o que você precisa saber para aproveitar ao máximo o servidor!**\n\n🗺️ **Exploração do servidor:** Familiarize-se com os canais e categorias disponíveis. Cada um tem um propósito específico para tornar sua experiência mais agradável.\n\n🔍 **Dúvidas e Ajuda:** Se precisar de ajuda, procure os canais de suporte ou entre em contato com um moderador.\n\n✨ **Dicas:** Não se esqueça de configurar suas notificações para receber alertas importantes!",
        color=Color.green()
    ),
    Embed(
        title="⚠️ **Política de Privacidade**",
        description="**Sua privacidade é nossa prioridade!**🔒\n\n🔹 **Coleta de dados:** O servidor coleta apenas informações essenciais para garantir uma experiência personalizada.\n\n🔸 **Segurança:** Implementamos medidas rigorosas para proteger seus dados contra acessos não autorizados.\n\n💡 **Consentimento:** Ao participar, você concorda com nossa política de privacidade e o uso de seus dados conforme descrito.",
        color=Color.purple()
    ),
    Embed(
        title="🎉 **Eventos e Promoções**",
        description="**Participe de nossos eventos e promoções exclusivas!**\n\n🔥 **Eventos:** Fique de olho em nossos eventos especiais que acontecem regularmente. Prêmios incríveis aguardam os vencedores!\n\n🎁 **Promoções:** Não perca nossas promoções e sorteios! Participe e tenha a chance de ganhar prêmios exclusivos.\n\n🗓️ **Calendário:** Confira o calendário de eventos no canal #eventos para não perder nenhuma oportunidade!",
        color=Color.gold()
    ),
    Embed(
        title="💬 **Comandos e Funcionalidades**",
        description="**Conheça os comandos e funcionalidades do servidor!**\n\n🔹 **Comandos básicos:** Utilize os comandos para interagir com o servidor, acessar funções exclusivas e personalizar sua experiência.\n\n🔸 **Funções especiais:** Verifique as funções exclusivas que você pode obter através de interação com o bot ou ganhando níveis.\n\n⚙️ **Personalização:** Customize sua experiência de acordo com suas preferências, como definir seu prefixo e configurar alertas.",
        color=Color.dark_blue()
    ),
    Embed(
        title="💡 **Sugestões e Feedback**",
        description="**Sua opinião é importante para nós!**\n\n🔹 **Como enviar sugestões:** Para sugerir melhorias ou novos recursos, use o canal #sugestoes.\n\n🔸 **Feedback:** Adoramos ouvir o que você acha do servidor. Se tiver algo a compartilhar, sinta-se à vontade para nos enviar um feedback!\n\n📈 **Atenção:** As sugestões mais votadas podem ser implementadas em atualizações futuras!",
        color=Color.orange()
    ),
    Embed(
        title="🛠️ **Suporte Técnico**",
        description="**Estamos aqui para ajudar com qualquer problema técnico!**\n\n🔹 **Problemas comuns:** Se você está enfrentando dificuldades para acessar o servidor ou utilizar os recursos, consulte nossa FAQ no canal #faq.\n\n🔸 **Contato com moderadores:** Caso precise de ajuda personalizada, entre em contato com um moderador diretamente no canal #suporte.\n\n🖥️ **Desempenho do servidor:** Se houver problemas de desempenho, notificaremos todos os membros através de anúncios.",
        color=Color.red()
    ),
    Embed(
        title="📚 **Biblioteca de Recursos**",
        description="**Acesse nossa biblioteca com materiais exclusivos!**\n\n📖 **Guias e tutoriais:** Aprenda novas habilidades e melhore sua experiência no servidor com nossos tutoriais detalhados.\n\n🔑 **Recursos exclusivos:** Sócios premium têm acesso a recursos adicionais e conteúdo exclusivo, incluindo guias avançados e ferramentas personalizadas.\n\n💻 **Apoio contínuo:** A biblioteca está sempre em expansão, com novos materiais adicionados regularmente.",
        color=Color.magenta()
    ),
    Embed(
        title="🏆 **Sistema de Níveis e Recompensas**",
        description="**Avance no servidor e conquiste recompensas incríveis!**\n\n🔸 **Ganhando pontos:** Participe ativamente do servidor, interaja com outros membros e complete desafios para ganhar pontos.\n\n🔹 **Recompensas:** Acumule pontos para obter recompensas exclusivas, como cargos especiais, acesso a canais ocultos e muito mais!\n\n🎯 **Objetivos:** Defina suas metas e conquiste novos níveis para desbloquear conteúdo exclusivo.",
        color=Color.yellow()
    ),
    Embed(
        title="🎤 **Sistema de Votação e Feedback**",
        description="**Ajude a melhorar o servidor através das votações!**\n\n🔹 **Votações regulares:** Participe de votações importantes sobre mudanças no servidor e novos recursos.\n\n🔸 **Feedback contínuo:** Compartilhe suas opiniões em nossas enquetes e ajude-nos a crescer e melhorar!\n\n📊 **Resultados:** As votações e enquetes serão compartilhadas com todos, para garantir transparência.",
        color=Color.blurple()
    ),
    Embed(
        title="⚔️ **Competição de Jogos e Desafios**",
        description="**Participe das nossas competições semanais e mostre suas habilidades!**\n\n🏅 **Desafios diários:** A cada dia, um novo desafio será lançado. Vença e ganhe pontos!\n\n🎮 **Competição de Jogos:** Participe de competições de jogos organizadas e dispute prêmios incríveis!\n\n🎁 **Prêmios:** Os vencedores recebem prêmios exclusivos como emojis, cargos especiais e até prêmios em dinheiro!",
        color=Color.red()
    ),
    Embed(
        title="💎 **Loja do Servidor**",
        description="**Confira a nossa loja de itens exclusivos!**\n\n🛒 **Itens especiais:** Adquira itens exclusivos, como cargos personalizados, emojis especiais e muito mais!\n\n💳 **Moeda do Servidor:** Use a moeda interna do servidor para comprar itens e personalizações.\n\n🎉 **Promoções e descontos:** Fique de olho nas promoções para aproveitar descontos incríveis em itens da loja.",
        color=Color.green()
    ),
    Embed(
        title="👾 **Desenvolvimento e Atualizações**",
        description="**Fique por dentro das últimas atualizações do servidor!**\n\n🛠️ **Atualizações regulares:** Nosso time de desenvolvimento está sempre trabalhando para melhorar a experiência do servidor.\n\n🔧 **Novos recursos:** Acompanhe as mudanças e novas funcionalidades que são adicionadas regularmente.\n\n🚀 **Feedback de testes:** Se você quiser testar novas funcionalidades, participe do canal de beta testers.",
        color=Color.blue()
    ),
    Embed(
        title="📈 **Estatísticas do Servidor**",
        description="**Confira as estatísticas do servidor!**\n\n📊 **Número de membros:** O servidor está crescendo! Confira o número de membros ativos e novos inscritos.\n\n🔔 **Notificações:** Ative as notificações para ser avisado sempre que houver novos membros ou mudanças importantes.\n\n📅 **Histórico:** Veja o progresso do servidor desde sua criação até hoje.",
        color=Color.purple()
    ),
    Embed(
        title="🌍 **Regras Globais**",
        description="**As regras globais aplicam-se a todos os membros do servidor!**\n\n🌐 **Comportamento adequado:** Trate todos com respeito, sem importar a origem ou crença.\n\n✋ **Proibição de discriminação:** Qualquer tipo de discriminação será severamente punido.\n\n🚫 **Conteúdo impróprio:** É proibido compartilhar conteúdo explícito ou de ódio.",
        color=Color.orange()
    ),
    Embed(
        title="🔧 **Configurações de Notificações**",
        description="**Configure suas preferências de notificações para melhor aproveitamento do servidor!**\n\n🔔 **Notificações de novos posts:** Ative as notificações para receber alertas sobre novos conteúdos e atualizações.\n\n📩 **Notificações pessoais:** Configure alertas personalizados para eventos ou interações com seus amigos.\n\n⚠️ **Desativar notificações:** Caso queira evitar notificações excessivas, você pode desativá-las facilmente.",
        color=Color.teal()
    ),
       
    Embed(
        title="🏅 **Sistema de Conquistas**",
        description="**Desbloqueie conquistas incríveis enquanto interage no servidor!**\n\n🎯 **Desafios e conquistas:** Complete tarefas específicas para desbloquear conquistas especiais, como ‘Conquistador de Níveis’ ou ‘Explorador de Canais’.\n\n🥇 **Recompensas exclusivas:** Conquistas desbloqueiam prêmios como cargos personalizados, emojis especiais e outros benefícios exclusivos!\n\n🏆 **Competição saudável:** Participe de competições e veja como suas conquistas se comparam com outros membros.",
        color=Color.green()
    ),
    Embed(
        title="💬 **Sistema de Reputação e Feedback**",
        description="**Construa sua reputação no servidor!**\n\n⭐ **Reputação positiva:** Interaja de forma positiva com os outros membros para ganhar pontos de reputação e construir sua imagem no servidor.\n\n👎 **Reputação negativa:** Evite ações negativas, pois elas podem diminuir sua reputação e levar a punições.\n\n🛠️ **Gerenciamento de reputação:** Moderadores podem conceder ou remover pontos de reputação com base no comportamento e nas interações.",
        color=Color.blue()
    ),
    Embed(
        title="💎 **Cargos e Benefícios Premium**",
        description="**Aproveite as vantagens de ser um membro Premium!**\n\n🔹 **Cargos especiais:** Membros Premium têm acesso a cargos exclusivos que oferecem vantagens no servidor.\n\n💰 **Benefícios adicionais:** Como membro Premium, você tem acesso a canais privados, conteúdos exclusivos, emotes personalizados e mais!\n\n🎁 **Descontos e promoções:** Membros Premium recebem ofertas especiais em eventos e itens da loja do servidor.",
        color=Color.gold()
    ),
    Embed(
        title="🎨 **Sistema de Personalização**",
        description="**Deixe seu perfil ainda mais único!**\n\n🎭 **Customização do avatar e banner:** Mude a aparência do seu perfil com imagens personalizadas e efeitos especiais.\n\n🖋️ **Defina sua biografia:** Personalize seu perfil com uma biografia que descreva quem você é ou o que você faz no servidor.\n\n💬 **Cores e fontes personalizadas:** Adicione um toque pessoal ao seu nome e mensagens usando cores e fontes exclusivas.",
        color=Color.purple()
    ),
    Embed(
        title="🎯 **Missões e Tarefas Diárias**",
        description="**Complete missões e ganhe recompensas!**\n\n📅 **Missões diárias:** Todo dia, novas missões são oferecidas, incentivando a interação e a atividade no servidor.\n\n🎁 **Recompensas e prêmios:** Conclua as missões e receba itens, moedas e cargos exclusivos como prêmio.\n\n🔥 **Desafios especiais:** Às vezes, você encontrará desafios únicos que oferecem recompensas ainda mais valiosas!",
        color=Color.red()
    ),
    Embed(
        title="💬 **Interações com Bots**",
        description="**Aproveite os bots para interagir e melhorar sua experiência no servidor!**\n\n🤖 **Comandos do bot:** Aprenda a usar comandos interativos para personalizar sua experiência e acessar funções exclusivas.\n\n🎮 **Jogos e diversão:** Jogue com os bots e participe de competições dentro do servidor.\n\n📈 **Gerenciamento de funções:** Alguns bots oferecem funcionalidades como gerenciamento de cargos, canais e muito mais!",
        color=Color.blue()
    ),
    Embed(
        title="📅 **Calendário de Eventos**",
        description="**Fique por dentro de todos os eventos programados!**\n\n🗓️ **Eventos regulares:** Participe de eventos semanais, como sorteios, competições de jogos e mais!\n\n🏆 **Eventos especiais:** Eventos anuais e ocasionais oferecem prêmios grandiosos, como moedas e itens raros.\n\n📲 **Calendário de fácil acesso:** Acesse o calendário de eventos no canal específico e nunca perca uma data importante!",
        color=Color.dark_blue()
    ),
    Embed(
        title="🎮 **Jogos e Desafios Semanais**",
        description="**Participe dos jogos e desafios semanais do servidor!**\n\n🎯 **Desafios semanais:** Enfrente novos desafios e complete tarefas semanais para ganhar recompensas especiais.\n\n🏅 **Competições de jogos:** Participe de torneios e desafios de jogos organizados dentro do servidor.\n\n🔑 **Recompensas exclusivas:** Os vencedores ganham prêmios como cargos exclusivos, emojis personalizados e itens raros.",
        color=Color.orange()
    ),
    Embed(
        title="🔔 **Alertas de Mudança de Regras**",
        description="**Fique atento às mudanças nas regras do servidor!**\n\n⚠️ **Mudanças regulares:** O servidor pode atualizar as regras de tempos em tempos. Sempre leia as atualizações para garantir que você esteja seguindo as normas mais recentes.\n\n📜 **Notificação de alterações:** Toda vez que uma mudança de regra for feita, todos os membros serão alertados imediatamente.\n\n✅ **Conformidade obrigatória:** O não cumprimento das novas regras pode resultar em penalidades ou até banimento.",
        color=Color.green()
    ),
    Embed(
        title="💼 **Suporte Profissional**",
        description="**Receba ajuda profissional em várias áreas!**\n\n🔧 **Suporte técnico:** Se você estiver enfrentando problemas técnicos, entre em contato com nosso suporte técnico especializado.\n\n👨‍💻 **Consultoria e orientação:** Oferecemos consultoria sobre diferentes áreas, como criação de conteúdo, desenvolvimento e muito mais.\n\n🎓 **Aprendizado contínuo:** Participe de workshops e seminários online sobre uma variedade de tópicos!",
        color=Color.purple()
    ),
    Embed(
        title="🌟 **Histórico e Conquistas do Servidor**",
        description="**Veja como o servidor cresceu e suas principais conquistas!**\n\n🏅 **Marco de membros:** O servidor passou de 1000 membros! \n\n🌍 **Eventos históricos:** Conheça os maiores eventos e marcos da nossa jornada.\n\n🎯 **Prêmios e conquistas:** O servidor conquistou prêmios de excelência em vários tópicos, incluindo comunidade e eventos.",
        color=Color.gold()
    ),
    Embed(
        title="🔒 **Privacidade e Segurança**",
        description="**Sua segurança é nossa prioridade!**\n\n🔐 **Proteção de dados:** Trabalhamos com medidas avançadas para garantir que seus dados e informações no servidor sejam mantidos seguros.\n\n🛡️ **Monitoramento de segurança:** A equipe de moderação monitora ativamente para garantir que o servidor permaneça seguro contra ataques e comportamentos maliciosos.\n\n🚨 **Alerta de segurança:** Se detectar qualquer atividade suspeita, reporte imediatamente a um moderador ou administrador.",
        color=Color.red()
    ),
    Embed(
        title="📡 **Notificações e Anúncios Importantes**",
        description="**Nunca perca uma atualização importante!**\n\n📢 **Alertas imediatos:** Quando algo importante acontecer no servidor, você será notificado instantaneamente.\n\n📰 **Atualizações regulares:** Fique por dentro de todas as mudanças, desde novos recursos até atualizações de regras e eventos especiais.\n\n🔔 **Notificação personalizada:** Escolha como e quando receber suas notificações para nunca ficar por fora.",
        color=Color.blurple()
    ),
    Embed(
        title="🏆 **Premiações e Reconhecimentos**",
        description="**Reconheça os melhores membros do servidor!**\n\n🥇 **Membros do mês:** Todo mês, os membros mais ativos e engajados recebem prêmios exclusivos.\n\n🎉 **Premiações de eventos:** Participe de eventos e ganhe prêmios incríveis por suas habilidades e participação.\n\n🏅 **Reconhecimento público:** Membros notáveis são destacados nos canais do servidor para mostrar suas conquistas.",
        color=Color.yellow()
    ),
    Embed(
        title="💼 **Oportunidades de Colaboração**",
        description="**Colabore com outros membros do servidor!**\n\n🤝 **Projetos e parcerias:** Junte-se a outros membros para trabalhar em projetos colaborativos dentro do servidor.\n\n💡 **Desenvolvimento de ideias:** Participe da criação de novas ideias, eventos e recursos para o servidor.\n\n🎨 **Ofereça seus talentos:** Se você é criativo ou possui habilidades especiais, compartilhe seu trabalho com os outros e ganhe reconhecimento!",
        color=Color.green()
    ),
]
