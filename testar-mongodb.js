/**
 * Script para testar conexão com MongoDB
 */
const { MongoClient, ServerApiVersion } = require('mongodb');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017';

async function testConnection() {
    console.log('🔍 Testando conexão com MongoDB...');
    console.log(`📡 URI: ${MONGODB_URI.replace(/\/\/([^:]+):([^@]+)@/, '//$1:***@')}`);
    
    const client = new MongoClient(MONGODB_URI, {
        serverApi: {
            version: ServerApiVersion.v1,
            strict: true,
            deprecationErrors: true,
        },
    });

    try {
        console.log('⏳ Conectando...');
        await Promise.race([
            client.connect(),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Timeout (30s)')), 30000)
            )
        ]);
        
        console.log('✅ Conectado!');
        
        // Testar ping
        await client.db('admin').command({ ping: 1 });
        console.log('✅ Ping bem-sucedido!');
        
        // Listar bancos
        const dbs = await client.db().admin().listDatabases();
        console.log('📊 Bancos disponíveis:', dbs.databases.map(d => d.name).join(', '));
        
        await client.close();
        console.log('✅ Conexão fechada com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro:', error.message);
        console.error('📋 Detalhes:', error);
        process.exit(1);
    }
}

testConnection();


