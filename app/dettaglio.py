"""
Dettaglio del singolo ordine: dati delle schede Generali, Condizioni e Logistica.

La testata viene da LeggiElenco, che riporta soprattutto codici. Le descrizioni vengono dai report REST di
sola lettura elencati qui sotto. Ciò che nessun servizio espone resta vuoto: non si ricava per ipotesi.
Se un report non risponde il dettaglio si apre lo stesso, senza quelle descrizioni e con un avviso.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .esolver import DOCVEN, EsolverError, _data

log = logging.getLogger(__name__)

TERRITORIALITA = {0: "Italia", 1: "CEE", 2: "Fuori CEE"}

# righe di un report: (nome, filtri) -> righe
LeggiReport = Callable[[str, list[dict]], list[dict]]


def _testo(v) -> str:
    return str(v if v is not None else "").strip()


def _codice(v) -> str:
    """Codice come testo; lo zero di eSolver significa "non indicato"."""
    return "" if v in (None, 0, "", "0") else _testo(v)


def _voce(codice, descrizione="") -> str:
    """Formato "codice - descrizione" delle caselle di eSolver."""
    return " - ".join(x for x in (_testo(codice), _testo(descrizione)) if x)


def _indirizzo(numero, indirizzo, comune, provincia) -> str:
    testo = " ".join(x for x in (_testo(indirizzo), _testo(comune), f"({_testo(provincia)})" if _testo(provincia) else "") if x)
    return _voce(numero, testo) if testo else ""


def _uno(righe: list[dict], **chiave) -> dict:
    """La riga con quei valori, o un dizionario vuoto."""
    return next((r for r in righe if all(_testo(r.get(k)) == _testo(v) for k, v in chiave.items())), {})


def leggi_descrizioni(raw: dict, report: LeggiReport) -> tuple[dict[str, list[dict]], list[str]]:
    """Legge in parallelo i report che servono all'ordine. Restituisce le righe e gli avvisi."""
    clienti = sorted({c for c in (_codice(raw.get("CodCliFor")), _codice(raw.get("AnagrFattCod"))) if c})
    agenti = sorted({c for c in (_codice(raw.get("CodAgente1")), _codice(raw.get("CodAgente2"))) if c})

    def per_codice(codici):
        return [{"Name": "CodCliFor", "Operators": 11, "Values": codici}]

    richieste = {
        "tipi": ("TIPIDOC_MCP", [], "tipo documento"),
        "pagamenti": ("CONDPAGELENCO_MCP", [], "condizione di pagamento"),
    }
    if clienti:
        richieste["clienti"] = ("CLIENTIELENCO_MCP", per_codice(clienti), "partita IVA e anagrafica di fatturazione")
        richieste["indirizzi"] = ("CLIENTIINDIRIZZI_MCP", per_codice(clienti), "destinatario fattura")
    if agenti:
        richieste["agenti"] = ("AGENTIELENCO_MCP", per_codice(agenti), "nomi degli agenti")
    giorno = _data(raw.get("DataRegistrazione"))
    if giorno:
        g = giorno[8:10] + giorno[5:7] + giorno[:4]
        richieste["docven"] = (DOCVEN, [
            {"Name": "TipoMovimento", "Operators": 11, "Values": ["4"]},
            {"Name": "CliForCod", "Operators": 11, "Values": [_testo(raw.get("CodCliFor"))]},
            {"Name": "DataRegistraz", "Operators": 3, "Values": [g, g]}], "zona e capo area")

    def leggi(voce):
        chiave, (nome, filtri, cosa) = voce
        try:
            return chiave, report(nome, filtri), None
        except EsolverError as e:
            if e.status == 503:  # accesso mancante: va segnalato
                raise
            log.warning("Descrizioni non disponibili (%s): %s", nome, e)
            return chiave, [], cosa

    with ThreadPoolExecutor(len(richieste)) as ex:
        esiti = list(ex.map(leggi, richieste.items()))
    return {k: r for k, r, _ in esiti}, [cosa for _, _, cosa in esiti if cosa]


