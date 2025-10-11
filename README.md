# 🤖 APBIA - Assistente de Projetos para Bragantec Baseado em IA

Sistema de assistente virtual inteligente desenvolvido para auxiliar estudantes e orientadores na **Bragantec**, a feira de ciências do IFSP Bragança Paulista.

## 📋 Sobre o Projeto

O APBIA utiliza o **Google Gemini 2.5 Flash** com thinking mode para fornecer orientação personalizada no desenvolvimento de projetos científicos, oferecendo:

- 💡 Geração de ideias inovadoras
- 📊 Planejamento estruturado de projetos
- 📚 Acesso ao histórico da Bragantec
- 🎯 Assistência personalizada por tipo de usuário
- 💬 Interface de chat intuitiva

## 🚀 Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **Flask** - Framework web
- **Flask-Login** - Autenticação
- **Google Generative AI** - Gemini 2.5 Flash
- **Supabase** - Banco de dados PostgreSQL
- **bcrypt** - Hash de senhas

### Frontend
- **HTML5 / CSS3**
- **Bootstrap 5.3** - Framework CSS
- **JavaScript (ES6+)**
- **Font Awesome 6** - Ícones

### Arquitetura
- **Padrão MVC** (Model-View-Controller)
- **DAO** (Data Access Object)
- **POO** (Programação Orientada a Objetos)

## 📦 Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/apbia.git
cd apbia
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves **NOVAS** (não use as que foram expostas!):

```env
SECRET_KEY=sua-chave-secreta-forte
DEBUG=True

SUPABASE_URL=sua-url-supabase
SUPABASE_KEY=sua-nova-anon-key
SUPABASE_SERVICE_KEY=sua-nova-service-key

GEMINI_API_KEY=sua-nova-api-key-gemini
```

### 5. Configurar Banco de Dados

Acesse o SQL Editor do Supabase e execute o script `schema_supabase.sql`:

```bash
# O arquivo está em: schema_supabase.sql
```

### 6. Adicionar Arquivos de Contexto

Coloque os arquivos TXT dos cadernos de resumos da Bragantec na pasta `context_files/`:

```bash
mkdir -p context_files
# Adicione seus arquivos .txt aqui
```

### 7. Executar o Aplicativo

```bash
python app.py
```

Acesse: `http://localhost:5000`

## 🔐 Segurança

### ⚠️ IMPORTANTE - Proteção de Credenciais

1. **NUNCA comite** o arquivo `.env` no Git
2. **SEMPRE use** `.env.example` como template
3. **Gere novas chaves** se as suas foram expostas:
   - Google AI Studio: https://aistudio.google.com/apikey
   - Supabase Dashboard: https://supabase.com/dashboard

### Resetar Chaves Comprometidas

Se suas chaves foram expostas:

1. **Gemini API Key**: Revogue imediatamente em https://aistudio.google.com/apikey
2. **Supabase Keys**: Resete em Project Settings > API
3. **Senha do BD**: Altere nas configurações do projeto

## 👥 Tipos de Usuário

### Administrador
- Gerencia usuários
- Liga/desliga a IA
- Acessa painel administrativo

### Participante
- Conversa com IA personalizada
- Desenvolve projetos
- Histórico de conversas

### Orientador
- IA adaptada para mentoria
- Gerencia múltiplos projetos
- Orientação pedagógica

### Visitante
- Acesso limitado
- Apenas consulta

## 📁 Estrutura do Projeto

```
apbia/
├── app.py                      # Aplicação Flask principal
├── config.py                   # Configurações
├── requirements.txt            # Dependências
├── .env.example               # Template de variáveis
├── .gitignore                 # Arquivos ignorados
│
├── models/
│   └── models.py              # Classes de modelo
│
├── dao/
│   └── dao.py                 # Data Access Objects
│
├── controllers/
│   ├── auth_controller.py     # Autenticação
│   ├── chat_controller.py     # Chat com IA
│   └── admin_controller.py    # Admin
│
├── services/
│   └── gemini_service.py      # Integração Gemini
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   └── chat.js
│   └── uploads/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── chat.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── usuarios.html
│   │   └── configuracoes.html
│   └── errors/
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
│
└── context_files/             # Arquivos TXT de contexto
```

## 🤖 Sobre o Gemini 2.5 Flash

O APBIA utiliza o **Gemini 2.5 Flash** com as seguintes características:

- ✨ **Thinking Mode**: Raciocínio aprofundado
- 📄 **Processamento de Documentos**: Lê arquivos TXT diretamente
- 🧠 **Multimodal**: Texto, imagens e arquivos
- ⚡ **Rápido e Eficiente**: Respostas em tempo real

## 🛠️ Desenvolvimento

### Adicionar Novo Tipo de Usuário

1. Insira no banco de dados:
```sql
INSERT INTO tipos_usuario (nome) VALUES ('Novo Tipo');
```

2. Atualize os métodos no `models.py`

### Personalizar IA

Edite `services/gemini_service.py` na função `_get_system_instruction()`

## 📝 TO-DO / Futuras Melhorias

- [ ] Sistema de notificações em tempo real
- [ ] Estatísticas de uso detalhadas
- [ ] Export de conversas em PDF
- [ ] Modo escuro
- [ ] API REST para integração externa
- [ ] Sistema de feedback sobre respostas da IA
- [ ] Armazenamento de histórico de mensagens no BD
- [ ] Upload de múltiplos arquivos simultâneos
- [ ] Suporte a mais idiomas

## 📄 Licença

Este projeto foi desenvolvido para uso educacional no IFSP Bragança Paulista.

## 👨‍💻 Autor

Desenvolvido para a **Bragantec - IFSP Bragança Paulista**

## 🆘 Suporte

Em caso de problemas:

1. Verifique os logs do servidor
2. Confirme que todas as variáveis de ambiente estão corretas
3. Verifique a conexão com Supabase e Google AI
4. Consulte a documentação oficial:
   - [Flask](https://flask.palletsprojects.com/)
   - [Gemini API](https://ai.google.dev/gemini-api/docs)
   - [Supabase](https://supabase.com/docs)

## 🔧 Troubleshooting

### Erro: "IA está temporariamente offline"
- Verifique a `GEMINI_API_KEY` no `.env`
- Confirme que a IA está ativada no painel admin

### Erro de Conexão com Banco de Dados
- Verifique as credenciais do Supabase
- Confirme que o schema foi executado corretamente

### Erro 500 ao Enviar Mensagem
- Verifique os logs para detalhes
- Confirme que os arquivos de contexto existem

## 📸 Screenshots

*Em breve: capturas de tela do sistema*

## 🤝 Contribuindo

Este é um projeto educacional. Sugestões e melhorias são bem-vindas!

---

**APBIA** - Transformando ideias em projetos científicos de excelência! 🚀🔬