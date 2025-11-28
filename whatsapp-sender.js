const { Client, LocalAuth, RemoteAuth, MessageMedia } = require('whatsapp-web.js');
const MongoStore = require('./mongo-store');
const qrcode = require('qrcode-terminal');
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();

// Configurar CORS para permitir requisições do frontend
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    
    // Responder a requisições OPTIONS (preflight)
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    
    next();
});

app.use(express.json());

// Número do WhatsApp para enviar (formato: 5534999499430@c.us)
const WHATSAPP_NUMBER = process.env.WHATSAPP_NUMBER || '5534999499430@c.us';
const WHATSAPP_LINK = 'wa.me/551151944697?text=oi';

// Configuração MongoDB para RemoteAuth
const MONGODB_URI = process.env.MONGODB_URI || process.env.MONGO_URI || 'mongodb://localhost:27017';
const MONGODB_DB_NAME = process.env.MONGODB_DB_NAME || 'whatsapp-sessions';
const USE_REMOTE_AUTH = process.env.USE_REMOTE_AUTH === 'true' || !!process.env.MONGODB_URI;

let client = null;
let isReady = false;
let serverRunning = false;
let currentQR = null;
const serverLogs = [];
const MAX_SERVER_LOGS = 500;

function addLog(type, message) {
    const entry = {
        timestamp: new Date().toISOString(),
        type,
        message,
    };
    
    serverLogs.push(entry);
    if (serverLogs.length > MAX_SERVER_LOGS) {
        serverLogs.splice(0, serverLogs.length - MAX_SERVER_LOGS);
    }
    
    const emojiMap = {
        INFO: 'ℹ️',
        QR_CODE: '📱',
        READY: '✅',
        AUTHENTICATED: '🔐',
        AUTH_FAILURE: '❌',
        DISCONNECTED: '⚠️',
        RECONNECT: '🔄',
        LOGOUT: '🚪',
        ERROR: '⛔',
    };
    
    const emoji = emojiMap[type] || '📝';
    const time = new Date().toLocaleTimeString('pt-BR', { hour12: false });
    const logMessage = `[${time}] ${emoji} ${message}`;
    
    if (type === 'ERROR' || type === 'AUTH_FAILURE') {
        console.error(logMessage);
    } else {
        console.log(logMessage);
    }
    
    return entry;
}

async function stopWhatsAppClient() {
    if (!client) {
        serverRunning = false;
        isReady = false;
        currentQR = null;
        return;
    }
    
    serverRunning = false;
    
    try {
        await client.destroy();
    } catch (error) {
        addLog('ERROR', `Erro ao destruir cliente WhatsApp: ${error.message}`);
    } finally {
        client = null;
        isReady = false;
        currentQR = null;
    }
}

