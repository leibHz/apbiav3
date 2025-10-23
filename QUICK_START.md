# 🚀 Guia de Instalação Rápida - APBIA

## ⚠️ ATENÇÃO: SEGURANÇA DAS CHAVES

**AS CHAVES FORNECIDAS NO DOCUMENTO ORIGINAL FORAM EXPOSTAS PUBLICAMENTE!**

Antes de prosseguir, você DEVE:

1. **Revogar IMEDIATAMENTE** todas as chaves antigas:
   - Google AI Studio: https://aistudio.google.com/apikey
   - Supabase Dashboard: https://supabase.com/dashboard → Settings → API

2. **Gerar novas chaves** e nunca mais compartilhá-las publicamente

3. **Alterar a senha** do banco de dados Supabase

---

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Conta no Supabase (gratuita)
- API Key do Google Gemini (gratuita)
- Git

---

## 🔧 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/apbia.git
cd apbia
```

### 2. Crie o Ambiente Virtual

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

```bash
# Copie o template
cp .env.example .env

# Edite o arquivo .env com suas NOVAS credenciais
nano .env  # ou use seu editor favorito
```

**Preencha:**
- `SECRET_KEY` - Gere com: `python -c "import secrets; print(secrets.token_hex(32))"`
- `SUPABASE_URL` - URL do seu projeto
- `SUPABASE_KEY` - Nova Anon Key
- `SUPABASE_SERVICE_KEY` - Nova Service Role Key
- `GEMINI_API_KEY` - Nova API Key do Gemini

### 5. Configure o Banco de Dados no Supabase

1. Acesse o SQL Editor do Supabase
2. Cole e execute o conteúdo de `schema_supabase.sql`
3. Verifique se todas as tabelas foram criadas

### 6. Adicione Arquivos de Contexto

```bash
mkdir -p context_files

# Adicione seus arquivos TXT com informações da Bragantec
# Exemplo: context_files/resumos_bragantec_2024.txt
```

### 7. Execute o Aplicativo

```bash
python app.py
```

Acesse: **http://localhost:5000**

---

## 👤 Login Inicial

**Usuário Administrador Padrão:**
- **Email:** `admin@bragantec.ifsp.edu.br`
- **Senha:** `admin123`
- **⚠️ ALTERE IMEDIATAMENTE APÓS PRIMEIRO LOGIN!**

---

## 📁 Estrutura de Pastas

```
apbia/
├── app.py                    # Aplicação principal
├── config.py                 # Configurações
├── requirements.txt          # Dependências
├── .env                      # Variáveis (NÃO COMITAR!)
├── .env.example              # Template de variáveis
├── schema_supabase.sql       # Schema do banco
│
├── controllers/              # Controllers (MVC)
│   ├── auth_controller.py
│   ├── chat_controller.py
│   ├── admin_controller.py
│   └── project_controller.py
│
├── models/                   # Models (MVC)
│   └── models.py
│
├── dao/                      # Data Access Objects
│   └── dao.py
│
├── services/                 # Serviços externos
│   ├── gemini_service.py
│   └── pdf_service.py
│
├── utils/                    # Utilitários
│   ├── helpers.py
│   └── decorators.py
│
├── static/                   # Arquivos estáticos
│   ├── css/
│   ├── js/
│   └── uploads/
│
├── templates/                # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── chat.html
│   ├── admin/
│   ├── projetos/
│   └── errors/
│
└── context_files/            # Arquivos TXT de contexto
    └── (seus arquivos .txt aqui)
```

---

## ✅ Checklist de Configuração

- [ ] Python 3.11+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas
- [ ] Arquivo `.env` configurado com NOVAS chaves
- [ ] Schema SQL executado no Supabase
- [ ] Arquivos de contexto adicionados
- [ ] Senha admin alterada no primeiro login
- [ ] `.env` adicionado ao `.gitignore`

---

## 🐛 Troubleshooting

### Erro: "IA está temporariamente offline"
- Verifique se a `GEMINI_API_KEY` está correta no `.env`
- Teste a API em: https://aistudio.google.com

### Erro de Conexão com Banco de Dados
- Verifique `SUPABASE_URL` e `SUPABASE_KEY`
- Confirme que o schema foi executado
- Verifique se o projeto Supabase está ativo

### Erro 500 ao Enviar Mensagem
- Verifique os logs do console Python
- Confirme que os arquivos de contexto existem
- Teste a API do Gemini separadamente

### Erro de Importação
```bash
pip install --upgrade -r requirements.txt
```

---

## 🔐 Segurança

### ⚠️ NUNCA FAÇA ISSO:

- ❌ Comitar o arquivo `.env`
- ❌ Expor suas API Keys publicamente
- ❌ Usar a senha admin padrão em produção
- ❌ Desabilitar HTTPS em produção

### ✅ SEMPRE FAÇA ISSO:

- ✅ Use `.env` para credenciais
- ✅ Gere uma `SECRET_KEY` forte
- ✅ Altere senhas padrão imediatamente
- ✅ Mantenha dependências atualizadas
- ✅ Use HTTPS em produção

---

## 📚 Recursos

- [Documentação Flask](https://flask.palletsprojects.com/)
- [Documentação Gemini](https://ai.google.dev/gemini-api/docs)
- [Documentação Supabase](https://supabase.com/docs)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)

---

## 🆘 Suporte

Em caso de problemas:

1. Verifique os logs do servidor
2. Confirme que todas as variáveis de ambiente estão corretas
3. Teste a conexão com Supabase e Google AI separadamente
4. Verifique se os arquivos de contexto existem

---

## 📝 Próximos Passos

Após a instalação:

1. **Adicionar usuários** pelo painel admin
2. **Configurar arquivos de contexto** com informações da Bragantec
3. **Testar o chat** com a IA
4. **Criar um projeto de teste**
5. **Gerar PDF** do projeto

---

**APBIA** - Transformando ideias em projetos científicos de excelência! 🚀🔬