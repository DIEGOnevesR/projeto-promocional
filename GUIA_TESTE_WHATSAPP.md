# 🧪 Guia de Teste - Envio via WhatsApp

Este guia passo a passo irá ajudá-lo a testar o envio de imagens para o WhatsApp.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter:

- ✅ Node.js instalado (versão 16+)
- ✅ Python instalado
- ✅ Dependências do Node.js instaladas (`npm install`)
- ✅ Servidor WhatsApp rodando e autenticado

## 🚀 Passo a Passo do Teste

### **PASSO 1: Iniciar o Servidor WhatsApp**

1. Abra um terminal/Prompt de Comando
2. Navegue até a pasta do projeto
3. Execute:
   ```bash
   start-whatsapp-server.bat
   ```
   Ou:
   ```bash
   npm start
   ```

4. **Aguarde aparecer o QR Code** no terminal
5. **Escaneie o QR Code** com seu WhatsApp:
   - Abra o WhatsApp no celular
   - Vá em **Menu** (três pontos) → **Dispositivos conectados**
   - Toque em **Conectar um dispositivo**
   - Escaneie o QR Code exibido no terminal

6. **Aguarde a mensagem**: `✅ Cliente WhatsApp pronto!`

⚠️ **IMPORTANTE**: Mantenha esta janela aberta!

---

### **PASSO 2: Executar o Teste Guiado**

1. **Abra um NOVO terminal** (deixe o servidor WhatsApp rodando no anterior)

2. Execute o script de teste:
   ```bash
   test-whatsapp.bat
   ```
   Ou:
   ```bash
   python test_whatsapp.py
   ```

3. **Siga as instruções** que aparecem na tela:
   - O script verificará se o servidor está rodando
   - O script procurará uma imagem de teste
   - O script enviará a imagem para o WhatsApp

---

### **PASSO 3: Verificar o Resultado**

1. **Verifique seu WhatsApp** (número: 5534999499430)
2. Você deve receber:
   - ✅ Uma imagem (banner de teste)
   - ✅ Uma legenda com o texto:
     ```
     Banner de Teste
     
     Compre no Whatsapp - wa.me/551151944697?text=oi
     ```

---

## 🔍 O que o Teste Verifica?

O script de teste verifica:

1. ✅ **Conexão com o servidor**: Se o servidor WhatsApp está rodando
2. ✅ **Status do WhatsApp**: Se o WhatsApp está autenticado e pronto
3. ✅ **Imagem de teste**: Se existe uma imagem para testar
4. ✅ **Envio de imagem**: Se a imagem é enviada com sucesso
5. ✅ **Legenda**: Se a legenda é adicionada corretamente

---

## ❌ Solução de Problemas

### Problema: "Servidor WhatsApp não está disponível"

**Solução:**
1. Verifique se o servidor está rodando
2. Execute `start-whatsapp-server.bat`
3. Aguarde aparecer "✅ Cliente WhatsApp pronto!"
4. Execute o teste novamente

---

### Problema: "Servidor está rodando mas não está pronto"

**Solução:**
1. Verifique se o QR Code foi escaneado
2. Escaneie o QR Code novamente se necessário
3. Aguarde a mensagem "✅ Cliente WhatsApp pronto!"
4. Execute o teste novamente

---

### Problema: "Nenhuma imagem de teste encontrada"

**Solução:**
1. Gere um banner primeiro:
   ```bash
   python main.py
   ```
2. Ou coloque uma imagem JPG na pasta `banners/`
3. Execute o teste novamente

---

### Problema: "Erro ao enviar imagem"

**Soluções possíveis:**

1. **Verifique o número do WhatsApp:**
   - Abra `whatsapp-sender.js`
   - Verifique se o número está correto: `5534999499430@c.us`

2. **Verifique a autenticação:**
   - Delete a pasta `whatsapp-auth/`
   - Reinicie o servidor
   - Escaneie o QR Code novamente

3. **Verifique a conexão com a internet:**
   - Certifique-se de que há conexão com a internet
   - O WhatsApp Web precisa de internet para funcionar

4. **Verifique os logs do servidor:**
   - Olhe a janela do servidor WhatsApp
   - Veja se há mensagens de erro
   - Copie as mensagens de erro para depuração

---

## 📊 Verificação Manual

Se preferir testar manualmente:

### 1. Verificar Status do Servidor

Acesse no navegador:
```
http://localhost:3001/health
```

Deve retornar:
```json
{
  "status": "ready",
  "message": "Cliente WhatsApp pronto",
  "number": "5534999499430@c.us"
}
```

### 2. Testar Envio Manual

Você pode usar o código Python abaixo para testar:

```python
import requests
import os

# Caminho da imagem de teste
image_path = "banners/10-11-2025/SFL-10-11-2025-001-09-05-57.jpg"

# Enviar para o servidor
response = requests.post(
    'http://localhost:3001/send-image',
    json={
        'imagePath': os.path.abspath(image_path),
        'caption': 'Teste Manual\n\nCompre no Whatsapp - wa.me/551151944697?text=oi'
    }
)

print(response.json())
```

---

## ✅ Teste Bem-Sucedido

Se o teste foi bem-sucedido, você verá:

```
✅ TESTE CONCLUÍDO COM SUCESSO!

📱 Verifique seu WhatsApp:
   - Você deve ter recebido a imagem
   - A legenda deve conter o link de compra
   - O número deve ser: 5534999499430

🎉 O sistema está funcionando corretamente!
   Agora você pode gerar banners e eles serão enviados automaticamente.
```

E no seu WhatsApp, você receberá a imagem com a legenda!

---

## 🎯 Próximos Passos

Após o teste bem-sucedido:

1. ✅ **Gere banners normalmente**: `python main.py`
2. ✅ **Cada banner será enviado automaticamente** para o WhatsApp
3. ✅ **As legendas serão adicionadas automaticamente** com o link de compra

---

## 📞 Suporte

Se tiver problemas:

1. Verifique os logs do servidor WhatsApp
2. Verifique o arquivo `README_WHATSAPP.md`
3. Verifique se todas as dependências estão instaladas
4. Tente reiniciar o servidor WhatsApp

---

## 🎉 Pronto!

Agora você está pronto para usar o sistema de envio via WhatsApp!

Buena suerte! 🚀

