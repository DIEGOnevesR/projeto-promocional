# 📧 Monitor de E-mails Gmail

Sistema de monitoramento automático de e-mails do Gmail com envio automático via WhatsApp.

## 📋 Funcionalidades

- ✅ Conexão com Gmail via OAuth2
- ✅ Monitoramento automático de novos e-mails
- ✅ Extração automática de informações do e-mail
- ✅ Formatação de mensagem para WhatsApp
- ✅ Geração de link de autorização
- ✅ Envio automático via WhatsApp
- ✅ Rastreamento de e-mails processados (SQLite)
- ✅ Recuperação de e-mails pendentes após desligamento
- ✅ Interface web integrada no template_editor.html

## 🚀 Configuração Inicial

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Gmail API

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Gmail API**
4. Vá em **Credenciais** → **Criar credenciais** → **ID do cliente OAuth 2.0**
5. Configure:
   - Tipo de aplicativo: **Aplicativo da área de trabalho**
   - Nome: Gmail Monitor
6. Baixe o arquivo JSON e salve como `credentials.json` na raiz do projeto

### 3. Estrutura de Arquivos

```
Projeto Promocional/
├── credentials.json          # Credenciais OAuth2 (baixar do Google Cloud)
├── token.json                # Token de acesso (gerado automaticamente)
├── emails_sent.db            # Banco de dados SQLite (criado automaticamente)
├── gmail-monitor-api.py      # Servidor Flask API
├── gmail_service.py           # Serviço Gmail
├── email_processor.py         # Processamento de e-mails
├── email_database.py          # Gerenciamento do banco de dados
└── template_editor.html       # Interface web (já atualizada)
```

## 🎯 Como Usar

### Passo 1: Iniciar Servidor WhatsApp

Certifique-se de que o servidor WhatsApp está rodando:

```bash
npm start
# ou
node whatsapp-sender.js
```

### Passo 2: Iniciar Servidor Gmail Monitor

```bash
python gmail-monitor-api.py
```

O servidor iniciará na porta **5001** (porta 5000 é usada pelo servidor do gerador de banners).

### Passo 3: Abrir Interface Web

1. Abra o arquivo `template_editor.html` no navegador
2. Clique na aba **📧 Gmail Monitor**
3. Clique em **🔐 Conectar Gmail**
4. Autorize o acesso na janela do navegador que abrir
5. O token será salvo automaticamente em `token.json`

### Passo 4: Configurar Monitoramento

1. Defina o intervalo de verificação (padrão: 5 minutos)
2. Clique em **▶️ Iniciar Monitoramento**
3. O sistema começará a verificar novos e-mails automaticamente

## 📧 Formato do E-mail Esperado

O sistema espera e-mails no seguinte formato:

```
Prezado, NOME COMPLETO DO VENDEDOR,

O(A) NOME_ASSISTENTE Cliente: NOME_EMPRESA - CNPJ: XX.XXX.XXX/XXXX-XX - Cod Cliente: XXXXXXX - Telefone utilizado: (XX) XXXXX-XXXX

Encaminhe esse e-mail para vendermais@friboi.com.br com sua autorização para que possamos te ajudar com o ajuste do telefone

Telefone do Vendedor: (XX) XXXXX-XXXX
```

### Informações Extraídas

- **Nome do Vendedor**: Primeiro nome extraído
- **Name**: Nome da assistente (ex: Patiocanoagrill)
- **Code**: Código do cliente
- **Phone**: Telefone utilizado (formatado para link)
- **Empresa**: Nome da empresa
- **CNPJ**: CNPJ do cliente
- **Telefone do Vendedor**: Para envio via WhatsApp

## 📱 Mensagem WhatsApp Gerada

A mensagem será formatada automaticamente:

```
Prezado, [PRIMEIRO_NOME]

O(A) [NAME], tentou acessar a conta do Cliente: [CODE] - [EMPRESA] - CNPJ: [CNPJ] na Assistente Virtual WhatsApp com o telefone [TELEFONE] porém esse telefone não está cadastrado no sistema.

Clique no Link Abaixo para autorizar ou recusar o Acesso desse cliente com esse número.

[LINK_DE_AUTORIZAÇÃO]
```

