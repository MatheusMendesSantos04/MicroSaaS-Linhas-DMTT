# Frontend - MicroSaaS Linhas DMTT

Interface web para consumo da API local e visualização das linhas no mapa.

## Requisitos

- Node.js 18+

## Executar

No diretório `frontend`:

```bash
npm install
npm run dev
```

Por padrão, a aplicação usa `http://127.0.0.1:8000` como base da API.

Para alterar:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```