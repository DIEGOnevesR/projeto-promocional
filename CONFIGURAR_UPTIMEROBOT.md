# 🔄 Como Configurar UptimeRobot para Manter Projeto Ativo no Render

Este guia explica como configurar o UptimeRobot para manter seus serviços Render ativos 24/7, mesmo no plano gratuito.

## 📋 URLs dos Seus Serviços

Com base na configuração do projeto, você tem os seguintes serviços no Render:

1. **Backend Principal**: `https://projeto-promocional.onrender.com`
2. **WhatsApp Sender**: `https://whatsapp-sender-weq8.onrender.com`
3. **Gmail Monitor**: `https://gmail-monitor-pfts.onrender.com`

## 🚀 Passo a Passo: Configurar UptimeRobot

### 1. Criar Conta no UptimeRobot

1. Acesse: https://uptimerobot.com
2. Clique em **"Log In"** no canto superior direito
3. Se não tiver conta, clique em **"Sign Up"** ou acesse: https://uptimerobot.com/signUp
4. Você pode se cadastrar com:
   - **Google** (recomendado - mais rápido)
   - **GitHub**
   - **Email** (precisa verificar email depois)

### 2. Adicionar Monitores

Após fazer login, você verá o dashboard. Para cada serviço:

#### Monitor 1: Backend Principal

1. Clique em **"+ Add New Monitor"** ou **"Add Monitor"**
2. Preencha:
   - **Monitor Type**: Selecione `HTTP(s)`
   - **Friendly Name**: `Projeto Promocional - Backend`
   - **URL (or IP)**: `https://projeto-promocional.onrender.com/health`
   - **Monitoring Interval**: `5 minutes` (gratuito)
   - **Alert Contacts**: Selecione seu email (ou adicione um novo)
3. Clique em **"Create Monitor"**

#### Monitor 2: WhatsApp Sender

1. Clique em **"+ Add New Monitor"** novamente
2. Preencha:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `WhatsApp Sender`
   - **URL (or IP)**: `https://whatsapp-sender-weq8.onrender.com/health`
   - **Monitoring Interval**: `5 minutes`
   - **Alert Contacts**: Selecione seu email
3. Clique em **"Create Monitor"**

#### Monitor 3: Gmail Monitor

1. Clique em **"+ Add New Monitor"** novamente
2. Preencha:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `Gmail Monitor`
   - **URL (or IP)**: `https://gmail-monitor-pfts.onrender.com/health`
   - **Monitoring Interval**: `5 minutes`
   - **Alert Contacts**: Selecione seu email
3. Clique em **"Create Monitor"**

### 3. Verificar Configuração

Após criar os monitores, você verá:

- ✅ **Status**: "Up" (verde) = Serviço está funcionando
- ⚠️ **Status**: "Down" (vermelho) = Serviço está offline
- ⏸️ **Status**: "Paused" = Monitor pausado

## 📊 Limites do Plano Gratuito

- ✅ **50 monitores** (você só precisa de 3)
- ✅ **Intervalo mínimo**: 5 minutos (suficiente para manter ativo)
- ✅ **Notificações por email**: Ilimitadas
- ✅ **Histórico**: 2 meses

## ⚙️ Configurações Avançadas (Opcional)

### Alertas Personalizados

1. Vá em **"My Settings"** → **"Alert Contacts"**
2. Adicione seu email, Telegram, Slack, etc.
3. Configure quando receber alertas (só quando cair, ou sempre)

### Página de Status Pública

1. Vá em **"My Settings"** → **"Public Status Page"**
2. Ative a página pública
3. Compartilhe o link com sua equipe

## 🔍 Verificar se Está Funcionando

1. Acesse seu dashboard no UptimeRobot
2. Verifique se todos os 3 monitores estão com status **"Up"** (verde)
3. Aguarde alguns minutos e verifique o histórico de requisições
4. Teste acessando as URLs diretamente no navegador

## 🐛 Troubleshooting

### Monitor mostra "Down" mas o serviço está funcionando

- Verifique se a URL está correta (incluindo `/health`)
- Verifique se o endpoint `/health` existe no servidor
- Aguarde alguns minutos (pode levar tempo para atualizar)

### Não recebe notificações

- Verifique se o email está verificado
- Verifique a pasta de spam
- Configure alertas em **"My Settings"** → **"Alert Contacts"**

### Serviço ainda entra em sleep

- Verifique se o intervalo está configurado para 5 minutos ou menos
- Verifique se o monitor está ativo (não pausado)
- Aguarde alguns minutos após configurar (pode levar tempo para começar)

## 📝 Notas Importantes

- ⏱️ O Render pode levar **10-30 segundos** para "acordar" o serviço após o sleep
- 🔄 A primeira requisição após o sleep pode ser mais lenta
- 💰 O plano gratuito do UptimeRobot é suficiente para manter seus 3 serviços ativos
- 📧 Você receberá notificações por email quando algum serviço cair

## ✅ Checklist de Configuração

- [ ] Conta criada no UptimeRobot
- [ ] Monitor 1: Backend Principal configurado
- [ ] Monitor 2: WhatsApp Sender configurado
- [ ] Monitor 3: Gmail Monitor configurado
- [ ] Todos os monitores mostrando status "Up"
- [ ] Alertas configurados e testados

## 🔗 Links Úteis

- **UptimeRobot Dashboard**: https://uptimerobot.com/dashboard
- **Documentação**: https://uptimerobot.com/api/
- **Render Dashboard**: https://dashboard.render.com

---

**Pronto!** Seus serviços agora estarão ativos 24/7, mesmo no plano gratuito do Render! 🎉

