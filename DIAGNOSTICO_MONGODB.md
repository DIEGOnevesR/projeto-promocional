# 🔍 Diagnóstico: Problema de Conexão MongoDB

## ❌ Erro Atual:
```
Timeout ao conectar ao MongoDB (30s)
```

## 🔍 Possíveis Causas:

### 1. Network Access não configurado (MAIS PROVÁVEL)
- MongoDB Atlas bloqueia conexões por padrão
- Precisa liberar IP no Network Access

### 2. Connection String incorreta
- Senha errada
- URI mal formatada
- Faltam parâmetros

### 3. Problemas de rede/firewall
- Render pode ter restrições de saída
- MongoDB Atlas pode estar bloqueando

---

## ✅ Passo a Passo para Resolver:

### PASSO 1: Verificar Network Access no MongoDB Atlas

1. Acesse: https://cloud.mongodb.com
2. Faça login
3. Selecione seu projeto
4. Vá em **"Network Access"** (menu lateral)
5. Verifique a lista de IPs

**Se NÃO houver nenhum IP:**
- Clique em **"Add IP Address"**
- Selecione **"Allow Access from Anywhere"** (0.0.0.0/0)
- Clique em **"Confirm"**
- Aguarde alguns minutos para propagar

**Se JÁ houver IPs:**
- Verifique se há `0.0.0.0/0` na lista
- Se não houver, adicione

### PASSO 2: Verificar Connection String no Render

No Render, serviço **whatsapp-sender**, verifique:

**Variável:** `MONGODB_URI`
**Valor deve ser:**
```
mongodb+srv://lgp350diego_db_user:LUHIJsVTrgKRcMUR@cluster0.xsjcl7s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

**Verifique:**
- ✅ Senha está correta (sem espaços)
- ✅ Tem `retryWrites=true&w=majority`
- ✅ Não tem espaços extras
- ✅ Começa com `mongodb+srv://`

### PASSO 3: Verificar Database Access

1. No MongoDB Atlas, vá em **"Database Access"**
2. Verifique se o usuário `lgp350diego_db_user` existe
3. Verifique se a senha está correta
4. Verifique se tem permissões (Atlas admin ou Read/Write)

### PASSO 4: Testar Connection String Localmente

No seu computador, execute:

```powershell
# Configurar variável
$env:MONGODB_URI="mongodb+srv://lgp350diego_db_user:LUHIJsVTrgKRcMUR@cluster0.xsjcl7s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Testar
node testar-mongodb.js
```

**Se funcionar localmente:**
- Problema é Network Access no MongoDB Atlas
- Libere o IP (Passo 1)

**Se não funcionar localmente:**
- Problema é na connection string ou credenciais
- Verifique senha e usuário

---

## 🧪 Teste Rápido

Execute este comando no PowerShell para testar:

```powershell
node -e "const {MongoClient}=require('mongodb');(async()=>{const c=new MongoClient('mongodb+srv://lgp350diego_db_user:LUHIJsVTrgKRcMUR@cluster0.xsjcl7s.mongodb.net/?retryWrites=true&w=majority');try{await c.connect();console.log('✅ Conectado!');await c.close();}catch(e){console.error('❌ Erro:',e.message);}})();"
```

---

## 📋 Checklist Completo:

- [ ] Network Access permite 0.0.0.0/0 no MongoDB Atlas
- [ ] Connection string está correta no Render
- [ ] Senha está correta (sem espaços)
- [ ] Connection string tem `retryWrites=true&w=majority`
- [ ] Usuário existe no Database Access
- [ ] Usuário tem permissões corretas
- [ ] Teste local funciona (se sim, problema é Network Access)

---

## 🎯 Solução Mais Provável:

**99% das vezes é Network Access!**

1. Vá no MongoDB Atlas
2. Network Access → Add IP Address
3. Allow Access from Anywhere (0.0.0.0/0)
4. Aguarde 2-3 minutos
5. Teste novamente

---

**Me diga o resultado do teste local para identificarmos exatamente o problema!**


<<<<<<< HEAD
=======


>>>>>>> origin/master
