# 🗄️ Configurar MongoDB Atlas - Passo a Passo

Este guia mostra exatamente como configurar o MongoDB Atlas para o WhatsApp.

## 📋 Passo 1: Criar Conta e Cluster

1. Acesse: https://www.mongodb.com/cloud/atlas/register
2. Crie uma conta (pode usar Google/GitHub)
3. Escolha o plano **Free (M0)**
4. Escolha uma região próxima (ex: **AWS / São Paulo**)
5. Dê um nome ao cluster (ex: `Cluster0`)
6. Clique em **"Create"**

---

## 🔐 Passo 2: Configurar Acesso de Rede

1. No menu lateral, clique em **"Network Access"**
2. Clique em **"Add IP Address"**
3. Selecione **"Allow Access from Anywhere"** (0.0.0.0/0)
   - Ou adicione o IP específico do Render (mais seguro)
4. Clique em **"Confirm"**

---

## 👤 Passo 3: Criar Usuário do Banco

1. No menu lateral, clique em **"Database Access"**
2. Clique em **"Add New Database User"**
3. Configure:
   - **Authentication Method:** Password
   - **Username:** `lgp350diego_db_user` (ou outro nome)
   - **Password:** Crie uma senha forte (anote!)
   - **Database User Privileges:** "Atlas admin" ou "Read and write to any database"
4. Clique em **"Add User"**

---

## 🔗 Passo 4: Obter Connection String

1. No menu lateral, clique em **"Database"**
2. Clique em **"Connect"** no seu cluster
3. Escolha **"Connect your application"**
4. Driver: **Node.js**
5. Version: **5.5 or later**
6. Copie a **Connection String**

A string será algo como:
```
mongodb+srv://lgp350diego_db_user:<password>@cluster0.xsjcl7s.mongodb.net/?appName=Cluster0
```

**IMPORTANTE:** Substitua `<password>` pela senha que você criou no Passo 3!

Exemplo:
```
mongodb+srv://lgp350diego_db_user:MinhaSenh@123@cluster0.xsjcl7s.mongodb.net/?appName=Cluster0
```

---

## ⚙️ Passo 5: Configurar no Render

1. Acesse: https://dashboard.render.com
2. Clique no serviço **whatsapp-sender**
3. Vá em **"Environment"**
4. Adicione estas variáveis:

### Variável 1:
- **Key:** `MONGODB_URI`
- **Value:** `mongodb+srv://lgp350diego_db_user:SUA_SENHA@cluster0.xsjcl7s.mongodb.net/?appName=Cluster0`
  - (Substitua `SUA_SENHA` pela senha real)

### Variável 2 (Opcional):
- **Key:** `MONGODB_DB_NAME`
- **Value:** `whatsapp-sessions`

### Variável 3 (Opcional):
- **Key:** `USE_REMOTE_AUTH`
- **Value:** `true`

5. Clique em **"Save Changes"**
6. O Render fará um novo deploy automaticamente

---

## ✅ Passo 6: Verificar se Funcionou

1. Aguarde o deploy terminar (alguns minutos)
2. Verifique os logs do serviço **whatsapp-sender**
3. Você deve ver:
   ```
   ✅ Conectado ao MongoDB: whatsapp-sessions/whatsapp_sessions
   Usando RemoteAuth com MongoDB
   ```

4. Quando escanear o QR Code, a sessão será salva no MongoDB
5. Na próxima vez que o serviço reiniciar, não precisará escanear novamente!

---

## 🔒 Segurança

- ⚠️ **Nunca compartilhe** sua connection string
- ⚠️ **Nunca commite** a connection string no Git
- ⚠️ Use sempre variáveis de ambiente
- ⚠️ Considere restringir o IP no Network Access (mais seguro)

---

## 🐛 Troubleshooting

### Erro: "Authentication failed"
- Verifique se a senha na connection string está correta
- Verifique se o usuário existe no Database Access

### Erro: "Connection timeout"
- Verifique se o IP está liberado no Network Access
- Tente "Allow Access from Anywhere" temporariamente

### Erro: "MongoServerError"
- Verifique se a connection string está completa
- Certifique-se de que substituiu `<password>` pela senha real

---

## 📝 Resumo

1. ✅ Criar cluster no MongoDB Atlas
2. ✅ Liberar acesso de rede (0.0.0.0/0)
3. ✅ Criar usuário do banco
4. ✅ Obter connection string
5. ✅ Configurar no Render como variável de ambiente
6. ✅ Pronto! Sessão será persistida

---

**Dúvidas?** Consulte os logs no Render para mais detalhes.



