# 📹 Youtube analisis MCP

Servidor **MCP** por stdio que analiza comentarios recientes de un canal de YouTube (sentimiento + palabras clave).

## Requisitos

Existen dos formas de correr el programa, peude ser directamente con python o con uv

- Python 3.10+
- Uv (opcional)

### 🪟 Windows

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 🐧 Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- (alternativa) `pip install uv`

## 🚀 Instalación

Clona el repo (o copia los archivos) y desde la carpeta del proyecto:

```bash
uv sync
```

Esto crea un `.venv` y instala dependencias de `pyproject.toml`.

## 🤑 Ejecutar el servidor MCP

Dos formas:

- con python directo

```bash
python Server.py
```

- con uv

```bash
uv run mcp.py
```

## 🧐 Como conectarlo a cloud?

```bash
{
  "mcpServers": {
    "youtube": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\<Path al archivo>\\MCP_Server",
        "run",
        "Server.py"
      ]
    }
  }
}
```

## 💩 Como correrlo en tu chatbot?

Si tu implentacion tiene tipo es stdio, comando es python y args ./server.py.
ejemplo:

```bash
Name: ServerGerax
type: "stdio"
commnad: "python"
Args = ["./Server.py"] # Aqui es donde esta clonado el server
```
