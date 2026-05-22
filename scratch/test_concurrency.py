import urllib.request
import json
import threading
import time

API_URL = "http://localhost:8000/analyze"
TEST_LOG = "May 20 10:24:45 prod-web-server sshd[18245]: Failed password for invalid user admin from 185.220.101.42 port 54820 ssh2"

def make_request(model_name, thread_id):
    data = json.dumps({
        "log": TEST_LOG,
        "context": "Contexto de teste"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{API_URL}?model={model_name}", 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        print(f"[Thread {thread_id}] Enviando requisição para {model_name}...")
        start = time.time()
        with urllib.request.urlopen(req) as response:
            res_content = response.read().decode('utf-8')
            elapsed = time.time() - start
            print(f"[Thread {thread_id}] Concluído {model_name} em {elapsed:.2f}s (Tamanho: {len(res_content)} bytes)")
    except Exception as e:
        print(f"[Thread {thread_id}] Erro no modelo {model_name}: {e}")

if __name__ == "__main__":
    t1 = threading.Thread(target=make_request, args=("sem_prompt", 1))
    t2 = threading.Thread(target=make_request, args=("com_prompt", 2))
    
    start_time = time.time()
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    print(f"Tempo total concorrente: {time.time() - start_time:.2f}s")
