# IA Fiscal Capivari

Sistema de monitoramento e alertas para gastos municipais de Capivari/SP utilizando inteligência artificial.

## Visão Geral

O "IA Fiscal Capivari" é um sistema automatizado que monitora gastos públicos municipais, detecta anomalias fiscais e gera alertas inteligentes. O sistema coleta dados dos portais de transparência Betha, processa e analisa as informações usando regras de negócio e IA, e apresenta os resultados através de um dashboard interativo.

## Características Principais

- **Coleta Automatizada**: Scraping diário dos portais Betha (folha, despesas, contratos)
- **Processamento ETL**: Normalização e enriquecimento de dados
- **Detecção de Anomalias**: Regras de negócio para identificar irregularidades
- **Explicações com IA**: Claude AI gera explicações claras e assessíveis
- **Dashboard Interativo**: Interface Streamlit com autenticação Google OAuth
- **Notificações**: Alertas via email e Telegram
- **Relatórios**: Exportação em PDF, Excel e CSV

## Tipos de Anomalias Detectadas

1. **Sobrepreço**: Itens com preços acima da média de mercado
2. **Fracionamento**: Divisão de despesas para evitar licitação
3. **Concentração de Fornecedores**: Poucos fornecedores dominam contratos
4. **Emergências Recorrentes**: Mesmo fornecedor com muitas emergências
5. **Anomalias na Folha**: Pagamentos atípicos na folha de pagamento
6. **Horários Incomuns**: Transações em horários suspeitos
7. **Pagamentos Duplicados**: Possíveis pagamentos duplicados

## Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Portais       │    │   Apify Actor   │    │   FastAPI       │
│   Betha         │────│   (Scraping)    │────│   (Ingestion)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Claude AI     │    │   ETL Pipeline  │
│   Streamlit     │────│   (Explicações) │────│   (Processar)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Notificações  │    │   Regras de     │    │   Armazenamento │
│   Email/Telegram│────│   Negócio       │────│   Parquet/SQLite│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Instalação

### Pré-requisitos

- Python 3.8+
- Node.js 16+ (para Apify Actor)
- Conta Apify
- Chave da API Claude
- Credenciais Google OAuth

### Configuração

1. **Clone o repositório**:
```bash
git clone https://github.com/your-org/ia-fiscal-capivari.git
cd ia-fiscal-capivari
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

4. **Configure o arquivo de configuração**:
```bash
# Edite config/config.json conforme necessário
```

5. **Crie os diretórios necessários**:
```bash
mkdir -p data/raw data/processed data/alerts logs reports
```

## Uso

### Executar o Sistema Completo

```bash
python main.py --mode full
```

### Executar Apenas a API

```bash
python main.py --mode api
```

### Executar Apenas o Dashboard

```bash
python main.py --mode dashboard
```

### Executar Apenas o Scheduler

```bash
python main.py --mode scheduler
```

## Configuração do Apify Actor

1. **Instale o Apify CLI**:
```bash
npm install -g apify-cli
```

2. **Configure o actor**:
```bash
cd src/scraping
npm install
apify push
```

3. **Configure o webhook**:
   - No console Apify, configure o webhook para apontar para sua API
   - URL: `https://seu-app.repl.co/webhook/ingestion`

## Configuração das Notificações

### Email (SMTP)

1. Configure as credenciais SMTP no arquivo `.env`
2. Adicione destinatários no código ou banco de dados

### Telegram

1. Crie um bot no Telegram (@BotFather)
2. Obtenha o token do bot
3. Configure o token e chat ID no arquivo `.env`

## Autenticação Google OAuth

1. Crie um projeto no Google Cloud Console
2. Ative a Google+ API
3. Crie credenciais OAuth 2.0
4. Configure as credenciais no arquivo `.env`

## Estrutura do Projeto

```
ia-fiscal-capivari/
├── src/
│   ├── api/                 # FastAPI application
│   ├── auth/                # Authentication
│   ├── ai/                  # Claude AI integration
│   ├── dashboard/           # Streamlit dashboard
│   ├── export/              # Report generation
│   ├── ingestion/           # Data ingestion
│   ├── models/              # Data models
│   ├── monitoring/          # Logging and metrics
│   ├── notifications/       # Email and Telegram
│   ├── rules/               # Business rules engine
│   └── scraping/            # Apify actor
├── config/
│   └── config.json          # Application configuration
├── data/                    # Data storage
├── logs/                    # Application logs
├── reports/                 # Generated reports
├── requirements.txt         # Python dependencies
├── main.py                  # Application entry point
└── README.md               # This file
```

## Desenvolvimento

### Executar Testes

```bash
pytest tests/
```

### Executar Linting

```bash
flake8 src/
black src/
```

### Adicionar Nova Regra de Negócio

1. Adicione a regra em `src/rules/engine.py`
2. Implemente a lógica de detecção
3. Adicione testes em `tests/test_rules.py`
4. Atualize a documentação

### Personalizar Explicações da IA

1. Edite os prompts em `src/ai/claude_explainer.py`
2. Adicione contexto específico para novos tipos de regras
3. Teste as explicações geradas

## Monitoramento

### Métricas

O sistema coleta métricas de:
- Requests da API
- Processamento de dados
- Alertas gerados
- Notificações enviadas
- Uso de sistema

### Logs

Logs são armazenados em:
- `logs/app.log` - Logs gerais
- `logs/error.log` - Logs de erro
- `logs/structured.log` - Logs estruturados (JSON)

### Health Checks

Endpoint de saúde: `GET /health`

## Deployment

### Replit

1. Importe o projeto no Replit
2. Configure as variáveis de ambiente (Secrets)
3. Execute o projeto

### Docker

```bash
# Build
docker build -t ia-fiscal-capivari .

# Run
docker run -p 8000:8000 -p 8501:8501 ia-fiscal-capivari
```

### Google Cloud Run

```bash
# Deploy
gcloud run deploy ia-fiscal-capivari \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para suporte técnico:
- Email: suporte@capivari.sp.gov.br
- Issues: [GitHub Issues](https://github.com/ioannisvossos/ia-fiscal-capivari/issues)

## Roadmap

- [ ] Integração com mais portais de transparência
- [ ] Análise preditiva com machine learning
- [ ] API pública para terceiros
- [ ] Aplicativo mobile
- [ ] Integração com sistemas de auditoria
- [ ] Alertas em tempo real
- [ ] Análise de redes de fornecedores

## Créditos

Desenvolvido pela equipe de tecnologia da Prefeitura Municipal de Capivari/SP com apoio da comunidade de código aberto.

---

**IA Fiscal Capivari** - Transparência e eficiência na gestão pública através da inteligência artificial.