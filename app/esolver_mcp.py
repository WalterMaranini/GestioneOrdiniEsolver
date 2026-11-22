"""
Lettura degli ordini da eSolver tramite il server MCP ES_VENDITE.

Il server usa OAuth con login nel browser. Prima di avviare l'applicazione:

    python -m app.esolver_mcp login     accede e salva il token nel profilo Windows dell'utente
    python -m app.esolver_mcp test      verifica collegamento e strumenti disponibili
    python -m app.esolver_mcp logout    cancella il token salvato

Configurazione (variabili d'ambiente):
    ESOLVER_MCP_URL   URL del server MCP (default: MCP_URL)
    ESOLVER_GROUP     codice gruppo, es. WM

Servizi usati, entrambi di sola lettura:
- ES_SRV_ORVLeggiElenco_Post: testata e righe (fonte dell'elenco)
- DOCVEN_MCP: quantità consegnate e residue. Non contiene tutti gli ordini: dove la riga manca
  le quantità restano vuote (None), non 0.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from mcp import Client
from mcp.client.auth import AuthorizationCodeResult, OAuthClientProvider, OAuthFlowError
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from .esolver import DOCVEN, EsolverError, EsolverRepository, documenti_nuovi

MCP_URL = "https://mcpesolver.sistemi.com/mcp/App-Sistemi/ES_VENDITE"
REDIRECT_PORT = 8766
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
LOGIN_TIMEOUT = 300
MAX_EVENTO = 64 * 1024 * 1024  # un ordine da 50 righe pesa circa 260 KB

# Il server espone anche servizi di scrittura: il programma può chiamare solo questi.
LEGGI_ORDINI = "ES_SRV_ORVLeggiElenco_Post"
STRUMENTI_AMMESSI = {LEGGI_ORDINI, DOCVEN}


class LoginRichiesto(EsolverError):
    """Manca un token valido."""

    status = 503

    def __init__(self):
        super().__init__("Accesso a eSolver mancante o scaduto: eseguire 'python -m app.esolver_mcp login'")


# ----------------------------------------------------------------- token

def _file_token() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".config")
    return base / "GestioneOrdiniEsolver" / "mcp_token.json"


class FileTokenStorage:
    """Token e registrazione del client, salvati fuori dal progetto."""

    def __init__(self, path: Path | None = None):
        self.path = path or _file_token()

    def _leggi(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return {}

    def _scrivi(self, chiave: str, valore) -> None:
        d = self._leggi()
        d[chiave] = valore.model_dump(mode="json", exclude_none=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(self.path)

    def ha_token(self) -> bool:
        return "token" in self._leggi()

    def cancella(self) -> None:
        self.path.unlink(missing_ok=True)

    async def get_tokens(self) -> OAuthToken | None:
        d = self._leggi().get("token")
        return OAuthToken.model_validate(d) if d else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._scrivi("token", tokens)

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        d = self._leggi().get("client")
        return OAuthClientInformationFull.model_validate(d) if d else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._scrivi("client", client_info)


# ----------------------------------------------------------------- login nel browser

class _Callback:
    """Server locale che riceve il codice di autorizzazione dopo il login."""

    def __init__(self):
        self.esito: dict[str, str] = {}
        self.arrivato = threading.Event()
        callback = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                u = urlparse(self.path)
                if u.path != "/callback":
                    self.send_error(404)
                    return
                callback.esito = {k: v[0] for k, v in parse_qs(u.query).items()}
                ok = "code" in callback.esito
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                testo = "Accesso completato, puoi chiudere questa pagina." if ok else "Accesso non riuscito."
                self.wfile.write(testo.encode("utf-8"))
                callback.arrivato.set()

            def log_message(self, *a):  # l'URL contiene il codice: non va scritto a video
                pass

        self.server = HTTPServer(("127.0.0.1", REDIRECT_PORT), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    async def apri(self, url: str) -> None:
        print("Apro il browser per l'accesso. Se non si apre, usa questo indirizzo:\n" + url)
        webbrowser.open(url)

    async def attendi(self) -> AuthorizationCodeResult:
        if not await asyncio.to_thread(self.arrivato.wait, LOGIN_TIMEOUT):
            raise OAuthFlowError("Tempo scaduto in attesa del login")
        if "code" not in self.esito:
            raise OAuthFlowError(self.esito.get("error_description") or self.esito.get("error") or "Login annullato")
        return AuthorizationCodeResult(code=self.esito["code"], state=self.esito.get("state"),
                                       iss=self.esito.get("iss"))

    def chiudi(self) -> None:
        self.server.shutdown()
        self.server.server_close()


# ----------------------------------------------------------------- client MCP

def _contiene(exc: BaseException, tipo: type) -> bool:
    if isinstance(exc, BaseExceptionGroup):
        return any(_contiene(e, tipo) for e in exc.exceptions)
    return isinstance(exc, tipo)


def _causa(exc: BaseException) -> BaseException:
    while isinstance(exc, BaseExceptionGroup):
        exc = exc.exceptions[0]
    return exc


class McpEsolver:
    """Client sincrono: apre una sessione per ogni richiesta (le API girano nel threadpool)."""

    def __init__(self, url: str | None = None, storage: FileTokenStorage | None = None):
        self.url = url or os.environ.get("ESOLVER_MCP_URL") or MCP_URL
        self.storage = storage or FileTokenStorage()
        self._nomi: dict[str, str] = {}

    def esegui(self, operazione, callback: _Callback | None = None):
        """Esegue `await operazione(client)` in una sessione MCP."""
        if callback is None and not self.storage.ha_token():
            raise LoginRichiesto()
        try:
            return asyncio.run(self._sessione(operazione, callback))
        except Exception as e:
            causa = _causa(e)
            if isinstance(causa, EsolverError):
                raise causa from None
            if callback is None and _contiene(e, OAuthFlowError):
                raise LoginRichiesto() from None
            raise EsolverError(f"Server MCP eSolver: {type(causa).__name__}: {causa}") from e

    async def _sessione(self, operazione, callback):
        # Senza callback (server web) il login interattivo non è possibile: l'SDK solleva OAuthFlowError.
        auth = OAuthClientProvider(
            server_url=self.url,
            client_metadata=OAuthClientMetadata(
                client_name="Gestione Ordini eSolver",
                redirect_uris=[REDIRECT_URI],
                grant_types=["authorization_code"],
                response_types=["code"],
                token_endpoint_auth_method="none",
            ),
            storage=self.storage,
            redirect_handler=callback.apri if callback else None,
            callback_handler=callback.attendi if callback else None,
        )
        async with create_mcp_http_client(auth=auth) as http:
            trasporto = streamable_http_client(self.url, http_client=http, max_sse_event_size=MAX_EVENTO)
            async with Client(trasporto, mode="legacy") as client:
                return await operazione(client)

    async def strumenti(self, client: Client) -> dict[str, str]:
        """Nomi reali sul server degli strumenti ammessi (il server può aggiungere un prefisso)."""
        if not self._nomi:
            tutti = []
            cursore = None
            while True:
                r = await client.list_tools(cursor=cursore)
                tutti += [t.name for t in r.tools]
                cursore = r.next_cursor
                if not cursore:
                    break
            for s in STRUMENTI_AMMESSI:
                nome = next((n for n in tutti if n == s or n.endswith("_" + s)), None)
                if nome:
                    self._nomi[s] = nome
        return self._nomi

    async def chiama(self, client: Client, strumento: str, argomenti: dict) -> dict:
        if strumento not in STRUMENTI_AMMESSI:
            raise EsolverError(f"Strumento non ammesso: {strumento}")
        nome = (await self.strumenti(client)).get(strumento)
        if not nome:
            raise EsolverError(f"Il server MCP non espone {strumento}")
        r = await client.call_tool(nome, argomenti, read_timeout_seconds=120)
        testo = "".join(getattr(c, "text", "") for c in r.content)
        if r.is_error:
            raise EsolverError(f"{strumento}: {testo[:500]}")
        try:
            dati = json.loads(testo) if testo else r.structured_content
        except ValueError:
            raise EsolverError(f"{strumento}: risposta non valida: {testo[:200]}") from None
        if not isinstance(dati, dict):
            raise EsolverError(f"{strumento}: risposta inattesa")
        return dati


# ----------------------------------------------------------------- repository

class McpRepository(EsolverRepository):
    """Come EsolverRepository, ma passa dal server MCP e legge l'elenco dal servizio ordini."""

    ELENCO_DA_REPORT = False

    PAGE = 10
    PAGE_DOCVEN = 200

    def __init__(self, mcp: McpEsolver | None = None, group: str | None = None):
        self.mcp = mcp or McpEsolver()
        self.group = group or os.environ.get("ESOLVER_GROUP", "WM")
        self._azzera()

    def _chiama(self, payload: dict) -> list[dict]:
        async def leggi(client):
            dati, visti = [], set()
            while True:
                nuovi = documenti_nuovi(await self.mcp.chiama(client, LEGGI_ORDINI, {
                    "X-BC-GROUP": self.group, **payload, "Skip": len(dati), "Take": self.PAGE}), visti)
                if not nuovi:
                    return dati
                dati += nuovi
        return self.mcp.esegui(leggi)

    def _righe_report(self, nome: str, filtri: list[dict]) -> list[dict]:
        async def leggi(client):
            righe = []
            while True:
                d = await self.mcp.chiama(client, nome, {
                    "X-BC-GROUP": self.group, "Filters": filtri, "Digits": [],
                    "Skip": len(righe), "Take": self.PAGE_DOCVEN})
                pagina = d.get("result") or []
                righe += pagina
                if not pagina or len(righe) >= d.get("count", 0):
                    return righe
        return self.mcp.esegui(leggi)


# ----------------------------------------------------------------- comandi

def main(argv: list[str]) -> int:
    comando = argv[0] if argv else ""
    mcp = McpEsolver()
    if comando == "logout":
        mcp.storage.cancella()
        print("Token cancellato.")
        return 0
    if comando not in ("login", "test"):
        print(__doc__)
        return 2
    callback = _Callback() if comando == "login" else None
    try:
        nomi = mcp.esegui(mcp.strumenti, callback)
    except EsolverError as e:
        print(f"Errore: {e}")
        return 1
    finally:
        if callback:
            callback.chiudi()
    mancanti = STRUMENTI_AMMESSI - nomi.keys()
    print("Collegamento riuscito. Strumenti: " + ", ".join(sorted(nomi.values())))
    if mancanti:
        print("Mancano: " + ", ".join(sorted(mancanti)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