def map_dettaglio(raw: dict, d: dict[str, list[dict]]) -> dict:
    """Campi delle schede, nell'ordine in cui compaiono nella maschera."""
    def v(campo):
        return _testo(raw.get(campo))

    cliente = _codice(raw.get("CodCliFor"))
    anagrafica = _uno(d.get("clienti", []), CodCliFor=cliente)
    cod_fatt = _codice(raw.get("AnagrFattCod"))
    fatturazione = _uno(d.get("clienti", []), CodCliFor=cod_fatt) if cod_fatt else {}
    num_fatt = raw.get("AnagrFattNumRifIndir") or 0
    destinatario = _uno(d.get("indirizzi", []), CodCliFor=cod_fatt, NumProgr=num_fatt) if cod_fatt else {}
    tipo = _uno(d.get("tipi", []), GruppoDoc="ORV", CodTipoDoc=raw.get("CodTipoDoc"))
    pagamento = _uno(d.get("pagamenti", []), CodCondizPagamento=raw.get("CodCondizPagamento"))
    # zona e capo area dell'ordine: quelli attuali del cliente possono essere diversi
    docven = _uno(d.get("docven", []), IdDocumento=raw["IdDocumento"])
    zona = _voce(docven.get("CodZona"), docven.get("DesZona")) if _testo(docven.get("CodZona")) else ""

    def agente(n):
        codice = _codice(raw.get(f"CodAgente{n}"))
        return {
            "agente": _voce(codice, _uno(d.get("agenti", []), CodCliFor=codice).get("RagSocCompleta")) if codice else "",
            "ruolo": _codice(raw.get(f"RuoloAgente{n}")),
            "provvigione": raw.get(f"PercProvvigione{n}") or 0,
            # il report espone solo il capo area dell'agente 1
            "capo_area": _voce(_codice(docven.get("CoaCapoAreaAgente1")), docven.get("AgenteCapoArea"))
            if n == 1 and _codice(docven.get("CoaCapoAreaAgente1")) else "",
        }

    def vettore(n):
        x = _uno(raw.get("Vettori") or [], NumProgrVett=n)
        return {
            "vettore": _codice(x.get("CodVettore")),
            "ragione_sociale": " ".join(t for t in (_testo(x.get("RagSoc1")), _testo(x.get("RagSoc2"))) if t),
            "indirizzo": _testo(x.get("Indir")), "indirizzo2": _testo(x.get("Indir2")),
            "comune": _testo(x.get("Localita")), "provincia": _testo(x.get("Provincia")),
            "cap": _testo(x.get("Cap")), "stato": _testo(x.get("CodStato")),
            "partita_iva": _testo(x.get("PartitaIva")), "albo": _testo(x.get("NumIscrizioneAlbo")),
        }

    return {
        "id": raw["IdDocumento"],
        "num_reg": raw.get("NumRegistraz"),
        "data_reg": _data(raw.get("DataRegistrazione")),
        "cod_tipo": _testo(raw.get("CodTipoDoc")),
        "tipo": _testo(tipo.get("Des")),
        "cod_cliente": cliente,
        "cliente": v("CliForRagSoc1"),
        "intestatario": {
            "ragione_sociale": " ".join(t for t in (v("CliForRagSoc1"), v("CliForRagSoc2")) if t),
            "indirizzo": " ".join(t for t in (v("CliForIndir1"), v("CliForIndir2")) if t),
            "comune": v("CliForLocalita1"), "provincia": v("CliForProv"), "cap": v("CliForCap"),
            "stato": _testo(anagrafica.get("CodStato")), "frazione": v("CliForLocalita2"),
            "partita_iva": _testo(anagrafica.get("PartitaIva")),
            "codice_fiscale": _testo(anagrafica.get("CodFiscale")),
        },
        "consegna": {
            "codice": _indirizzo(raw.get("DatiSpedNum") or 0, v("DatiSpedIndir1"), v("DatiSpedLocalita1"), v("DatiSpedProv")),
            "ragione_sociale": " ".join(t for t in (v("DatiSpedRagSoc1"), v("DatiSpedRagSoc2")) if t),
            "indirizzo": v("DatiSpedIndir1"), "indirizzo2": v("DatiSpedIndir2"),
            "comune": v("DatiSpedLocalita1"), "provincia": v("DatiSpedProv"), "cap": v("DatiSpedCap"),
            "stato": v("SpedCodStatoUe"), "frazione": v("DatiSpedLocalita2"),
        },
        "agenti": [agente(1), agente(2)],
        "altri": {
            "data_consegna": _data(raw.get("DataConsegnaRich")),
            "divisione": v("CodDivisione"), "centro": v("CodCentroImputazione"),
            "riferimento": v("Riferimento"),
            "confermato": bool(raw.get("OrdineConfermato")), "blocca_evasione": bool(raw.get("BloccaEvasione")),
            "derivato": v("GruppoDocumentoDer"), "tipo_fattura": _codice(raw.get("CodTipoFattura")),
            "valuta": v("CodValuta"), "cambio": raw.get("CambioRiferimento") or 0,
            "iva_agevolata": v("CodIvaAgevolato"),
            "addebiti": "Abilita" if raw.get("EseguiAddebitiAuto") else "Disabilita",
            "lingua": _codice(raw.get("CodLinguaDocumenti")),
        },
        "commerciali": {
            "listino_prioritario": _voce(v("TipoListinoPrioritario"), v("CodListinoPrioritario")),
            "listino_ordinario": _voce(v("TipoListinoOrdinario"), v("CodListinoOrdinario")),
            "politica_sconti": v("CodPoliticaSconti"), "zona": zona,
        },
        "finanziarie": {
            "pagamento": _voce(v("CodCondizPagamento"), pagamento.get("Des")) if v("CodCondizPagamento") else "",
            "sconto": raw.get("ScontoCondizPagam") or 0,
            "decorrenza": _data(raw.get("DataDecorrCalcScad")),
        },
        "fatturazione": {
            "codice": _voce(cod_fatt, fatturazione.get("RagSocCompleta")),
            "indirizzo": _testo(fatturazione.get("IndirizzoCompleto")),
            "comune": _testo(fatturazione.get("Localita")), "provincia": _testo(fatturazione.get("Provincia")),
            "cap": _testo(fatturazione.get("Cap")), "stato": _testo(fatturazione.get("CodStato")),
            "frazione": _testo(fatturazione.get("Localita2")),
            "territorialita": TERRITORIALITA.get(raw.get("TerritorialitaIVA") or 0, v("TerritorialitaIVA")),
            "privato": bool(raw.get("CessioneCliPrivato")),
        },
        "destinatario_fattura": {
            "numero": _indirizzo(num_fatt, destinatario.get("IndirizzoCompleto"), destinatario.get("Localita"),
                                 destinatario.get("Provincia")),
            "indirizzo": _testo(destinatario.get("IndirizzoCompleto")),
            "comune": _testo(destinatario.get("Localita")), "provincia": _testo(destinatario.get("Provincia")),
            "cap": _testo(destinatario.get("Cap")), "stato": _testo(destinatario.get("CodStato")),
            "frazione": _testo(destinatario.get("Localita2")),
            "contatto": _codice(raw.get("ContattoIndDestFatt")),
        },
        "banca": {
            "nostra": _codice(raw.get("IntestCodBancaRif")), "appoggio": _codice(raw.get("IntestAppoggBanca")),
        },
        "logistica": {
            "magazzino": v("CodMag"), "area": v("CodAreaMag"),
            "magazzino_sec": v("CodMagArrivo"), "area_sec": v("CodAreaMagSec"),
            "porto": v("CodPorto"), "des_porto": v("DesPorto"),
            "trasporto": v("CodTrasportoMezzo"), "des_trasporto": v("DesTrasportoMezzo"),
            "causale": v("CodCausaleTrasporto"), "des_causale": v("DesCausaleTrasporto"),
            "aspetto": v("AspettoBeni"), "des_aspetto": v("DesAspettoBeni"),
            "giro": v("CodGiroConsegne"), "sequenza": raw.get("OrdineNelGiro") or 0,
        },
        "vettori": [vettore(1), vettore(2)],
    }
