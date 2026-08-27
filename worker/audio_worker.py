#!/usr/bin/env python3
"""Example external audio worker.

This script simulates the EXTERNAL worker that will live on another
computer. It polls the shared Redis queue for ``generate_audio`` jobs,
"generates" per-word timings for each sentence, and pushes the result
back onto the results list — exactly the contract the orchestrator waits
for.

Real deployment: replace ``simulate_timings`` with a real TTS call that
returns per-word start/end on the chunk audio timeline, then upload the
audio and set ``audio_url`` accordingly.

Run on the worker machine (only redis-py + Python needed):

    REDIS_HOST=<orchestrator-host> python worker/audio_worker.py
"""
import json
import os
from dotenv import load_dotenv
load_dotenv()
import sys
import time

import redis

JOBS_KEY = "readalong:audio:jobs"
RESULTS_KEY = "readalong:audio:results"

WORDS_PER_SECOND = 3.0  # rough speaking rate used to fake timings


def connect() -> redis.Redis:
    """Point at the same Redis the orchestrator uses (remote = other host)."""
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD") or None
    
    print(f"[worker] Connecting to Redis: host={host}, port={port}, db={db}, password={'***' if password else 'None'}")
    
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True  # Adicione isso para facilitar
    )


def simulate_timings(text: str) -> list[dict]:
    """Return fake per-word timings relative to the sentence start.

    Each word gets a duration proportional to its length (in chars) at the
    assumed speaking rate. A real worker would replace this with actual
    TTS alignment.
    """
    words = text.split()
    timings = []
    cursor = 0.0
    for word in words:
        duration = len(word) / WORDS_PER_SECOND
        timings.append({
            "text": word,
            "start": round(cursor, 3),
            "end": round(cursor + duration, 3),
        })
        cursor += duration
    return timings


def handle_job(message: dict) -> dict:
    """Build the result for one job message (the confirmed contract)."""
    sentences = []
    cursor = 0.0
    for sentence in message["sentences"]:
        words = simulate_timings(sentence["text"])
        end = cursor + (words[-1]["end"] if words else 0.0)
        sentences.append({
            "segmentCode": sentence["segmentCode"],
            "start": round(cursor, 3),
            "end": round(end, 3),
            "duration": round(end - cursor, 3),
            "words": words,
        })
        cursor = end

    return {
        "chunk_id": message["chunk_id"],
        "audio_url": f"audio/chunks/{message['chunk_id']}.wav",
        "sentences": sentences,
    }


def run() -> None:
    client = connect()
    print(f"[worker] listening on {JOBS_KEY} (redis {os.getenv('REDIS_HOST', 'localhost')})")
    print(f"[worker] using database: {os.getenv('REDIS_DB', '0')}")
    
    # Testar se o Redis está funcionando
    try:
        client.ping()
        print("[worker] ✅ Redis connection OK")
        
        # Testar escrita
        test_key = "test:worker:write"
        client.set(test_key, "test_value")
        test_value = client.get(test_key)
        print(f"[worker] ✅ Test write successful: {test_value}")
        client.delete(test_key)
    except Exception as e:
        print(f"[worker] ❌ Redis error: {e}")
        return
    
    while True:
        item = client.blpop(JOBS_KEY, timeout=0)  # block indefinitely
        if item is None:
            continue
        _, raw = item
        message = json.loads(raw)

        if message.get("type") != "generate_audio":
            print(f"[worker] ignoring job type {message.get('type')}")
            continue

        print(f"[worker] synthesizing chunk {message['chunk_id']} "
              f"({len(message['sentences'])} sentences)")
        result = handle_job(message)
        
        # Verificar antes de salvar
        print(f"[worker] Attempting to save result for {result['chunk_id']}")
        
        try:
            result_json = json.dumps(result, ensure_ascii=False)
            pushed = client.rpush(RESULTS_KEY, result_json)
            print(f"[worker] ✅ RPUSH successful, queue length: {pushed}")
            
            # Verificar se foi realmente salvo
            verify = client.lrange(RESULTS_KEY, -1, -1)
            if verify:
                print(f"[worker] ✅ Verified save for {result['chunk_id']}")
            else:
                print(f"[worker] ❌ Verification failed for {result['chunk_id']}")
                
        except Exception as e:
            print(f"[worker] ❌ Error saving result: {e}")
            
        print(f"[worker] done -> pushed result for {result['chunk_id']}")


if __name__ == "__main__":
    run()
