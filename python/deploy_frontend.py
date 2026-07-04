"""Sobe frontend/dist/ para a Hostinger via SFTP.

Lê credenciais de .env (nunca imprime a senha). Uso:
    npm --prefix frontend run build
    python python/deploy_frontend.py
"""
import os
import stat
from pathlib import Path

import paramiko
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "frontend" / "dist"

load_dotenv(ROOT / ".env")

SSH_HOST = os.environ["SSH_HOST"]
SSH_PORT = int(os.environ["SSH_PORT"])
SSH_USER = os.environ["SSH_USER"]
SSH_PASSWORD = os.environ["SSH_PASSWORD"]
REMOTE_DIR = os.environ["PASTA_SUBDOMINIO"]

DIR_PERM = 0o755
FILE_PERM = 0o644


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_path: str) -> None:
    try:
        sftp.stat(remote_path)
    except FileNotFoundError:
        parent = remote_path.rsplit("/", 1)[0]
        if parent and parent != remote_path:
            ensure_remote_dir(sftp, parent)
        sftp.mkdir(remote_path)
        sftp.chmod(remote_path, DIR_PERM)


def upload_dir(sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str) -> tuple[int, int]:
    files_sent = 0
    dirs_sent = 0
    ensure_remote_dir(sftp, remote_dir)
    dirs_sent += 1
    for entry in sorted(local_dir.iterdir()):
        remote_path = f"{remote_dir}/{entry.name}"
        if entry.is_dir():
            f, d = upload_dir(sftp, entry, remote_path)
            files_sent += f
            dirs_sent += d
        else:
            sftp.put(str(entry), remote_path)
            sftp.chmod(remote_path, FILE_PERM)
            files_sent += 1
    return files_sent, dirs_sent


def main() -> None:
    if not DIST_DIR.exists():
        raise SystemExit(f"{DIST_DIR} não existe — rode `npm run build` no frontend antes.")

    transport = paramiko.Transport((SSH_HOST, SSH_PORT))
    transport.connect(username=SSH_USER, password=SSH_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)

    print(f"Enviando {DIST_DIR} -> {SSH_USER}@{SSH_HOST}:{REMOTE_DIR}")
    files_sent, dirs_sent = upload_dir(sftp, DIST_DIR, REMOTE_DIR)
    print(f"Concluído: {files_sent} arquivos, {dirs_sent} pastas.")

    sftp.close()
    transport.close()


if __name__ == "__main__":
    main()
