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
            // Criar cliente com opções SSL/TLS corretas para MongoDB Atlas
            // Remover opções deprecated e usar apenas o necessário
            const clientOptions = {
                serverApi: this.mongoOptions.serverApi,
            };
            
            this.client = new MongoClient(this.uri, clientOptions);
            
            // Conectar com timeout
            await Promise.race([
                this.client.connect(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout ao conectar ao MongoDB (30s)')), 30000)
                )
            ]);
            
            this.db = this.client.db(this.dbName);
            this.collection = this.db.collection(this.collectionName);
            
            // Criar índice para melhor performance
            await this.collection.createIndex({ sessionId: 1 }, { unique: true });
            
            console.log(`✅ Conectado ao MongoDB: ${this.dbName}/${this.collectionName}`);
        } catch (error) {
            console.error('❌ Erro ao conectar ao MongoDB:', error.message);
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


