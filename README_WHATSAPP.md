# 📱 Integração WhatsApp - Envio de Banners

Este guia explica como configurar e usar o sistema de envio de banners via WhatsApp.

## 📋 Pré-requisitos

1. **Node.js** instalado (versão 16.0.0 ou superior)
   - Download: https://nodejs.org/
   - Verificar instalação: `node --version`

2. **WhatsApp Web** funcionando no seu dispositivo

## 🚀 Configuração Inicial

### 1. Instalar Dependências

Execute no terminal:

```bash
npm install
```

Isso instalará:
- `whatsapp-web.js` - Biblioteca para interagir com WhatsApp
- `qrcode-terminal` - Exibir QR Code no terminal
- `express` - Servidor HTTP para receber requisições

### 2. Configurar Número do WhatsApp

O número já está configurado no arquivo `whatsapp-sender.js`:
- **Número de destino**: `5534999499430` (seu número)
- **Link de compra**: `wa.me/551151944697?text=oi`

Se precisar alterar, edite as constantes no início do arquivo `whatsapp-sender.js`:

```javascript
const WHATSAPP_NUMBER = '5534999499430@c.us';
const WHATSAPP_LINK = 'wa.me/551151944697?text=oi';
```

## 🎯 Como Usar

### Passo 1: Iniciar Servidor WhatsApp

**Windows:**
- Execute `start-whatsapp-server.bat`
- Ou no terminal: `npm start`

**Linux/Mac:**
```bash
node whatsapp-sender.js
```

### Passo 2: Autenticar WhatsApp

1. Quando o servidor iniciar, um **QR Code** aparecerá no terminal
2. Abra o **WhatsApp** no seu celular
3. Vá em **Menu** → **Dispositivos conectados** → **Conectar um dispositivo**
4. Escaneie o QR Code exibido no terminal
5. Aguarde a mensagem: `✅ Cliente WhatsApp pronto!`

⚠️ **Importante**: 
- Esta autenticação é feita apenas **uma vez**
- Os dados de autenticação são salvos na pasta `whatsapp-auth/`
- Mantenha o servidor rodando enquanto usar o sistema

### Passo 3: Gerar Banners

Execute normalmente o gerador de banners:

```bash
python main.py
```

Ou use a interface web através do `template_editor.html`.

## 🔄 Como Funciona

1. **Geração de Banner**: Quando um banner é gerado, ele é salvo como imagem JPEG
2. **Envio Imediato**: A imagem é enviada **imediatamente** para o WhatsApp
3. **Legenda Automática**: Cada imagem é enviada com a legenda:
   ```
   Banner {unidade} - {sequencia}
   
   Compre no Whatsapp - wa.me/551151944697?text=oi
   ```

## 📝 Estrutura de Arquivos

```
Projeto Promocional/
├── whatsapp-sender.js          # Servidor Node.js
├── package.json                # Dependências Node.js
├── start-whatsapp-server.bat   # Script de inicialização (Windows)
├── whatsapp-auth/              # Dados de autenticação (criado automaticamente)
├── main.py                     # Gerador de banners (modificado)
└── README_WHATSAPP.md          # Este arquivo
```

## 🛠️ Solução de Problemas

### Servidor não inicia

- Verifique se o Node.js está instalado: `node --version`
- Instale as dependências: `npm install`
- Verifique se a porta 3001 está disponível

### QR Code não aparece

- Verifique se há erros no terminal
- Tente reiniciar o servidor
- Limpe a pasta `whatsapp-auth/` e tente novamente

### Imagens não são enviadas

- Verifique se o servidor está rodando
- Verifique se o WhatsApp está autenticado (status: ready)
- Verifique se o número está correto no formato: `5534999499430@c.us`
- Verifique os logs no terminal do servidor

### Erro de autenticação

- Delete a pasta `whatsapp-auth/`
- Reinicie o servidor
- Escaneie o QR Code novamente

## 🔒 Segurança

- ⚠️ **Nunca compartilhe** a pasta `whatsapp-auth/`
- ⚠️ Mantenha o servidor rodando apenas quando necessário
- ⚠️ O WhatsApp Web pode ser desconectado se o celular ficar offline por muito tempo

## 📊 Status do Servidor

Para verificar o status do servidor, acesse:

```
http://localhost:3001/health
```

Resposta esperada:
```json
{
  "status": "ready",
  "message": "Cliente WhatsApp pronto",
  "number": "5534999499430@c.us"
}
```

## 🎉 Pronto!

Agora você pode gerar banners e eles serão enviados automaticamente para o seu WhatsApp!

Para mais informações, consulte a documentação do `whatsapp-web.js`:
https://wwebjs.dev/

