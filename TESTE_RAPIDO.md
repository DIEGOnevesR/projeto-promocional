# ⚡ Teste Rápido - WhatsApp

## 🚀 Execução Rápida (3 Passos)

### 1️⃣ Iniciar Servidor WhatsApp
```bash
start-whatsapp-server.bat
```
⏳ Aguarde: `✅ Cliente WhatsApp pronto!`

### 2️⃣ Executar Teste
```bash
test-whatsapp.bat
```
📋 Siga as instruções na tela

### 3️⃣ Verificar WhatsApp
📱 Verifique seu WhatsApp (5534999499430)
✅ Você deve receber a imagem com legenda!

---

## 📋 Checklist Rápido

- [ ] Servidor WhatsApp rodando
- [ ] QR Code escaneado
- [ ] Mensagem "✅ Cliente WhatsApp pronto!" apareceu
- [ ] Teste executado com sucesso
- [ ] Imagem recebida no WhatsApp
- [ ] Legenda com link de compra presente

---

## ❌ Problemas Comuns

| Problema | Solução |
|----------|---------|
| Servidor não conecta | Execute `start-whatsapp-server.bat` |
| QR Code não aparece | Reinicie o servidor |
| Imagem não enviada | Verifique autenticação do WhatsApp |
| Número errado | Verifique `whatsapp-sender.js` |

---

## 🎯 Teste Manual

Se preferir testar manualmente:

```python
import requests
import os

response = requests.post(
    'http://localhost:3001/send-image',
    json={
        'imagePath': os.path.abspath('banners/10-11-2025/SFL-10-11-2025-001-09-05-57.jpg'),
        'caption': 'Teste Manual\n\nCompre no Whatsapp - wa.me/551151944697?text=oi'
    }
)
print(response.json())
```

---

## 📞 Suporte

Para mais detalhes, consulte:
- `GUIA_TESTE_WHATSAPP.md` - Guia completo
- `README_WHATSAPP.md` - Documentação

---

## ✅ Pronto!

Após o teste bem-sucedido, os banners serão enviados automaticamente! 🎉