// Inicializar cliente WhatsApp
async function initializeWhatsApp() {
    console.log('\n🔍 [DEBUG] initializeWhatsApp() chamada');
    console.log(`   client existe: ${!!client}`);
    console.log(`   serverRunning: ${serverRunning}`);
    
    if (client) {
        addLog('INFO', 'Cliente WhatsApp já está inicializado.');
        console.log('⚠️ [DEBUG] Cliente já existe, retornando...');
        return;
    }
    
    console.log('✅ [DEBUG] Iniciando novo cliente...');
    addLog('INFO', 'Inicializando cliente WhatsApp...');
    serverRunning = true;
    isReady = false;
    currentQR = null;
    
    // Escolher estratégia de autenticação
    let authStrategy;
    if (USE_REMOTE_AUTH) {
        addLog('INFO', 'Tentando usar RemoteAuth com MongoDB...');
        try {
            const mongoStore = new MongoStore({
                uri: MONGODB_URI,
                dbName: MONGODB_DB_NAME,
                collectionName: 'whatsapp_sessions',
            });
            
            // Testar conexão antes de usar
            try {
                await mongoStore.connect();
                addLog('INFO', '✅ Conectado ao MongoDB com sucesso');
            } catch (mongoError) {
                addLog('ERROR', `Erro ao conectar ao MongoDB: ${mongoError.message}`);
                addLog('INFO', 'Falling back para LocalAuth devido a erro de conexão');
                throw mongoError; // Força fallback
            }
            
            // Configurar RemoteAuth com backup mínimo (60000ms = 1 minuto)
            // O RemoteAuth requer pelo menos 60000ms, mas não usamos dataPath
            // para evitar problemas com ZIP no Render (filesystem efêmero)
            try {
                authStrategy = new RemoteAuth({
                    store: mongoStore,
                    backupSyncIntervalMs: 60000, // Mínimo aceito: 1 minuto
                    // Não usar dataPath para evitar problemas com ZIP
                });
                addLog('INFO', 'RemoteAuth configurado com MongoDB (backup mínimo)');
            } catch (authError) {
                addLog('ERROR', `Erro ao configurar RemoteAuth: ${authError.message}`);
                throw authError;
            }
            
            // Ocultar senha na URL para logs
            const safeUri = MONGODB_URI.replace(/\/\/([^:]+):([^@]+)@/, '//$1:***@');
            addLog('INFO', `MongoDB configurado: ${safeUri}/${MONGODB_DB_NAME}`);
        } catch (error) {
            addLog('ERROR', `Erro ao configurar MongoDB: ${error.message}`);
            addLog('INFO', 'Usando LocalAuth como fallback (sessão não será persistida)');
            authStrategy = new LocalAuth({
                dataPath: './whatsapp-auth'
            });
        }
    } else {
        addLog('INFO', 'Usando LocalAuth (armazenamento local)');
        authStrategy = new LocalAuth({
            dataPath: './whatsapp-auth'
        });
    }
    
    client = new Client({
        authStrategy: authStrategy,
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--disable-features=TranslateUI,VizDisplayCompositor',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-renderer-backgrounding',
                '--disable-speech-api',
                '--disable-sync',
                '--hide-scrollbars',
                '--mute-audio',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--password-store=basic',
                '--use-mock-keychain',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-offer-store-unmasked-wallet-cards',
                '--memory-pressure-off',
                '--max-old-space-size=512',
                '--disable-web-security',
            ],
            ignoreHTTPSErrors: true,
            timeout: 60000,
            defaultViewport: { width: 800, height: 600 },
            // Configurações adicionais para evitar erros do Puppeteer
            handleSIGINT: false,
            handleSIGTERM: false,
            handleSIGHUP: false,
            // Reduzir uso de memória
            protocolTimeout: 120000, // 2 minutos
            // Ignorar erros de página
            ignoreDefaultArgs: ['--disable-extensions']
        },
        webVersionCache: {
            type: 'remote',
            remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54-beta.html',
        }
    });

    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelays = [5000, 10000, 20000, 30000, 60000];

    client.on('qr', (qr) => {
        currentQR = qr;
        isReady = false;
        addLog('QR_CODE', 'Novo QR Code disponível. Escaneie para conectar.');
        console.log('\n📱 ========================================');
        console.log('📱 ESCANEIE O QR CODE COM SEU WHATSAPP:');
        console.log('📱 ========================================\n');
        qrcode.generate(qr, { small: true });
        console.log('\n⏳ Aguardando autenticação...\n');
    });

    client.on('ready', () => {
        isReady = true;
        currentQR = null;
        reconnectAttempts = 0;
        addLog('READY', 'Cliente WhatsApp pronto!');
        addLog('INFO', `Número configurado: ${WHATSAPP_NUMBER}`);
    });

    client.on('authenticated', () => {
        addLog('AUTHENTICATED', 'Autenticado com sucesso!');
    });
    
    // Capturar erros do cliente (incluindo erros de backup e Puppeteer)
    client.on('error', (error) => {
        // Ignorar erros relacionados a backup ZIP (não são críticos)
        if (error.message && error.message.includes('RemoteAuth.zip')) {
            addLog('WARN', 'Aviso sobre backup ZIP (não crítico): ' + error.message);
            return; // Não tratar como erro crítico
        }
        
        // Tratar erros do Puppeteer de forma mais suave
        if (error.message && (error.message.includes('JSHandle') || error.message.includes('evaluate') || error.message.includes('puppeteer'))) {
            addLog('WARN', `Aviso do Puppeteer (pode ser temporário): ${error.message}`);
            // Não encerrar o cliente por erros do Puppeteer
            return;
        }
        
        addLog('ERROR', `Erro no cliente WhatsApp: ${error.message}`);
        if (error.stack) {
            addLog('ERROR', `Stack: ${error.stack.split('\n').slice(0, 3).join('\n')}`);
        }
    });

    client.on('auth_failure', (msg) => {
        isReady = false;
        currentQR = null;
        addLog('AUTH_FAILURE', `Falha na autenticação: ${msg}`);
    });

    client.on('disconnected', (reason) => {
        isReady = false;
        currentQR = null;
        addLog('DISCONNECTED', `Cliente desconectado: ${reason}`);
        
        if (!serverRunning) {
            addLog('INFO', 'Reconexão não executada porque o servidor foi parado manualmente.');
            return;
        }
        
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = reconnectDelays[reconnectAttempts] || 60000;
            addLog('RECONNECT', `Tentando reconectar em ${delay / 1000}s... (tentativa ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            
            setTimeout(() => {
                reconnectAttempts++;
                try {
                    client.initialize();
                } catch (err) {
                    addLog('ERROR', `Erro ao tentar reconectar: ${err.message}`);
                }
            }, delay);
        } else {
            addLog('ERROR', 'Número máximo de tentativas de reconexão atingido. Reinicie o servidor manualmente.');
        }
    });

    // client.on('message', ...) // mantido desativado para reduzir uso de CPU

    // Inicializar cliente com tratamento de erro melhorado
    try {
        addLog('INFO', 'Inicializando cliente WhatsApp...');
        client.initialize().catch((initError) => {
            // Se o erro for relacionado ao RemoteAuth.zip, tentar continuar
            if (initError.message && initError.message.includes('RemoteAuth.zip')) {
                addLog('WARN', 'Erro do RemoteAuth.zip durante inicialização (não crítico). Continuando...');
                // Não encerrar o cliente por esse erro
                return;
            }
            addLog('ERROR', `Erro ao inicializar cliente WhatsApp: ${initError.message}`);
            if (initError.stack) {
                addLog('ERROR', `Stack: ${initError.stack.split('\n').slice(0, 3).join('\n')}`);
            }
        });
    } catch (error) {
        // Se o erro for relacionado ao RemoteAuth.zip, tentar continuar
        if (error.message && error.message.includes('RemoteAuth.zip')) {
            addLog('WARN', 'Erro do RemoteAuth.zip durante inicialização (não crítico). Continuando...');
            // Não encerrar o cliente por esse erro
        } else {
            addLog('ERROR', `Erro ao inicializar cliente WhatsApp: ${error.message}`);
            client = null;
            serverRunning = false;
            isReady = false;
            currentQR = null;
            throw error;
        }
    }
}

// Endpoint para enviar imagem
app.post('/send-image', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { imagePath, caption } = req.body;

        if (!imagePath) {
            return res.status(400).json({
                success: false,
                error: 'Caminho da imagem não fornecido'
            });
        }

        // Verificar se o arquivo existe
        if (!fs.existsSync(imagePath)) {
            return res.status(404).json({
                success: false,
                error: `Arquivo não encontrado: ${imagePath}`
            });
        }

        // Ler a imagem
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // Determinar o tipo MIME baseado na extensão
        const ext = path.extname(imagePath).toLowerCase();
        let mimeType = 'image/jpeg';
        if (ext === '.png') {
            mimeType = 'image/png';
        } else if (ext === '.gif') {
            mimeType = 'image/gif';
        }

        const media = new MessageMedia(mimeType, base64Image, path.basename(imagePath));

        // Usar a legenda recebida (já vem completa do Python)
        // Se não houver legenda, usar apenas o link padrão
        const finalCaption = caption || `Compre no WhatsApp - ${WHATSAPP_LINK}`;

        // Enviar mensagem
        console.log(`📤 Enviando imagem: ${path.basename(imagePath)} para ${WHATSAPP_NUMBER}`);
        const chat = await client.getChatById(WHATSAPP_NUMBER);
        await chat.sendMessage(media, { caption: finalCaption });

        console.log(`✅ Imagem enviada com sucesso: ${path.basename(imagePath)}`);

        res.json({
            success: true,
            message: 'Imagem enviada com sucesso'
        });

    } catch (error) {
        console.error('❌ Erro ao enviar imagem:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint de saúde
app.get('/health', (req, res) => {
    res.json({
        status: isReady ? 'ready' : 'not-ready',
        message: isReady ? 'Cliente WhatsApp pronto' : 'Aguardando autenticação',
        number: WHATSAPP_NUMBER
    });
});

// Endpoint para obter status
app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        number: WHATSAPP_NUMBER,
        link: WHATSAPP_LINK
    });
});

app.get('/server-status', (req, res) => {
    res.json({
        success: true,
        running: serverRunning,
        ready: isReady,
        hasQR: Boolean(currentQR),
        number: isReady ? WHATSAPP_NUMBER : null,
        link: WHATSAPP_LINK
    });
});

app.get('/qr-code', (req, res) => {
    res.json({
        success: true,
        hasQR: Boolean(currentQR),
        qr: currentQR || null
    });
});

app.get('/logs', (req, res) => {
    const limit = Math.min(parseInt(req.query.limit, 10) || 100, MAX_SERVER_LOGS);
    const logs = serverLogs.slice(-limit);
    res.json({
        success: true,
        logs
    });
});

app.post('/logout', async (req, res) => {
    if (!client) {
        return res.status(400).json({
            success: false,
            error: 'Servidor não está em execução.'
        });
    }
    
    try {
        await client.logout();
        addLog('LOGOUT', 'Logout solicitado via API.');
        await stopWhatsAppClient();
        initializeWhatsApp();
        res.json({
            success: true,
            message: 'Logout realizado. Escaneie o novo QR Code para conectar.'
        });
    } catch (error) {
        addLog('ERROR', `Erro ao fazer logout: ${error.message}`);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/server-control', async (req, res) => {
    const action = req.body?.action;
    
    if (action === 'start') {
        if (serverRunning && client) {
            return res.json({
                success: false,
                error: 'Servidor já está em execução.'
            });
        }
        
        try {
            initializeWhatsApp();
            res.json({
                success: true,
                message: 'Servidor iniciado. Aguarde o QR Code para conectar.'
            });
        } catch (error) {
            addLog('ERROR', `Erro ao iniciar servidor via API: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    } else if (action === 'stop') {
        if (!client && !serverRunning) {
            return res.json({
                success: false,
                error: 'Servidor já está parado.'
            });
        }
        
        try {
            await stopWhatsAppClient();
            addLog('INFO', 'Servidor parado via API.');
            res.json({
                success: true,
                message: 'Servidor parado com sucesso.'
            });
        } catch (error) {
            addLog('ERROR', `Erro ao parar servidor via API: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    } else {
        res.status(400).json({
            success: false,
            error: 'Ação inválida. Use "start" ou "stop".'
        });
    }
});

// Cache para grupos e contatos
let groupsCache = null;
let contactsCache = null;
let groupsCacheTimestamp = null;
let contactsCacheTimestamp = null;
const CACHE_DURATION = 10 * 60 * 1000; // 10 minutos (aumentado para reduzir consultas)
const MAX_GROUPS = 500; // Reduzido de 1000 para 500
const MAX_CONTACTS = 500; // Limite para contatos também

// Endpoint para listar grupos
app.get('/list-groups', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        // Verificar cache
        const now = Date.now();
        if (groupsCache && groupsCacheTimestamp && (now - groupsCacheTimestamp) < CACHE_DURATION) {
            console.log('📋 Retornando grupos do cache...');
            return res.json({
                success: true,
                count: groupsCache.length,
                groups: groupsCache,
                cached: true
            });
        }

        console.log('📋 Listando grupos do WhatsApp... (pode levar alguns segundos)');
        
        // Limitar tempo de execução (aumentado para 90 segundos)
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout ao listar grupos (90s)')), 90000)
        );
        
        console.log('⏳ Aguardando resposta do WhatsApp...');
        const startTime = Date.now();
        
        const getChatsPromise = client.getChats();
        const chats = await Promise.race([getChatsPromise, timeoutPromise]);
        
        const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`✅ Chats recebidos em ${elapsedTime}s. Total: ${chats.length} chat(s)`);
        
        const groups = [];
        let processed = 0;
        let totalChats = chats.length;
        
        console.log(`🔄 Processando ${totalChats} chat(s) para encontrar grupos...`);

        // Processar em lotes menores com pausas maiores
        for (let i = 0; i < chats.length; i++) {
            const chat = chats[i];
            
            if (chat.isGroup && processed < MAX_GROUPS) {
                try {
                    const participants = chat.participants ? chat.participants.length : 0;
                    groups.push({
                        id: chat.id._serialized,
                        name: chat.name || 'Sem nome',
                        participants: participants,
                        isGroup: true
                    });
                    processed++;
                    
                    // Log de progresso a cada 50 grupos
                    if (processed % 50 === 0) {
                        console.log(`📊 Progresso: ${processed} grupo(s) encontrado(s) de ${i + 1}/${totalChats} chat(s) processado(s)`);
                    }
                } catch (err) {
                    // Silenciar erros individuais para não sobrecarregar logs
                    if (processed === 0) {
                        console.warn(`⚠️ Erro ao processar grupo: ${err.message}`);
                    }
                }
            }
            
            // Pausa maior a cada 25 grupos para reduzir carga de CPU
            if (processed % 25 === 0 && processed > 0) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Pausa ainda maior a cada 100 grupos
            if (processed % 100 === 0 && processed > 0) {
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }
        
        console.log(`✅ Processamento concluído: ${groups.length} grupo(s) encontrado(s) de ${totalChats} chat(s)`);

        // Ordenar por nome
        groups.sort((a, b) => a.name.localeCompare(b.name));

        // Atualizar cache
        groupsCache = groups;
        groupsCacheTimestamp = now;

        console.log(`✅ ${groups.length} grupo(s) encontrado(s)`);

        res.json({
            success: true,
            count: groups.length,
            groups: groups,
            cached: false
        });

    } catch (error) {
        console.error('❌ Erro ao listar grupos:', error.message);
        console.error('📊 Detalhes do erro:', {
            name: error.name,
            message: error.message,
            stack: error.stack?.split('\n').slice(0, 3).join('\n')
        });
        
        // Se for timeout, sugerir tentar novamente
        if (error.message.includes('Timeout')) {
            addLog('ERROR', `Timeout ao listar grupos. O WhatsApp pode estar lento. Tente novamente em alguns segundos.`);
        }
        
        res.status(500).json({
            success: false,
            error: error.message,
            suggestion: error.message.includes('Timeout') 
                ? 'O WhatsApp está demorando para responder. Tente novamente em alguns segundos.' 
                : 'Verifique se o cliente WhatsApp está conectado e funcionando.'
        });
    }
});

// Endpoint para salvar grupos em arquivo
app.get('/save-groups', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        console.log('📋 Listando e salvando grupos do WhatsApp...');
        const chats = await client.getChats();
        const groups = [];

        for (const chat of chats) {
            if (chat.isGroup) {
                try {
                    const participants = chat.participants ? chat.participants.length : 0;
                    groups.push({
                        id: chat.id._serialized,
                        name: chat.name || 'Sem nome',
                        participants: participants,
                        isGroup: true,
                        timestamp: new Date().toISOString()
                    });
                } catch (err) {
                    console.warn(`⚠️ Erro ao processar grupo: ${err.message}`);
                }
            }
        }

        // Ordenar por nome
        groups.sort((a, b) => a.name.localeCompare(b.name));

        // Salvar em arquivo JSON
        const groupsFile = './whatsapp-groups.json';
        fs.writeFileSync(groupsFile, JSON.stringify({
            lastUpdate: new Date().toISOString(),
            count: groups.length,
            groups: groups
        }, null, 2), 'utf-8');

        console.log(`✅ ${groups.length} grupo(s) salvos em ${groupsFile}`);

        res.json({
            success: true,
            count: groups.length,
            file: groupsFile,
            groups: groups
        });

    } catch (error) {
        console.error('❌ Erro ao salvar grupos:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint para enviar imagem para grupo
app.post('/send-image-to-group', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { groupId, imagePath, caption } = req.body;

        if (!groupId) {
            return res.status(400).json({
                success: false,
                error: 'ID do grupo não fornecido'
            });
        }

        if (!imagePath) {
            return res.status(400).json({
                success: false,
                error: 'Caminho da imagem não fornecido'
            });
        }

        // Verificar se o arquivo existe
        if (!fs.existsSync(imagePath)) {
            return res.status(404).json({
                success: false,
                error: `Arquivo não encontrado: ${imagePath}`
            });
        }

        // Ler a imagem
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // Determinar o tipo MIME
        const ext = path.extname(imagePath).toLowerCase();
        let mimeType = 'image/jpeg';
        if (ext === '.png') {
            mimeType = 'image/png';
        } else if (ext === '.gif') {
            mimeType = 'image/gif';
        }

        const media = new MessageMedia(mimeType, base64Image, path.basename(imagePath));

        // Usar a legenda recebida ou o link padrão
        const finalCaption = caption || `Compre no WhatsApp - ${WHATSAPP_LINK}`;

        // Enviar mensagem para o grupo
        console.log(`📤 Enviando imagem para grupo ${groupId}: ${path.basename(imagePath)}`);
        const chat = await client.getChatById(groupId);
        await chat.sendMessage(media, { caption: finalCaption });

        console.log(`✅ Imagem enviada com sucesso para o grupo: ${chat.name}`);

        res.json({
            success: true,
            message: 'Imagem enviada com sucesso',
            groupName: chat.name
        });

    } catch (error) {
        console.error('❌ Erro ao enviar imagem para grupo:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint para enviar apenas texto para grupo
app.post('/send-text-to-group', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { groupId, text } = req.body;

        if (!groupId) {
            return res.status(400).json({
                success: false,
                error: 'ID do grupo não fornecido'
            });
        }

        if (!text) {
            return res.status(400).json({
                success: false,
                error: 'Texto não fornecido'
            });
        }

        // Enviar mensagem de texto para o grupo
        console.log(`📤 Enviando texto para grupo ${groupId}`);
        const chat = await client.getChatById(groupId);
        await chat.sendMessage(text);

        console.log(`✅ Texto enviado com sucesso para o grupo: ${chat.name}`);

        res.json({
            success: true,
            message: 'Texto enviado com sucesso',
            groupName: chat.name
        });

    } catch (error) {
        console.error('❌ Erro ao enviar texto para grupo:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Função auxiliar para esperar ACK (entrega) de uma mensagem
function waitForAck(message, timeoutMs = 20000) {
    return new Promise((resolve) => {
        let resolved = false;
        let initialAck = typeof message.ack === 'number' ? message.ack : null;
        let ackChanged = false; // Flag para verificar se ACK mudou
        const MIN_WAIT_TIME = 5000; // Aguardar pelo menos 5 segundos antes de considerar entregue
        const startTime = Date.now();

        const messageId = message.id && message.id._serialized ? message.id._serialized : 
                         (message.id ? String(message.id) : null);

        if (!messageId) {
            console.log(`⚠️ Não foi possível obter ID da mensagem, considerando não entregue`);
            return resolve({ delivered: false, ack: null });
        }

        console.log(`⏳ Aguardando confirmação de entrega (dois ticks) para mensagem ID: ${messageId}`);
        console.log(`   ACK inicial: ${initialAck} (0=pendente, 1=servidor/um tick, 2=entregue/dois ticks, 3=lido)`);
        console.log(`   Aguardando pelo menos ${MIN_WAIT_TIME/1000}s e até ${timeoutMs/1000}s...`);

        // Handler para evento de ACK
        function onAck(msg, ack) {
            try {
                if (resolved) return;
                
                const msgId = msg.id && msg.id._serialized ? msg.id._serialized : 
                             (msg.id ? String(msg.id) : null);
                
                if (!msgId) return;

                // Comparar IDs (pode ser string ou objeto)
                const msgIdStr = String(msgId);
                const messageIdStr = String(messageId);
                
                // Verificar se é a mesma mensagem (comparação mais flexível)
                const isSameMessage = msgIdStr === messageIdStr || 
                                     msgIdStr.includes(messageIdStr) || 
                                     messageIdStr.includes(msgIdStr);
                
                if (isSameMessage) {
                    const elapsed = Date.now() - startTime;
                    console.log(`📨 ACK recebido para mensagem: ack=${ack}, msgId=${msgIdStr}, tempo=${(elapsed/1000).toFixed(1)}s`);
                    
                    // ack: 0=pendente, 1=servidor (um tick), 2=entregue (dois ticks), 3=lido (dois ticks azuis)
                    if (typeof ack === 'number' && ack >= 2) {
                        // ACK >= 2 = entregue ao dispositivo (dois ticks) ou lido
                        // Verificar se ACK mudou de 0/1 para 2+ (confirmação real de entrega)
                        if (initialAck === 0 || initialAck === 1 || initialAck === null) {
                            ackChanged = true;
                        }
                        
                        // Aguardar tempo mínimo antes de considerar entregue
                        const elapsedTime = Date.now() - startTime;
                        if (elapsedTime >= MIN_WAIT_TIME) {
                            // Se passou o tempo mínimo E ACK >= 2, considerar entregue
                            if (ackChanged || (initialAck === null && ack >= 2)) {
                                resolved = true;
                                client.removeListener('message_ack', onAck);
                                const ackStatus = ack === 2 ? 'entregue (dois ticks)' : ack === 3 ? 'lido (dois ticks azuis)' : 'entregue';
                                console.log(`✅ Mensagem confirmada como ENTREGUE (ack=${ack}=${ackStatus}, tempo=${(elapsedTime/1000).toFixed(1)}s)`);
                                resolve({ delivered: true, ack });
                            } else {
                                console.log(`⏳ ACK=${ack} mas ainda aguardando tempo mínimo...`);
                            }
                        } else {
                            console.log(`⏳ ACK=${ack} recebido mas aguardando tempo mínimo (${(elapsedTime/1000).toFixed(1)}s/${MIN_WAIT_TIME/1000}s)...`);
                        }
                    } else if (typeof ack === 'number' && ack === 1) {
                        // ACK 1 = apenas enviado ao servidor (um tick), ainda não entregue
                        console.log(`⏳ Mensagem enviada ao servidor mas ainda não entregue (ack=1, um tick apenas)`);
                    } else if (typeof ack === 'number' && ack === 0) {
                        // ACK 0 = pendente, ainda não enviado
                        console.log(`⏳ Mensagem pendente (ack=0)`);
                    }
                }
            } catch (e) {
                console.error(`❌ Erro no handler de ACK: ${e.message}`);
            }
        }

        client.on('message_ack', onAck);

        // Timeout: se não tiver ack >=2 confirmado em X segundos, consideramos não entregue
        setTimeout(() => {
            if (!resolved) {
                resolved = true;
                client.removeListener('message_ack', onAck);
                const finalAck = typeof message.ack === 'number' ? message.ack : null;
                const elapsed = Date.now() - startTime;
                console.log(`⏰ Timeout após ${(elapsed/1000).toFixed(1)}s. Mensagem NÃO confirmada como entregue`);
                console.log(`   ACK final: ${finalAck} (0=pendente, 1=servidor/um tick, 2+=entregue/dois ticks)`);
                console.log(`   ACK mudou para >=2: ${ackChanged}`);
                resolve({ 
                    delivered: false, 
                    ack: finalAck
                });
            }
        }, timeoutMs);
    });
}

// Endpoint para enviar apenas texto para contato individual
app.post('/send-text-to-contact', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { contactId, text } = req.body;

        if (!contactId) {
            return res.status(400).json({
                success: false,
                error: 'ID do contato não fornecido'
            });
        }

        if (!text) {
            return res.status(400).json({
                success: false,
                error: 'Texto não fornecido'
            });
        }

        // Formatar ID do contato (adicionar @c.us se necessário)
        const formattedId = contactId.includes('@') ? contactId : `${contactId}@c.us`;

        // Enviar mensagem de texto para o contato
        console.log(`📤 Enviando texto para contato ${formattedId}`);
        const chat = await client.getChatById(formattedId);
        const sentMessage = await chat.sendMessage(text);

        const messageId = sentMessage.id ? sentMessage.id._serialized || sentMessage.id : null;

        // Esperar ACK de entrega (dois ticks) com timeout de 20 segundos
        // Aguarda pelo menos 5 segundos para garantir que é realmente dois ticks
        console.log(`⏳ Aguardando confirmação de entrega (dois ticks)...`);
        const ackResult = await waitForAck(sentMessage, 20000);

        if (ackResult.delivered) {
            const ackStatus = ackResult.ack === 2 ? 'entregue (dois ticks)' : ackResult.ack === 3 ? 'lido (dois ticks azuis)' : 'entregue';
            console.log(`✅ Texto entregue para ${formattedId} | Status: ${ackStatus} (ack: ${ackResult.ack})`);
        } else {
            const ackDesc = ackResult.ack === 0 ? 'pendente' : ackResult.ack === 1 ? 'servidor/um tick' : 'desconhecido';
            console.log(`⚠️ Texto enviado para ${formattedId} mas não confirmado como entregue (ack: ${ackResult.ack || 'null'} = ${ackDesc})`);
        }

        res.json({
            success: true,
            message: 'Texto enviado',
            contactId: formattedId,
            messageId: messageId,
            ack: ackResult.ack,
            delivered: ackResult.delivered
        });

    } catch (error) {
        console.error('❌ Erro ao enviar texto para contato:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint para enviar imagem com legenda para contato individual
app.post('/send-image-to-contact', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { contactId, imagePath, caption } = req.body;

        if (!contactId) {
            return res.status(400).json({
                success: false,
                error: 'ID do contato não fornecido'
            });
        }

        if (!imagePath) {
            return res.status(400).json({
                success: false,
                error: 'Caminho da imagem não fornecido'
            });
        }

        // Verificar se o arquivo existe
        if (!fs.existsSync(imagePath)) {
            return res.status(404).json({
                success: false,
                error: `Arquivo não encontrado: ${imagePath}`
            });
        }

        // Formatar ID do contato (adicionar @c.us se necessário)
        const formattedId = contactId.includes('@') ? contactId : `${contactId}@c.us`;

        // Ler a imagem
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');
        
        // Determinar o tipo MIME
        const ext = path.extname(imagePath).toLowerCase();
        let mimeType = 'image/jpeg';
        if (ext === '.png') {
            mimeType = 'image/png';
        } else if (ext === '.gif') {
            mimeType = 'image/gif';
        }

        const media = new MessageMedia(mimeType, base64Image, path.basename(imagePath));

        // Usar a legenda recebida ou string vazia
        const finalCaption = caption || '';

        // Enviar mensagem para o contato
        console.log(`📤 Enviando imagem para contato ${formattedId}: ${path.basename(imagePath)}`);
        const chat = await client.getChatById(formattedId);
        await chat.sendMessage(media, { caption: finalCaption });

        console.log(`✅ Imagem enviada com sucesso para o contato: ${formattedId}`);

        res.json({
            success: true,
            message: 'Imagem enviada com sucesso',
            contactId: formattedId
        });

    } catch (error) {
        console.error('❌ Erro ao enviar imagem para contato:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint para enviar mensagem para múltiplos destinatários (batch)
app.post('/send-batch', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { 
            recipients, 
            imagePath, 
            text, 
            delayFirstMin = 25000, 
            delayFirstMax = 35000,
            delaySubsequentMin = 30000,
            delaySubsequentMax = 45000
        } = req.body;

        if (!recipients || !Array.isArray(recipients) || recipients.length === 0) {
            return res.status(400).json({
                success: false,
                error: 'Lista de destinatários não fornecida ou vazia'
            });
        }

        if (!imagePath && !text) {
            return res.status(400).json({
                success: false,
                error: 'É necessário fornecer imagem ou texto (ou ambos)'
            });
        }

        // Validar e normalizar delays (em milissegundos)
        const firstMin = Math.max(1000, parseInt(delayFirstMin) || 25000);
        const firstMax = Math.max(firstMin, parseInt(delayFirstMax) || 35000);
        const subsequentMin = Math.max(1000, parseInt(delaySubsequentMin) || 30000);
        const subsequentMax = Math.max(subsequentMin, parseInt(delaySubsequentMax) || 45000);
        
        console.log(`⏱️ Delay configurado (simulação humana):`);
        console.log(`   • Primeira mensagem: ${firstMin/1000}s - ${firstMax/1000}s`);
        console.log(`   • Mensagens subsequentes: ${subsequentMin/1000}s - ${subsequentMax/1000}s`);
        console.log(`🎲 Usando aleatoriedade máxima para parecer mais humano`);

        // Verificar se a imagem existe (se fornecida)
        let media = null;
        if (imagePath) {
            if (!fs.existsSync(imagePath)) {
                return res.status(404).json({
                    success: false,
                    error: `Arquivo não encontrado: ${imagePath}`
                });
            }

            // Ler a imagem
            const imageBuffer = fs.readFileSync(imagePath);
            const base64Image = imageBuffer.toString('base64');
            
            // Determinar o tipo MIME
            const ext = path.extname(imagePath).toLowerCase();
            let mimeType = 'image/jpeg';
            if (ext === '.png') {
                mimeType = 'image/png';
            } else if (ext === '.gif') {
                mimeType = 'image/gif';
            }

            media = new MessageMedia(mimeType, base64Image, path.basename(imagePath));
        }

        const results = {
            success: [],
            failed: [],
            total: recipients.length
        };

        // Enviar para cada destinatário
        for (let i = 0; i < recipients.length; i++) {
            const recipient = recipients[i];
            // Inicializar formattedId fora do try para estar disponível no catch
            let formattedId = recipient.id;
            
            try {
                console.log(`📤 Processando destinatário ${i + 1}/${recipients.length}: ${recipient.name || recipient.id} (ID: ${recipient.id}, Tipo: ${recipient.type || 'contact'})`);
                
                // Formatar ID (adicionar sufixo se necessário)
                formattedId = recipient.id;
                if (!formattedId.includes('@')) {
                    if (recipient.type === 'group') {
                        formattedId = `${formattedId}@g.us`;
                    } else {
                        // Para contatos, usar o número diretamente com @c.us
                        // O WhatsApp criará o LID automaticamente quando necessário
                        formattedId = `${recipient.id}@c.us`;
                    }
                }

                // Obter chat e enviar mensagem
                let chat;
                
                // Para contatos, tentar múltiplas abordagens
                if (recipient.type === 'contact' && !recipient.id.includes('@')) {
                    let chatFound = false;
                    
                    // Abordagem 1: Tentar obter número ID e usar para criar chat
                    try {
                        console.log(`🔍 Verificando número ${recipient.id}...`);
                        const numberIdResult = await client.getNumberId(recipient.id);
                        
                        // getNumberId pode retornar objeto ou string
                        let actualNumberId;
                        if (typeof numberIdResult === 'object' && numberIdResult !== null) {
                            // Se for objeto, extrair o ID corretamente
                            if (numberIdResult._serialized) {
                                actualNumberId = numberIdResult._serialized.replace('@c.us', '').replace('@g.us', '');
                            } else if (numberIdResult.user) {
                                actualNumberId = numberIdResult.user;
                            } else if (numberIdResult.id) {
                                actualNumberId = numberIdResult.id;
                            } else {
                                actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                            }
                        } else {
                            actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                        }
                        
                        if (actualNumberId && actualNumberId !== 'null' && actualNumberId !== 'undefined') {
                            formattedId = `${actualNumberId}@c.us`;
                            console.log(`✅ Número ID obtido: ${formattedId}`);
                        } else {
                            formattedId = `${recipient.id}@c.us`;
                        }
                    } catch (numberIdError) {
                        console.log(`⚠️ getNumberId falhou, usando número diretamente`);
                        formattedId = `${recipient.id}@c.us`;
                    }
                    
                    // Tentar obter chat diretamente
                    try {
                        chat = await client.getChatById(formattedId);
                        chatFound = true;
                        console.log(`✅ Chat encontrado: ${formattedId}`);
                    } catch (chatError) {
                        console.log(`⚠️ getChatById falhou com ${formattedId}: ${chatError.message}`);
                        
                        // Abordagem 2: Procurar chat existente na lista de chats
                        try {
                            console.log(`🔍 Procurando chat na lista de chats existentes...`);
                            const chats = await client.getChats();
                            
                            // Tentar encontrar o chat usando diferentes formatos
                            let foundChat = chats.find(c => {
                                const chatId = c.id._serialized;
                                // Pode estar em formato diferente
                                const cleanId = recipient.id.replace('@c.us', '').replace('@g.us', '');
                                return chatId === formattedId || 
                                       chatId === `${recipient.id}@c.us` ||
                                       chatId.includes(cleanId);
                            });
                            
                            if (foundChat) {
                                chat = foundChat;
                                chatFound = true;
                                console.log(`✅ Chat encontrado na lista: ${foundChat.id._serialized}`);
                            } else {
                                // Abordagem 3: Tentar criar chat enviando uma mensagem de teste vazia primeiro
                                // Mas como não temos sendMessage direto, vamos tentar o formattedId original
                                formattedId = `${recipient.id}@c.us`;
                                try {
                                    chat = await client.getChatById(formattedId);
                                    chatFound = true;
                                } catch (lastTry) {
                                    throw new Error(`Não foi possível criar ou encontrar chat para ${recipient.id}. O número pode precisar estar salvo nos seus contatos primeiro.`);
                                }
                            }
                        } catch (searchError) {
                            console.log(`⚠️ Busca de chat falhou: ${searchError.message}`);
                            throw new Error(`Não foi possível acessar o chat para ${recipient.id}. O número pode não estar registrado no WhatsApp ou não estar salvo nos seus contatos. Erro original: ${chatError.message}`);
                        }
                    }
                } else {
                    // Para grupos ou IDs que já têm @, usar método normal
                    chat = await client.getChatById(formattedId);
                }
                
                // Enviar mensagem usando o chat obtido
                if (media && text) {
                    await chat.sendMessage(media, { caption: text });
                } else if (media) {
                    await chat.sendMessage(media);
                } else if (text) {
                    await chat.sendMessage(text);
                }

                results.success.push({
                    id: formattedId,
                    name: recipient.name || formattedId,
                    type: recipient.type || 'contact'
                });

                console.log(`✅ Mensagem enviada para ${recipient.name || formattedId} (${i + 1}/${recipients.length})`);

                // Delay aleatório entre envios para simular comportamento humano
                if (i < recipients.length - 1) {
                    // Primeira mensagem usa delayFirst, subsequentes usam delaySubsequent
                    const isFirstMessage = i === 0;
                    const minDelay = isFirstMessage ? firstMin : subsequentMin;
                    const maxDelay = isFirstMessage ? firstMax : subsequentMax;
                    
                    // Gerar delay aleatório com máxima aleatoriedade
                    // Usa Math.random() com precisão decimal para maior variabilidade
                    const randomFactor = Math.random(); // 0.0 a 1.0
                    const delayRange = maxDelay - minDelay;
                    const randomDelay = Math.floor(minDelay + (randomFactor * delayRange));
                    
                    // Adicionar variação extra de 0-500ms para mais aleatoriedade
                    const extraRandomness = Math.floor(Math.random() * 500);
                    const finalDelay = randomDelay + extraRandomness;
                    
                    const delaySeconds = (finalDelay / 1000).toFixed(2);
                    const messageType = isFirstMessage ? 'primeira' : 'subsequente';
                    console.log(`⏱️ [${messageType}] Aguardando ${delaySeconds}s antes do próximo envio... (aleatório: ${(randomFactor * 100).toFixed(1)}%)`);
                    await new Promise(resolve => setTimeout(resolve, finalDelay));
                }

            } catch (error) {
                const errorMessage = error.message || error.toString();
                results.failed.push({
                    id: recipient.id,
                    name: recipient.name || recipient.id,
                    type: recipient.type || 'contact',
                    error: errorMessage
                });
                console.error(`❌ Erro ao enviar para ${recipient.name || recipient.id} (${recipient.id}): ${errorMessage}`);
                console.error(`   Tipo: ${recipient.type || 'contact'}, ID formatado tentado: ${formattedId || 'N/A'}`);
            }
        }

        res.json({
            success: true,
            message: `Envio concluído: ${results.success.length} sucesso, ${results.failed.length} falhas`,
            results: results
        });

    } catch (error) {
        console.error('❌ Erro ao enviar em lote:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint para preparar/salvar contatos (força criação do LID)
app.post('/prepare-contacts', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { numbers } = req.body;

        if (!numbers || !Array.isArray(numbers) || numbers.length === 0) {
            return res.status(400).json({
                success: false,
                error: 'Lista de números não fornecida ou vazia'
            });
        }

        const results = {
            prepared: [],
            failed: [],
            total: numbers.length
        };

        console.log(`🔄 Preparando ${numbers.length} contato(s)...`);

        for (let i = 0; i < numbers.length; i++) {
            const number = numbers[i];
            try {
                // Formatar número (remover @c.us se existir)
                const cleanNumber = number.replace('@c.us', '').replace('@g.us', '');
                const formattedId = `${cleanNumber}@c.us`;

                console.log(`🔍 Preparando contato ${i + 1}/${numbers.length}: ${cleanNumber}`);

                // Abordagem 1: Tentar obter o número ID (isso força a criação do LID)
                try {
                    const numberIdResult = await client.getNumberId(cleanNumber);
                    
                    // getNumberId pode retornar objeto ou string - extrair ID corretamente
                    let actualNumberId;
                    if (typeof numberIdResult === 'object' && numberIdResult !== null) {
                        if (numberIdResult._serialized) {
                            actualNumberId = numberIdResult._serialized.replace('@c.us', '').replace('@g.us', '');
                        } else if (numberIdResult.user) {
                            actualNumberId = numberIdResult.user;
                        } else if (numberIdResult.id) {
                            actualNumberId = numberIdResult.id;
                        } else {
                            actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                        }
                    } else {
                        actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                    }
                    
                    if (actualNumberId && actualNumberId !== 'null' && actualNumberId !== 'undefined') {
                        // Número registrado, criar chat para "ativar" o contato
                        const chatId = `${actualNumberId}@c.us`;
                        try {
                            const chat = await client.getChatById(chatId);
                            results.prepared.push({
                                number: cleanNumber,
                                chatId: chatId,
                                method: 'numberId'
                            });
                            console.log(`✅ Contato ${cleanNumber} preparado via numberId: ${chatId}`);
                        } catch (chatError) {
                            // Mesmo com numberId, não conseguiu criar chat
                            results.failed.push({
                                number: cleanNumber,
                                error: `Chat não criado: ${chatError.message}`
                            });
                        }
                    } else {
                        results.failed.push({
                            number: cleanNumber,
                            error: 'Número não registrado no WhatsApp'
                        });
                    }
                } catch (numberIdError) {
                    // Abordagem 2: Tentar criar chat diretamente (às vezes funciona mesmo sem numberId)
                    try {
                        const chat = await client.getChatById(formattedId);
                        // Se chegou aqui, conseguiu criar o chat
                        results.prepared.push({
                            number: cleanNumber,
                            chatId: formattedId,
                            method: 'direct'
                        });
                        console.log(`✅ Contato ${cleanNumber} preparado diretamente`);
                    } catch (chatError) {
                        // Não conseguiu criar chat de forma alguma
                        results.failed.push({
                            number: cleanNumber,
                            error: `Não foi possível preparar: ${chatError.message}`
                        });
                        console.log(`❌ Falha ao preparar ${cleanNumber}: ${chatError.message}`);
                    }
                }

                // Pequeno delay para não sobrecarregar
                if (i < numbers.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                }

            } catch (error) {
                results.failed.push({
                    number: number,
                    error: error.message
                });
                console.error(`❌ Erro ao preparar ${number}: ${error.message}`);
            }
        }

        res.json({
            success: true,
            message: `Preparação concluída: ${results.prepared.length} preparados, ${results.failed.length} falharam`,
            results: results
        });

    } catch (error) {
        console.error('❌ Erro ao preparar contatos:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Endpoint de teste para enviar mensagem simples
app.post('/test-send', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        const { number, message } = req.body;
        
        if (!number) {
            return res.status(400).json({
                success: false,
                error: 'Número não fornecido'
            });
        }

        const testMessage = message || 'oi';
        console.log(`🧪 TESTE: Enviando mensagem "${testMessage}" para ${number}...`);

        // Limpar número (remover @c.us se existir)
        const cleanNumber = number.replace('@c.us', '').replace('@g.us', '');
        
        let formattedId = `${cleanNumber}@c.us`;
        let chat = null;
        let attempts = [];

        // Tentativa 1: Usar número direto
        try {
            console.log(`🧪 Tentativa 1: getChatById(${formattedId})`);
            chat = await client.getChatById(formattedId);
            attempts.push({ method: 'getChatById direto', success: true });
        } catch (error1) {
            attempts.push({ method: 'getChatById direto', success: false, error: error1.message });
            console.log(`❌ Tentativa 1 falhou: ${error1.message}`);

            // Tentativa 2: Obter número ID primeiro
            try {
                console.log(`🧪 Tentativa 2: getNumberId(${cleanNumber})`);
                const numberIdResult = await client.getNumberId(cleanNumber);
                
                // getNumberId pode retornar objeto ou string
                let actualNumberId;
                if (typeof numberIdResult === 'object' && numberIdResult !== null) {
                    // Se for objeto, pode ter propriedades como _serialized, user, server, etc.
                    if (numberIdResult._serialized) {
                        actualNumberId = numberIdResult._serialized.replace('@c.us', '').replace('@g.us', '');
                    } else if (numberIdResult.user) {
                        actualNumberId = numberIdResult.user;
                    } else if (numberIdResult.id) {
                        actualNumberId = numberIdResult.id;
                    } else {
                        // Tentar usar o próprio objeto convertido para string
                        actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                    }
                } else {
                    actualNumberId = String(numberIdResult).replace('@c.us', '').replace('@g.us', '');
                }
                
                if (actualNumberId && actualNumberId !== 'null' && actualNumberId !== 'undefined') {
                    formattedId = `${actualNumberId}@c.us`;
                    console.log(`✅ Número ID obtido: ${formattedId} (do objeto: ${JSON.stringify(numberIdResult)})`);
                    chat = await client.getChatById(formattedId);
                    attempts.push({ method: 'getNumberId + getChatById', success: true, numberId: actualNumberId, rawResult: numberIdResult });
                } else {
                    attempts.push({ method: 'getNumberId', success: false, error: `Número ID inválido: ${actualNumberId}`, rawResult: numberIdResult });
                }
            } catch (error2) {
                attempts.push({ method: 'getNumberId', success: false, error: error2.message });
                console.log(`❌ Tentativa 2 falhou: ${error2.message}`);

                // Tentativa 3: Procurar na lista de chats
                try {
                    console.log(`🧪 Tentativa 3: Buscar na lista de chats`);
                    const chats = await client.getChats();
                    const foundChat = chats.find(c => {
                        const chatId = c.id._serialized;
                        return chatId === formattedId || 
                               chatId === `${cleanNumber}@c.us` ||
                               chatId.includes(cleanNumber);
                    });

                    if (foundChat) {
                        chat = foundChat;
                        attempts.push({ method: 'buscar na lista', success: true, chatId: foundChat.id._serialized });
                        console.log(`✅ Chat encontrado na lista: ${foundChat.id._serialized}`);
                    } else {
                        attempts.push({ method: 'buscar na lista', success: false, error: 'Chat não encontrado na lista' });
                    }
                } catch (error3) {
                    attempts.push({ method: 'buscar na lista', success: false, error: error3.message });
                    console.log(`❌ Tentativa 3 falhou: ${error3.message}`);
                }
            }
        }

        if (!chat) {
            return res.status(404).json({
                success: false,
                error: 'Não foi possível obter chat',
                attempts: attempts,
                info: 'O número pode não estar salvo nos seus contatos ou não estar registrado no WhatsApp'
            });
        }

        // Enviar mensagem
        console.log(`📤 Enviando mensagem via chat: ${chat.id._serialized}`);
        await chat.sendMessage(testMessage);
        
        console.log(`✅ TESTE: Mensagem enviada com sucesso!`);

        res.json({
            success: true,
            message: `Mensagem "${testMessage}" enviada com sucesso`,
            chatId: chat.id._serialized,
            formattedNumber: formattedId,
            attempts: attempts
        });

    } catch (error) {
        console.error('❌ TESTE: Erro ao enviar mensagem de teste:', error);
        res.status(500).json({
            success: false,
            error: error.message,
            stack: error.stack
        });
    }
});

// Endpoint para listar contatos
app.get('/list-contacts', async (req, res) => {
    try {
        if (!isReady || !client) {
            return res.status(503).json({
                success: false,
                error: 'Cliente WhatsApp não está pronto. Aguarde a autenticação.'
            });
        }

        // Verificar cache de contatos
        const now = Date.now();
        if (contactsCache && contactsCacheTimestamp && (now - contactsCacheTimestamp) < CACHE_DURATION) {
            console.log('📋 Retornando contatos do cache...');
            return res.json({
                success: true,
                count: contactsCache.length,
                contacts: contactsCache,
                cached: true
            });
        }

        console.log('📋 Listando contatos do WhatsApp... (pode levar alguns segundos)');
        
        // Limitar tempo de execução
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout ao listar contatos')), 45000)
        );
        
        const getContactsPromise = client.getContacts();
        const contacts = await Promise.race([getContactsPromise, timeoutPromise]);
        
        const contactsList = [];
        let processed = 0;

        // Processar em lotes com pausas para reduzir carga de CPU
        for (const contact of contacts) {
            if (contact.isUser && !contact.isGroup && processed < MAX_CONTACTS) {
                try {
                    contactsList.push({
                        id: contact.id._serialized,
                        name: contact.pushname || contact.name || contact.number || 'Sem nome',
                        number: contact.number || '',
                        isUser: contact.isUser
                    });
                    processed++;
                } catch (err) {
                    if (processed === 0) {
                        console.warn(`⚠️ Erro ao processar contato: ${err.message}`);
                    }
                }
            }
            
            // Pausa a cada 50 contatos para não sobrecarregar
            if (processed % 50 === 0 && processed > 0) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Pausa maior a cada 200 contatos
            if (processed % 200 === 0 && processed > 0) {
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }

        // Ordenar por nome
        contactsList.sort((a, b) => a.name.localeCompare(b.name));

        // Atualizar cache
        contactsCache = contactsList;
        contactsCacheTimestamp = now;

        console.log(`✅ ${contactsList.length} contato(s) encontrado(s)`);

        res.json({
            success: true,
            count: contactsList.length,
            contacts: contactsList,
            cached: false
        });

    } catch (error) {
        console.error('❌ Erro ao listar contatos:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Tratamento de erros não capturados
process.on('uncaughtException', (err) => {
    console.error('\n❌❌❌ ERRO NÃO CAPTURADO ❌❌❌\n');
    console.error('Erro:', err.message);
    console.error('Stack:', err.stack);
    console.error('\n═══════════════════════════════════════════════════════════\n');
    
    // Tratar erro específico do RemoteAuth.zip
    if (err.message && err.message.includes('RemoteAuth.zip')) {
        console.log('🔧 SOLUÇÃO PARA ERRO RemoteAuth.zip:\n');
        console.log('Este erro ocorre quando o RemoteAuth tenta criar um backup ZIP.');
        console.log('O diretório de backup será criado automaticamente.\n');
        
        // Tentar criar o diretório e continuar
        const backupDir = path.join(process.cwd(), 'whatsapp-auth-remote');
        try {
            if (!fs.existsSync(backupDir)) {
                fs.mkdirSync(backupDir, { recursive: true });
                console.log(`✅ Diretório criado: ${backupDir}`);
            }
            console.log('⚠️ Continuando execução apesar do erro...\n');
            return; // Não encerrar o processo
        } catch (mkdirError) {
            console.error('❌ Não foi possível criar o diretório:', mkdirError.message);
        }
    }
    
    console.log('O servidor será fechado devido a um erro crítico.\n');
    console.log('Pressione qualquer tecla para sair...\n');
    setTimeout(() => process.exit(1), 5000);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('\n❌❌❌ PROMISE REJEITADA ❌❌❌\n');
    console.error('Razão:', reason);
    console.error('\n═══════════════════════════════════════════════════════════\n');
});

// Inicializar WhatsApp
console.log('\n═══════════════════════════════════════════════════════════');
console.log('🚀 INICIANDO SERVIDOR WHATSAPP');
console.log('═══════════════════════════════════════════════════════════\n');

try {
    console.log('📋 Verificando configurações...');
    console.log(`   MongoDB URI: ${MONGODB_URI ? 'Configurado' : 'Não configurado'}`);
    console.log(`   MongoDB DB: ${MONGODB_DB_NAME}`);
    console.log(`   RemoteAuth: ${USE_REMOTE_AUTH ? 'Sim' : 'Não'}`);
    console.log(`   WhatsApp Number: ${WHATSAPP_NUMBER}\n`);
    
    console.log('🔄 Chamando initializeWhatsApp()...');
    initializeWhatsApp().then(() => {
        console.log('✅ initializeWhatsApp() concluído com sucesso');
    }).catch((err) => {
        console.error('\n❌❌❌ ERRO AO INICIALIZAR WHATSAPP (Promise) ❌❌❌\n');
        console.error('Erro:', err.message);
        console.error('Stack:', err.stack);
        console.error('\n═══════════════════════════════════════════════════════════\n');
    });
} catch (err) {
    console.error('\n❌❌❌ ERRO AO INICIALIZAR WHATSAPP (Sync) ❌❌❌\n');
    console.error('Erro:', err.message);
    console.error('Stack:', err.stack);
    console.error('\n═══════════════════════════════════════════════════════════\n');
    console.log('Verifique se todas as dependências estão instaladas:');
    console.log('  npm install\n');
    process.exit(1);
}

// Iniciar servidor
const PORT = process.env.PORT || 3001;

try {
    const server = app.listen(PORT, () => {
        console.log(`🌐 Servidor WhatsApp rodando na porta ${PORT}`);
        console.log(`📱 Aguardando autenticação do WhatsApp...`);
        console.log(`📞 Número de destino: ${WHATSAPP_NUMBER}`);
        console.log(`🔗 Link de compra: ${WHATSAPP_LINK}`);
        console.log(`\n💡 Acesse http://localhost:${PORT}/health para verificar o status\n`);
        addLog('INFO', `Servidor HTTP iniciado na porta ${PORT}.`);
    });

    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            console.error(`\n❌❌❌ ERRO: Porta ${PORT} já está em uso! ❌❌❌\n`);
            console.log(`═══════════════════════════════════════════════════════════`);
            console.log(`  SOLUÇÃO RÁPIDA:`);
            console.log(`═══════════════════════════════════════════════════════════\n`);
            console.log(`1. Execute: liberar-porta-3001.bat`);
            console.log(`   (Este script irá finalizar processos usando a porta 3001)\n`);
            console.log(`2. OU feche a janela do servidor WhatsApp anterior`);
            console.log(`   (Procure por janelas com "Servidor Flask" ou "WhatsApp")\n`);
            console.log(`3. OU execute no terminal:`);
            console.log(`   netstat -ano | findstr :3001`);
            console.log(`   taskkill /F /PID [NUMERO_DO_PID]\n`);
            console.log(`═══════════════════════════════════════════════════════════\n`);
            console.log(`⚠️  O servidor não pode iniciar enquanto a porta estiver em uso.\n`);
            console.log(`Aguardando 10 segundos antes de fechar...\n`);
            setTimeout(() => process.exit(1), 10000);
        } else {
            console.error(`\n❌ Erro ao iniciar servidor: ${err.message}\n`);
            console.error(`Stack: ${err.stack}\n`);
            console.log(`Aguardando 10 segundos antes de fechar...\n`);
            setTimeout(() => process.exit(1), 10000);
        }
    });
} catch (err) {
    console.error('\n❌❌❌ ERRO AO CRIAR SERVIDOR ❌❌❌\n');
    console.error('Erro:', err.message);
    console.error('Stack:', err.stack);
    console.error('\n═══════════════════════════════════════════════════════════\n');
    console.log('Aguardando 10 segundos antes de fechar...\n');
    setTimeout(() => process.exit(1), 10000);
}


