# Malware Analysis Dashboard

Dashboard local para análise e visualização de CSVs gerados pelo módulo de análise de malware.

## Pré-requisitos

- [Node.js](https://nodejs.org/) v18 ou superior

## Configuração dos diretórios

O `config.json` é **local** (fica fora do git, pois contém caminhos da sua máquina).
Crie-o a partir do modelo:

```bash
cp config.example.json config.json        # Linux/macOS
copy config.example.json config.json      # Windows (cmd)
```

Depois ajuste os caminhos. Aponte cada grupo para a pasta onde o analyzer gerou os CSVs
(normalmente `<data>/decrypted`):

```json
{
  "directories": {
    "android-malware": "C:\\Users\\voce\\analises\\android-virus-sign\\20260919\\decrypted",
    "general-malware": "/home/voce/analises/malwares-virus-sign/20260919/decrypted"
  }
}
```

- No Windows, separe as pastas com `\\` (barra dupla) ou `/`. Uma barra simples `\` torna o JSON inválido.
- Grupos que você não usa podem ser omitidos: aparecem como "Não configurado".
- Após editar o arquivo, use o botão **↺ Recarregar** do dashboard; não é preciso reiniciar.
- Se houver problema no arquivo (ausente, JSON inválido), o dashboard exibe um aviso explicando o que corrigir.

> **Atualizando de uma versão anterior:** o `config.json` deixou de ser versionado, e o `git pull`
> o apagaria (ou seria recusado, se você alterou o arquivo). Rode, a partir da raiz do repositório:
>
> ```bash
> cp dashboard/config.json ../config.json.bak       # 1. backup
> git checkout -- dashboard/config.json             # 2. descarta a versão local
> git pull                                          # 3. atualiza
> cp ../config.json.bak dashboard/config.json       # 4. restaura (agora ignorado pelo git)
> ```

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
