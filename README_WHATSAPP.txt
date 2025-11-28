═══════════════════════════════════════════════════════════════
  INTEGRAÇÃO WHATSAPP - ENVIO DE BANNERS
═══════════════════════════════════════════════════════════════

Este guia explica como configurar e usar o sistema de envio de
banners via WhatsApp.

═══════════════════════════════════════════════════════════════
  PRE-REQUISITOS
═══════════════════════════════════════════════════════════════

1. Node.js instalado (versão 16.0.0 ou superior)
   - Download: https://nodejs.org/
   - Verificar instalação: node --version

2. WhatsApp Web funcionando no seu dispositivo

═══════════════════════════════════════════════════════════════
  CONFIGURAÇÃO INICIAL
═══════════════════════════════════════════════════════════════

1. INSTALAR DEPENDÊNCIAS
───────────────────────────────────────────────────────────────
Execute no terminal:

npm install

Isso instalará:
- whatsapp-web.js - Biblioteca para interagir com WhatsApp
- qrcode-terminal - Exibir QR Code no terminal
- express - Servidor HTTP para receber requisições

───────────────────────────────────────────────────────────────

2. CONFIGURAR NÚMERO DO WHATSAPP
───────────────────────────────────────────────────────────────
O número já está configurado no arquivo whatsapp-sender.js:
- Número de destino: 5534999499430 (seu número)
- Link de compra: wa.me/551151944697?text=oi

Se precisar alterar, edite as constantes no início do arquivo
whatsapp-sender.js:

const WHATSAPP_NUMBER = '5534999499430@c.us';
const WHATSAPP_LINK = 'wa.me/551151944697?text=oi';

═══════════════════════════════════════════════════════════════
  COMO USAR
═══════════════════════════════════════════════════════════════

PASSO 1: INICIAR SERVIDOR WHATSAPP
───────────────────────────────────────────────────────────────

Windows:
- Execute start-whatsapp-server.bat
- Ou no terminal: npm start

Linux/Mac:
node whatsapp-sender.js

───────────────────────────────────────────────────────────────

PASSO 2: AUTENTICAR WHATSAPP
───────────────────────────────────────────────────────────────

1. Quando o servidor iniciar, um QR Code aparecerá no terminal
2. Abra o WhatsApp no seu celular
3. Vá em Menu → Dispositivos conectados → Conectar um dispositivo
4. Escaneie o QR Code exibido no terminal
5. Aguarde a mensagem: ✅ Cliente WhatsApp pronto!

⚠️  IMPORTANTE: 
- Esta autenticação é feita apenas UMA VEZ
- Os dados de autenticação são salvos na pasta whatsapp-auth/
- Mantenha o servidor rodando enquanto usar o sistema

───────────────────────────────────────────────────────────────

PASSO 3: GERAR BANNERS
───────────────────────────────────────────────────────────────
Execute normalmente o gerador de banners:

python main.py

Ou use a interface web através do template_editor.html.

═══════════════════════════════════════════════════════════════
  COMO FUNCIONA
═══════════════════════════════════════════════════════════════

1. Geração de Banner: Quando um banner é gerado, ele é salvo
   como imagem JPEG

2. Envio Imediato: A imagem é enviada IMEDIATAMENTE para o
   WhatsApp

3. Legenda Automática: Cada imagem é enviada com a legenda:
   
   Banner {unidade} - {sequencia}
   
   Compre no Whatsapp - wa.me/551151944697?text=oi

═══════════════════════════════════════════════════════════════
  ESTRUTURA DE ARQUIVOS
═══════════════════════════════════════════════════════════════

Projeto Promocional/
├── whatsapp-sender.js          # Servidor Node.js
├── package.json                # Dependências Node.js
├── start-whatsapp-server.bat   # Script de inicialização (Windows)
├── whatsapp-auth/              # Dados de autenticação (criado automaticamente)
├── main.py                     # Gerador de banners (modificado)
└── README_WHATSAPP.txt         # Este arquivo

═══════════════════════════════════════════════════════════════
  SOLUÇÃO DE PROBLEMAS
═══════════════════════════════════════════════════════════════

SERVIDOR NÃO INICIA
───────────────────────────────────────────────────────────────
- Verifique se o Node.js está instalado: node --version
- Instale as dependências: npm install
- Verifique se a porta 3001 está disponível

───────────────────────────────────────────────────────────────

QR CODE NÃO APARECE
───────────────────────────────────────────────────────────────
- Verifique se há erros no terminal
- Tente reiniciar o servidor
- Limpe a pasta whatsapp-auth/ e tente novamente

───────────────────────────────────────────────────────────────

IMAGENS NÃO SÃO ENVIADAS
───────────────────────────────────────────────────────────────
- Verifique se o servidor está rodando
- Verifique se o WhatsApp está autenticado (status: ready)
- Verifique se o número está correto no formato: 5534999499430@c.us
- Verifique os logs no terminal do servidor

───────────────────────────────────────────────────────────────

ERRO DE AUTENTICAÇÃO
───────────────────────────────────────────────────────────────
- Delete a pasta whatsapp-auth/
- Reinicie o servidor
- Escaneie o QR Code novamente

═══════════════════════════════════════════════════════════════
  SEGURANÇA
═══════════════════════════════════════════════════════════════

⚠️  NUNCA compartilhe a pasta whatsapp-auth/
⚠️  Mantenha o servidor rodando apenas quando necessário
⚠️  O WhatsApp Web pode ser desconectado se o celular ficar
    offline por muito tempo

═══════════════════════════════════════════════════════════════
  STATUS DO SERVIDOR
═══════════════════════════════════════════════════════════════

Para verificar o status do servidor, acesse:

http://localhost:3001/health

Resposta esperada:
{
  "status": "ready",
  "message": "Cliente WhatsApp pronto",
  "number": "5534999499430@c.us"
}

═══════════════════════════════════════════════════════════════
  PRONTO!
═══════════════════════════════════════════════════════════════

Agora você pode gerar banners e eles serão enviados
automaticamente para o seu WhatsApp!

Para mais informações, consulte a documentação do whatsapp-web.js:
https://wwebjs.dev/

