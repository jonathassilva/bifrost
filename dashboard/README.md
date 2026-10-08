# Malware Analysis Dashboard

Dashboard local para análise e visualização de CSVs gerados pelo módulo de análise de malware.

## Pré-requisitos

- [Node.js](https://nodejs.org/) v18 ou superior

## Configuração dos diretórios

Edite o arquivo `config.json` na raiz do projeto com os caminhos das suas pastas:

```json
{
  "directories": {
    "android-malware": "C:\\Users\\user\\Documents\\codes\\bifrost\\android-virus-sign\\260603",
    "general-malware": "C:\\Users\\user\\Documents\\codes\\bifrost\\malware-virus-sign\\260603"
  }
}
```

> Use `\\` para separar pastas no Windows, ou `/` no Linux/macOS.

## Como rodar

```bash
# 1. Instalar dependências
npm install

# 2. Iniciar o servidor (Express + Vite simultaneamente)
npm run dev
```

Acesse `http://localhost:5173` no browser.

## Como funciona

- O servidor Express (`server.js`) lê o `config.json` e serve os CSVs via API local
- O frontend React consome a API em `http://localhost:3001`
- Três abas disponíveis: **Android**, **Geral** e **Consolidado**
- O botão **↺ Recarregar** relê os diretórios sem precisar reiniciar

## Segurança

Todos os dados são processados **localmente**. O servidor Express roda apenas na sua máquina e não expõe dados para a internet.
