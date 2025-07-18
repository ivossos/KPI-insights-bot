# 🚀 Guia de Deploy no Replit - IA Fiscal Capivari

Este guia explica como fazer o deploy do sistema IA Fiscal Capivari no Replit.

## 📋 Pré-requisitos

Antes de fazer o deploy, você precisará das seguintes credenciais:

### 🔑 Obrigatórias:
- **Apify API Token** - Para web scraping
- **Claude API Key** - Para explicações de IA
- **Google OAuth Client ID & Secret** - Para autenticação
- **Credenciais SMTP** - Para notificações por email

### 🔑 Opcionais:
- **Telegram Bot Token & Chat ID** - Para notificações no Telegram

## 🚀 Passo a Passo do Deploy

### 1. Criar Conta no Replit

1. Acesse [replit.com](https://replit.com)
2. Crie uma conta ou faça login
3. Escolha um plano (recomendado: Hacker Plan para produção)

### 2. Importar o Projeto

1. Clique em "Create Repl"
2. Escolha "Import from GitHub"
3. Cole a URL do repositório: `https://github.com/ioannisvossos/ia-fiscal-capivari`
4. Clique em "Import from GitHub"

### 3. Configurar Variáveis de Ambiente (Secrets)

No Replit, vá em **Tools → Secrets** e adicione:

#### 🔐 Credenciais Obrigatórias:

```
APIFY_API_TOKEN=your_apify_token_here
CLAUDE_API_KEY=your_claude_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@capivari.sp.gov.br
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
WEBHOOK_SECRET=your_webhook_secret_here
```

#### 🔐 Credenciais Opcionais:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

#### 🔐 URLs e Configurações:

```
GOOGLE_REDIRECT_URI=https://your-repl-name.your-username.repl.co/auth/callback
DATABASE_URL=sqlite:///./data/ia_fiscal.db
PRECOS_API_URL=https://api.precos.gov.br
CATMAT_API_URL=https://api.catmat.gov.br
```

### 4. Configurar o Arquivo .replit

O arquivo `.replit` já está configurado, mas você pode ajustar se necessário:

```toml
[nix]
channel = "stable-22_11"

[deployment]
run = ["python", "main_replit.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 8000
externalPort = 80

[[ports]]
localPort = 8501
externalPort = 3000
```

### 5. Instalar Dependências

No terminal do Replit, execute:

```bash
pip install -r requirements-replit.txt
```

### 6. Executar o Sistema

Clique no botão **"Run"** ou execute:

```bash
python main_replit.py
```

### 7. Acessar o Sistema

- **API**: `https://your-repl-name.your-username.repl.co`
- **Dashboard**: `https://your-repl-name.your-username.repl.co:3000`

## 🔧 Configuração Detalhada

### Google OAuth Setup

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione um existente
3. Ative a Google+ API
4. Crie credenciais OAuth 2.0
5. Adicione a URL do Replit nas URLs autorizadas:
   - `https://your-repl-name.your-username.repl.co/auth/callback`

### Configuração do Apify

1. Acesse [Apify Console](https://console.apify.com)
2. Crie um novo Actor ou use o fornecido
3. Configure o webhook para apontar para:
   - `https://your-repl-name.your-username.repl.co/webhook/ingestion`

### Configuração do Telegram (Opcional)

1. Fale com [@BotFather](https://t.me/BotFather) no Telegram
2. Crie um novo bot com `/newbot`
3. Obtenha o token do bot
4. Adicione o bot ao grupo ou canal desejado
5. Obtenha o Chat ID

### Configuração de Email

Para Gmail:
1. Ative a verificação em duas etapas
2. Gere uma senha de app
3. Use a senha de app no `SMTP_PASSWORD`

## 📊 Monitoramento

### Logs

Os logs estão disponíveis em:
- Console do Replit
- Arquivos em `/logs/`

### Health Check

Verifique a saúde do sistema:
```
GET https://your-repl-name.your-username.repl.co/health
```

### Métricas

Visualize métricas em:
```
GET https://your-repl-name.your-username.repl.co/metrics
```

## 🔒 Segurança

### Secrets Management

- **NUNCA** commite credenciais no código
- Use apenas o sistema de Secrets do Replit
- Rotacione as chaves regularmente

### OAuth Security

- Configure URLs de callback corretas
- Use HTTPS sempre
- Mantenha client secrets seguros

### API Security

- Use webhook secrets para validação
- Implemente rate limiting
- Monitore tentativas de acesso

## 🚨 Troubleshooting

### Problemas Comuns:

**1. Erro de Importação de Módulos**
```bash
# Solução: Verificar PYTHONPATH
export PYTHONPATH=/home/runner/ia-fiscal-capivari/src
```

**2. Erro de Permissão de Arquivos**
```bash
# Solução: Criar diretórios necessários
mkdir -p data/raw data/processed data/alerts logs reports
```

**3. Erro de Conexão com APIs**
```bash
# Verificar se as credenciais estão corretas nos Secrets
# Testar conectividade
curl -I https://api.anthropic.com
```

**4. Erro de OAuth**
- Verificar se a URL de callback está correta
- Confirmar que o projeto Google tem as APIs habilitadas
- Verificar se as credenciais não expiraram

**5. Erro de Webhook**
- Verificar se a URL do webhook está acessível
- Confirmar que o signature está correto
- Verificar logs do Apify

### Logs Úteis:

```bash
# Ver logs da aplicação
tail -f logs/app.log

# Ver logs de erro
tail -f logs/error.log

# Ver logs estruturados
tail -f logs/structured.log
```

## 📈 Otimização para Produção

### Performance

1. **Upgrade para Hacker Plan** - Mais CPU e memória
2. **Configure Caching** - Redis ou memcached
3. **Otimize Queries** - Use índices no banco
4. **Monitoring** - Configure alertas

### Scaling

1. **Database** - Considere PostgreSQL para produção
2. **File Storage** - Use cloud storage para arquivos grandes
3. **CDN** - Para servir assets estáticos
4. **Load Balancing** - Para múltiplas instâncias

### Backup

1. **Database Backup** - Agende backups regulares
2. **Configuration Backup** - Versione configurações
3. **Logs Backup** - Archive logs antigos

## 🆘 Suporte

### Recursos de Ajuda:

- **Documentação**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/ioannisvossos/ia-fiscal-capivari/issues)
- **Replit Community**: [Replit Community](https://replit.com/talk)

### Contato:

- **Email**: suporte@capivari.sp.gov.br
- **Telegram**: @capivari_tech

## 📝 Checklist de Deploy

- [ ] Conta Replit criada
- [ ] Projeto importado
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Google OAuth configurado
- [ ] Apify Actor configurado
- [ ] Webhook configurado
- [ ] Dependências instaladas
- [ ] Sistema executando
- [ ] Dashboard acessível
- [ ] Notificações funcionando
- [ ] Logs configurados
- [ ] Health check OK

## 🎉 Deploy Completo!

Após seguir todos os passos, seu sistema estará rodando em:

- **🌐 API**: `https://your-repl-name.your-username.repl.co`
- **📊 Dashboard**: `https://your-repl-name.your-username.repl.co:3000`

O sistema começará a coletar dados automaticamente e gerar alertas conforme configurado.

---

**Parabéns! 🎉 O IA Fiscal Capivari está rodando no Replit!**