import redis
import json

client = redis.Redis(
    host='localhost',
    port=6379,
    password='redispassword',
    decode_responses=True,
    db=0
)

# Testar escrita
print("Testando escrita no Redis...")
test_result = {
    "chunk_id": "manual_test_001",
    "audio_url": "audio/test.wav",
    "sentences": [
        {"segmentCode": "s1", "start": 0, "end": 1, "duration": 1, "words": [{"text": "test", "start": 0, "end": 1}]}
    ]
}

try:
    # Salvar
    result = client.rpush('readalong:audio:results', json.dumps(test_result))
    print(f"✅ Salvo! Tamanho da fila: {result}")
    
    # Verificar
    saved = client.lrange('readalong:audio:results', 0, -1)
    print(f"✅ Verificado: {len(saved)} resultados")
    print(f"Conteúdo: {saved[0][:100]}...")
    
    # Ver todas as chaves
    print("\nTodas as chaves:")
    for key in client.keys('*'):
        print(f"  - {key}")
        
except Exception as e:
    print(f"❌ Erro: {e}")