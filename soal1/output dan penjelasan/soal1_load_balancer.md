# Soal 1 — Load Balancer Sederhana (NGINX Weighted Round Robin)

## Gambaran Arsitektur

```
Client → NGINX (port 80) → backend1 (weight=3)
                         → backend2 (weight=1)
```

NGINX bertindak sebagai pintu masuk tunggal. Setiap request dari client diteruskan ke salah satu backend sesuai bobot yang dikonfigurasi.

---

## 1. Aplikasi Backend (Flask)

Kedua backend menjalankan kode yang hampir identik, hanya berbeda di teks identitasnya.

```python
from flask import Flask, jsonify
import socket

app = Flask(__name__)

@app.route('/')
def index():
    hostname = socket.gethostname()
    return f"Server 1 - TokoKita | Hostname: {hostname}"

@app.route('/products')
def products():
    data = [
        {"id": 1, "name": "Laptop",   "price": 12000000},
        {"id": 2, "name": "Mouse",    "price": 150000},
        {"id": 3, "name": "Keyboard", "price": 350000}
    ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Poin penting:**
- `socket.gethostname()` mengembalikan nama container Docker, sehingga terlihat perbedaan server saat di-load balance.
- `host='0.0.0.0'` wajib agar Flask bisa menerima koneksi dari luar container.
- Kedua server mengembalikan data produk yang **sama persis** (hardcode).

---

## 2. Konfigurasi NGINX (Weighted Round Robin)

```nginx
upstream app {
    server backend1:5000 weight=3;
    server backend2:5000 weight=1;
}

server {
    listen 80;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Poin penting:**
- `upstream app` mendefinisikan kumpulan server tujuan.
- `weight=3` pada backend1 berarti dari setiap 4 request, 3 dikirim ke backend1 dan 1 ke backend2.
- `proxy_pass http://app` meneruskan request ke upstream yang sudah didefinisikan.
- `backend1` dan `backend2` adalah nama service di Docker Compose — Docker secara otomatis me-resolve nama tersebut ke IP container yang sesuai.

---

## 3. Docker Compose

```yaml
version: '3.8'

services:
  backend1:
    build: ./backend1
    ports:
      - "5001:5000"

  backend2:
    build: ./backend2
    ports:
      - "5002:5000"

  nginx:
    build: ./nginx
    ports:
      - "80:80"
    depends_on:
      - backend1
      - backend2
```

**Poin penting:**
- `build: ./backend1` — Docker membangun image dari Dockerfile di folder tersebut.
- `ports: "5001:5000"` — format `host:container`. Backend bisa diakses langsung di port 5001/5002 (bypass NGINX), berguna untuk debugging.
- `depends_on` memastikan backend1 dan backend2 sudah jalan sebelum NGINX dimulai.
- NGINX di-expose di port 80 (port default HTTP), sehingga cukup akses `localhost` tanpa nomor port.

---

## 4. Pola Distribusi Request (Weighted Round Robin)

Dengan konfigurasi `weight=3` dan `weight=1`, urutan distribusi per siklus adalah:

| Request ke- | Diarahkan ke |
|:-----------:|:------------:|
| 1           | backend1     |
| 2           | backend1     |
| 3           | backend1     |
| 4           | backend2     |
| 5           | backend1     |
| 6           | backend1     |
| ...         | ...          |

Artinya **75% traffic** ke backend1 dan **25% traffic** ke backend2.

---

## 5. Cara Verifikasi di Terminal

```bash
# Hit endpoint / sebanyak 8 kali dan lihat hasilnya
for i in {1..8}; do curl -s http://localhost; echo ""; done
```

Output yang diharapkan (pola 3:1):
```
Server 1 - TokoKita | Hostname: <id_container>
Server 1 - TokoKita | Hostname: <id_container>
Server 1 - TokoKita | Hostname: <id_container>
Server 2 - TokoKita | Hostname: <id_container>
Server 1 - TokoKita | Hostname: <id_container>
...
```
