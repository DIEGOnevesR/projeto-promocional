# 🔧 Solução: Timeout ao Conectar ao MongoDB

O erro de timeout geralmente acontece por um destes motivos:

## 🔍 Diagnóstico

### 1. Verificar Connection String

A connection string deve estar no formato:
```
mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**IMPORTANTE:**
- Substitua `<password>` pela senha real
- A senha não pode ter caracteres especiais sem encoding
- Se a senha tiver `@`, `#`, `%`, etc., precisa ser codificada

### 2. Verificar Network Access no MongoDB Atlas

1. Acesse: https://cloud.mongodb.com
2. Vá em **"Network Access"**
3. Verifique se há um IP liberado
4. **Adicione:** `0.0.0.0/0` (Allow Access from Anywhere)
   - Ou adicione o IP específico do Render

### 3. Verificar Database Access

1. Vá em **"Database Access"**
2. Verifique se o usuário existe
3. Verifique se a senha está correta
4. Verifique se o usuário tem permissões

### 4. Verificar Connection String no Render

No Render, verifique se a variável `MONGODB_URI` está:
- ✅ Configurada corretamente
- ✅ Com a senha substituída (não `<password>`)
- ✅ Sem espaços extras
- ✅ Com `?retryWrites=true&w=majority` no final

---

## 🛠️ Soluções

### Solução 1: Codificar Senha na URL

Se sua senha tem caracteres especiais (`@`, `#`, `%`, etc.), codifique:

- `@` → `%40`
- `#` → `%23`
- `%` → `%25`
- `&` → `%26`
- `+` → `%2B`
- `=` → `%3D`

**Exemplo:**
Se sua senha é `Minha@Senh#123`:
```
mongodb+srv://usuario:Minha%40Senh%23123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### Solução 2: Recriar Usuário com Senha Simples

1. No MongoDB Atlas, vá em **"Database Access"**
2. Delete o usuário atual
3. Crie um novo com senha simples (sem caracteres especiais)
4. Use essa senha na connection string

### Solução 3: Verificar IP do Render

1. No MongoDB Atlas, vá em **"Network Access"**
2. Clique em **"Add IP Address"**
3. Selecione **"Allow Access from Anywhere"** (0.0.0.0/0)
4. Clique em **"Confirm"**

### Solução 4: Testar Connection String Localmente

Execute no seu computador:

```powershell
# Criar arquivo test-mongo.js
node testar-mongodb.js
```

Isso vai testar se a connection string funciona.

---

## 📝 Connection String Correta

Formato completo:
```
mongodb+srv://USUARIO:SENHA@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

**Exemplo real:**
```
mongodb+srv://lgp350diego_db_user:MinhaSenha123@cluster0.xsjcl7s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

---

## ✅ Checklist

- [ ] Connection string tem senha real (não `<password>`)
- [ ] Senha está codificada se tiver caracteres especiais
- [ ] Network Access permite 0.0.0.0/0 ou IP do Render
- [ ] Usuário existe no Database Access
- [ ] Usuário tem permissões (Atlas admin ou Read/Write)
- [ ] Connection string termina com `?retryWrites=true&w=majority`

---

## 🧪 Testar Localmente

1. Configure a variável de ambiente:
   ```powershell
   $env:MONGODB_URI="sua-connection-string-aqui"
   ```

2. Execute o teste:
   ```powershell
   node testar-mongodb.js
   ```

Se funcionar localmente mas não no Render, o problema é Network Access.

---

**Me diga qual dessas soluções resolveu ou se precisa de mais ajuda!**



<<<<<<< HEAD
=======


>>>>>>> origin/master
