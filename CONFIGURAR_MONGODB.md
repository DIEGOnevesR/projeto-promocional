# 🗄️ Configurar MongoDB para WhatsApp (RemoteAuth)

Este guia explica como configurar MongoDB para persistir a sessão do WhatsApp no Render.

## 🎯 Por que usar MongoDB?

- ✅ **Persistência**: A sessão não é perdida quando o serviço reinicia
- ✅ **Confiável**: Funciona mesmo no plano Free do Render
- ✅ **Seguro**: Dados armazenados de forma segura
- ✅ **Escalável**: Pode ser usado em múltiplos servidores

---

## 🚀 Opção 1: MongoDB Atlas (Recomendado - Gratuito)

### Passo 1: Criar conta no MongoDB Atlas

1. Acesse: https://www.mongodb.com/cloud/atlas/register
2. Crie uma conta gratuita
3. Escolha o plano **Free (M0)**

### Passo 2: Criar Cluster

1. Clique em "Build a Database"
2. Escolha **"Free"** (M0)
3. Escolha uma região próxima (ex: AWS / São Paulo)
4. Dê um nome ao cluster (ex: `whatsapp-sessions`)
5. Clique em "Create"

### Passo 3: Configurar Acesso

1. **Network Access:**
   - Clique em "Network Access"
   - Clique em "Add IP Address"
   - Selecione "Allow Access from Anywhere" (0.0.0.0/0)
   - Ou adicione o IP do Render

2. **Database Access:**
   - Clique em "Database Access"
   - Clique em "Add New Database User"
   - Escolha "Password" como método de autenticação
   - Crie um usuário e senha (anote!)
   - Role: "Atlas admin" ou "Read and write to any database"
   - Clique em "Add User"

### Passo 4: Obter String de Conexão

1. Clique em "Connect" no cluster
2. Escolha "Connect your application"
3. Driver: **Node.js**
4. Versão: **5.5 or later**
5. Copie a **Connection String**
   - Exemplo: `mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Passo 5: Configurar no Render

No serviço **whatsapp-sender** no Render, adicione:

**Variável de Ambiente:**
- **Key:** `MONGODB_URI`
- **Value:** `mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
  - (Substitua `usuario` e `senha` pelos valores que você criou)

**Variável Opcional:**
- **Key:** `MONGODB_DB_NAME`
- **Value:** `whatsapp-sessions` (ou outro nome)

**Para Ativar RemoteAuth:**
- **Key:** `USE_REMOTE_AUTH`
- **Value:** `true`

---

## 🚀 Opção 2: MongoDB no Render (Pago)

1. No Render, crie um novo **MongoDB** service
2. Escolha o plano (Starter: $7/mês)
3. Render gerará automaticamente a string de conexão
4. Use essa string como `MONGODB_URI`

---

## ✅ Verificar se Funcionou

Depois de configurar:

1. Faça commit e push do código atualizado
2. O Render fará deploy automaticamente
3. Verifique os logs do serviço **whatsapp-sender**
4. Você deve ver: `✅ Conectado ao MongoDB para armazenar sessão WhatsApp`

---

## 🔄 Migração de LocalAuth para RemoteAuth

Se você já tem uma sessão local:

1. **Primeira vez:** Escaneie o QR Code novamente
2. A sessão será salva no MongoDB
3. **Próximas vezes:** Não precisará escanear novamente!

---

## 🐛 Troubleshooting

### Erro: "MongoServerError: Authentication failed"
- Verifique se o usuário e senha estão corretos na connection string
- Verifique se o usuário tem permissões no MongoDB Atlas

### Erro: "MongoNetworkError"
- Verifique se o IP está liberado no Network Access
- Verifique se a connection string está correta

### Erro: "Connection timeout"
- Verifique se o MongoDB Atlas está acessível
- Tente usar "Allow Access from Anywhere" temporariamente

---

## 📝 Resumo das Variáveis

| Variável | Valor | Obrigatório |
|----------|-------|-------------|
| `MONGODB_URI` | String de conexão do MongoDB | Sim |
| `MONGODB_DB_NAME` | Nome do banco (padrão: whatsapp-sessions) | Não |
| `USE_REMOTE_AUTH` | `true` para ativar | Não (detecta automaticamente) |

---

**Pronto!** Agora sua sessão do WhatsApp será persistida no MongoDB e não será perdida quando o serviço reiniciar! 🎉