## 🔗 Link de Autorização

O link é gerado automaticamente com as variáveis:

- `name`: Nome da assistente (URL encoded)
- `code`: Código do cliente
- `phone`: Telefone sem formatação (apenas números)
- `empresa`: Nome da empresa (URL encoded)

Exemplo:
```
https://script.google.com/macros/s/.../exec?name=Patiocanoagrill&code=3051288&phone=8897797542&empresa=PATIO%20GRILL
```

## 🗄️ Banco de Dados

O sistema usa SQLite (`emails_sent.db`) para rastrear:

- E-mails recebidos
- Informações extraídas
- Status de envio (enviado/pendente)
- Tentativas de envio
- Erros (se houver)

### Estrutura da Tabela

- `message_id`: ID único do Gmail
- `enviado_whatsapp`: 0 = pendente, 1 = enviado
- `data_envio`: Data/hora do envio
- `tentativas`: Número de tentativas
- `erro`: Mensagem de erro (se houver)

## 🔄 Recuperação de E-mails Pendentes

Se o servidor ficar desligado:

1. Ao reiniciar, clique em **🔄 Processar Pendentes**
2. O sistema verificará todos os e-mails não enviados
3. Tentará enviar novamente em ordem cronológica

## 📊 API Endpoints

### `POST /gmail/connect`
Conecta ao Gmail (inicia OAuth2)

### `GET /gmail/status`
Retorna status da conexão

### `POST /gmail/start-monitor`
Inicia monitoramento automático

### `POST /gmail/stop-monitor`
Para monitoramento

### `GET /gmail/monitor-status`
Retorna status do monitor e estatísticas

### `GET /gmail/pending-emails`
Lista e-mails pendentes

### `POST /gmail/process-pending`
Processa e-mails pendentes

### `GET /gmail/history`
Retorna histórico de e-mails

### `POST /gmail/test-email`
Testa processamento de e-mail (envia corpo do e-mail no JSON)

## ⚙️ Configurações

### Intervalo de Verificação

Padrão: 5 minutos (300 segundos)

Pode ser alterado na interface web ou via API.

### Porta do Servidor

Padrão: 5001 (porta 5000 é usada pelo servidor do gerador de banners)

Para alterar, edite `gmail-monitor-api.py`:

```python
GMAIL_MONITOR_PORT = 5001  # Altere aqui
app.run(host='0.0.0.0', port=GMAIL_MONITOR_PORT, debug=True)
```

## 🛠️ Solução de Problemas

### Erro: "Arquivo de credenciais não encontrado"

- Certifique-se de que `credentials.json` está na raiz do projeto
- Baixe o arquivo do Google Cloud Console

### Erro: "Gmail não está autenticado"

- Clique em **Conectar Gmail** na interface
- Autorize o acesso na janela do navegador
- Verifique se `token.json` foi criado

### E-mails não estão sendo enviados

1. Verifique se o servidor WhatsApp está rodando (porta 3001)
2. Verifique os logs na interface web
3. Verifique se o telefone do vendedor foi extraído corretamente
4. Tente processar e-mails pendentes manualmente

### Token expirado

- Delete o arquivo `token.json`
- Reconecte o Gmail na interface
- Um novo token será gerado

## 📝 Logs

Os logs são exibidos em tempo real na interface web na seção **📝 Logs**.

Cada ação é registrada com timestamp:
- ✅ Sucesso
- ❌ Erro
- ⚠️ Aviso
- 🔄 Processamento

## 🔒 Segurança

- ⚠️ **Nunca compartilhe** `credentials.json` ou `token.json`
- ⚠️ Adicione esses arquivos ao `.gitignore`
- ⚠️ Mantenha as credenciais seguras

## 📞 Suporte

Para problemas ou dúvidas, verifique:
1. Logs na interface web
2. Logs do servidor Python
3. Status do servidor WhatsApp

