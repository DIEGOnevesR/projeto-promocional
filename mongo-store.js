/**
 * MongoDB Store para RemoteAuth do whatsapp-web.js
 */
const { MongoClient, ServerApiVersion } = require('mongodb');

class MongoStore {
    constructor(options = {}) {
        this.dbName = options.dbName || 'whatsapp-sessions';
        this.collectionName = options.collectionName || 'sessions';
        this.uri = options.uri || process.env.MONGODB_URI || process.env.MONGO_URI || 'mongodb://localhost:27017';
        this.client = null;
        this.db = null;
        this.collection = null;
        
        // Configurar opções do MongoDB (compatível com MongoDB Atlas)
        this.mongoOptions = {
            serverApi: {
                version: ServerApiVersion.v1,
                strict: true,
                deprecationErrors: true,
            },
            tls: true,
            tlsAllowInvalidCertificates: false,
            ...options.mongoOptions
        };
    }

    async connect() {
        if (this.client && this.client.topology && this.client.topology.isConnected()) {
            return;
        }

        try {
            console.log('🔍 Iniciando conexão com MongoDB...');
            console.log(`📡 URI: ${this.uri.replace(/\/\/([^:]+):([^@]+)@/, '//$1:***@')}`);
            console.log(`📦 Database: ${this.dbName}`);
            console.log(`📋 Collection: ${this.collectionName}`);
            
            // Criar cliente com opções SSL/TLS corretas para MongoDB Atlas
            const clientOptions = {
                serverApi: this.mongoOptions.serverApi,
                // Timeouts aumentados
                connectTimeoutMS: 60000,
                serverSelectionTimeoutMS: 60000,
                socketTimeoutMS: 60000,
                // Configurações de retry
                retryWrites: true,
                retryReads: true,
            };
            
            console.log('⏳ Criando cliente MongoDB...');
            this.client = new MongoClient(this.uri, clientOptions);
            
            console.log('⏳ Tentando conectar (timeout: 60s)...');
            const startTime = Date.now();
            
            // Conectar com timeout maior e mais informações
            await Promise.race([
                this.client.connect().then(() => {
                    const elapsed = Date.now() - startTime;
                    console.log(`✅ Cliente conectado em ${elapsed}ms`);
                }),
                new Promise((_, reject) => 
                    setTimeout(() => {
                        const elapsed = Date.now() - startTime;
                        reject(new Error(`Timeout ao conectar ao MongoDB após ${elapsed}ms`));
                    }, 60000)
                )
            ]);
            
            console.log('⏳ Acessando database...');
            this.db = this.client.db(this.dbName);
            this.collection = this.db.collection(this.collectionName);
            
            console.log('⏳ Criando índice...');
            // Criar índice para melhor performance
            await this.collection.createIndex({ sessionId: 1 }, { unique: true });
            
            console.log(`✅ Conectado ao MongoDB: ${this.dbName}/${this.collectionName}`);
            
            // Testar conexão com ping
            console.log('⏳ Testando conexão (ping)...');
            await this.db.admin().command({ ping: 1 });
            console.log('✅ Ping bem-sucedido!');
            
        } catch (error) {
            console.error('❌ Erro ao conectar ao MongoDB:');
            console.error(`   Tipo: ${error.constructor.name}`);
            console.error(`   Mensagem: ${error.message}`);
            if (error.code) {
                console.error(`   Código: ${error.code}`);
            }
            if (error.cause) {
                console.error(`   Causa: ${error.cause.message || error.cause}`);
            }
            
            // Informações adicionais para diagnóstico
            console.error('📋 Informações de diagnóstico:');
            console.error(`   URI configurada: ${this.uri ? 'Sim' : 'Não'}`);
            console.error(`   URI começa com mongodb+srv: ${this.uri.startsWith('mongodb+srv://')}`);
            
            if (this.client) {
                try {
                    await this.client.close();
                } catch (closeError) {
                    // Ignorar erro ao fechar
                }
                this.client = null;
            }
            throw error;
        }
    }

    async sessionExists(options) {
        await this.connect();
        const session = await this.collection.findOne({ sessionId: options.session });
        return !!session;
    }

    async save(options) {
        await this.connect();
        const sessionData = {
            sessionId: options.session,
            data: options.data,
            updatedAt: new Date(),
        };

        await this.collection.updateOne(
            { sessionId: options.session },
            { $set: sessionData },
            { upsert: true }
        );
    }

    async extract(options) {
        await this.connect();
        const session = await this.collection.findOne({ sessionId: options.session });
        return session ? session.data : null;
    }

    async delete(options) {
        await this.connect();
        await this.collection.deleteOne({ sessionId: options.session });
    }

    async list() {
        await this.connect();
        const sessions = await this.collection.find({}).toArray();
        return sessions.map(s => s.sessionId);
    }

    async close() {
        if (this.client) {
            await this.client.close();
            this.client = null;
            this.db = null;
            this.collection = null;
        }
    }
}

module.exports = MongoStore;


