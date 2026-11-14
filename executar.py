"""Executa um arquivo .sql no banco taskflow.db e mostra o resultado de cada comando.
Uso: python executar.py nome_do_arquivo.sql
"""
import sqlite3
import sys

if len(sys.argv) < 2:
    print("Uso: python executar.py nome_do_arquivo.sql")
    sys.exit(1)

try:
    texto = open(sys.argv[1], encoding="utf-8").read()
except FileNotFoundError:
    print(f"Arquivo não encontrado: {sys.argv[1]}")
    sys.exit(1)

conn = sqlite3.connect("taskflow.db")
conn.execute("PRAGMA foreign_keys = ON")  # liga a checagem de FOREIGN KEY

# remove linhas de comentário (--) e separa os comandos pelo ;
linhas = [l for l in texto.splitlines() if not l.strip().startswith("--")]
comandos = [c.strip() for c in "\n".join(linhas).split(";") if c.strip()]

for comando in comandos:
    print(">>", comando.splitlines()[0][:70])
    try:
        cur = conn.execute(comando)
        if cur.description:  # foi um SELECT: mostra a tabela
            print("   " + " | ".join(col[0] for col in cur.description))
            for linha in cur.fetchall():
                print("   " + " | ".join(str(v) for v in linha))
        elif cur.rowcount >= 0:  # INSERT, UPDATE, DELETE
            print(f"   OK ({cur.rowcount} linha(s) afetada(s))")
        else:  # CREATE, DROP, PRAGMA
            print("   OK")
    except sqlite3.Error as erro:
        print(f"   ERRO: {erro}")

conn.commit()
conn.close()