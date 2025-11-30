const { MongoClient, ServerApiVersion } = require('mongodb');

class MongoStore {
    constructor(options) {
        this.uri = options.uri;
        this.dbName = options.dbName || 'whatsapp-sessions';
        this.collectionName = options.collectionName || 'whatsapp_sessions';
        this.client = null;
        this.db = null;
        this.collection = null;
    }

    async connect() {
        if (this.client) {
            return;
        }

        console.log('[MongoStore] Conectando ao MongoDB...');
        console.log(`[MongoStore] URI: ${this.uri.substring(0, 30)}...`);
        console.log(`[MongoStore] Database: ${this.dbName}`);
        console.log(`[MongoStore] Collection: ${this.collectionName}`);

        try {
            this.client = new MongoClient(this.uri, {
                serverApi: {
                    version: ServerApiVersion.v1,
                    strict: true,
                    deprecationErrors: true,
                },
                connectTimeoutMS: 60000,
                serverSelectionTimeoutMS: 60000,
                socketTimeoutMS: 60000,
                retryWrites: true,
                retryReads: true,
            });

            await this.client.connect();
            console.log('[MongoStore] ✅ Conectado ao MongoDB');

            this.db = this.client.db(this.dbName);
            this.collection = this.db.collection(this.collectionName);

            // Criar índice para melhor performance
            await this.collection.createIndex({ session: 1 }, { unique: true });
            console.log('[MongoStore] ✅ Índice criado');

            // Testar conexão com ping
            await this.db.admin().command({ ping: 1 });
            console.log('[MongoStore] ✅ Ping bem-sucedido');
        } catch (error) {
            console.error('[MongoStore] ❌ Erro ao conectar:', error.message);
            throw error;
        }
    }

    async sessionExists(options) {
        if (!this.collection) {
            await this.connect();
        }

        const session = options.session || 'default';
        console.log(`[MongoStore] Verificando se sessão existe: ${session}`);

        try {
            const doc = await this.collection.findOne({ session });
            const exists = !!doc;
            
            console.log(`[MongoStore] Sessão "${session}": ${exists ? 'EXISTE' : 'NÃO EXISTE'}`);
            if (exists) {
                console.log(`[MongoStore] 📦 Dados da sessão encontrados (${Object.keys(doc).length} campos)`);
            }
            
            return exists;
        } catch (error) {
            console.error(`[MongoStore] ❌ Erro ao verificar sessão: ${error.message}`);
            return false;
        }
    }

    async save(options) {
        if (!this.collection) {
            await this.connect();
        }

        const session = options.session || 'default';
        const data = options.data || {};

        console.log(`[MongoStore] 💾 Salvando sessão: ${session}`);
        console.log(`[MongoStore] Tamanho dos dados: ${JSON.stringify(data).length} bytes`);

        try {
            await this.collection.updateOne(
                { session },
                { 
                    $set: { 
                        session,
                        data,
                        updatedAt: new Date()
                    }
                },
                { upsert: true }
            );
            console.log(`[MongoStore] ✅ Sessão salva com sucesso`);
        } catch (error) {
            console.error(`[MongoStore] ❌ Erro ao salvar sessão: ${error.message}`);
            throw error;
        }
    }

    async extract(options) {
        if (!this.collection) {
            await this.connect();
        }

        const session = options.session || 'default';
        console.log(`[MongoStore] 📥 Extraindo sessão: ${session}`);

        try {
            const doc = await this.collection.findOne({ session });
            
            if (!doc) {
                console.log(`[MongoStore] ⚠️ Sessão não encontrada`);
                return null;
            }

            console.log(`[MongoStore] ✅ Sessão extraída (${Object.keys(doc.data || {}).length} campos)`);
            return doc.data || null;
        } catch (error) {
            console.error(`[MongoStore] ❌ Erro ao extrair sessão: ${error.message}`);
            return null;
        }
    }

    async delete(options) {
        if (!this.collection) {
            await this.connect();
        }

        const session = options.session || 'default';
        console.log(`[MongoStore] 🗑️ Deletando sessão: ${session}`);

        try {
            const result = await this.collection.deleteOne({ session });
            console.log(`[MongoStore] ✅ Sessão deletada: ${result.deletedCount > 0 ? 'SIM' : 'NÃO ENCONTRADA'}`);
            return result.deletedCount > 0;
        } catch (error) {
            console.error(`[MongoStore] ❌ Erro ao deletar sessão: ${error.message}`);
            return false;
        }
    }

    async list() {
        if (!this.collection) {
            await this.connect();
        }

        console.log(`[MongoStore] 📋 Listando todas as sessões`);

        try {
            const sessions = await this.collection.find({}).toArray();
            console.log(`[MongoStore] ✅ Encontradas ${sessions.length} sessão(ões)`);
            return sessions.map(doc => doc.session);
        } catch (error) {
            console.error(`[MongoStore] ❌ Erro ao listar sessões: ${error.message}`);
            return [];
        }
    }

    async close() {
        if (this.client) {
            console.log('[MongoStore] Fechando conexão...');
            await this.client.close();
            this.client = null;
            this.db = null;
            this.collection = null;
            console.log('[MongoStore] ✅ Conexão fechada');
        }
    }
}

module.exports = MongoStore;
