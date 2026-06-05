import os
import re
import csv
from html import escape
 
INPUT_DIR = r"C:\fup"
OUTPUT_DIR = "output"
VOL_FILE = os.path.join(INPUT_DIR, "volumetria.csv")
HIER_FILE = os.path.join(INPUT_DIR, "hierarquia_bare.csv")
 
REGION_FOLDERS = ["SUL", "NE_NCO", "SP_CAPITAL", "SP_INTERIOR", "RJ_MG_ES"]
 
STATUS_BLOQUEADOS = ("EMIT", "PEND", "DECLIN")
 
V_COL_SUPEX = "SUPEX"
V_COL_SUC = "SUC-CPD"
V_COL_STATUS = "Status (Obrigatório)"
V_COL_SUBSTAT = "Substatus"
V_COL_EMAIL = "Email corretor"
V_COL_CORRET = "Nome Corretor"
V_COL_COTACAO = "Numero de Cotacao"
V_COL_SEGUR = "Nome segurado em cotação"
V_COL_VIG = "Inicio de Vigencia"
V_COL_GWP = "GWP"
 
H_COL_SUC = "Suc_CPD Corretor"
H_COL_GC = "E-mail do GC"
H_COL_SUP = "E-mail do Superintendente da Cia"
 
SIGNATURES = {
    "SUL": (
        "Larissa Araújo Macedo (external) | External Staff | Contractor | Operations Corporate Solutions<br>"
        "Swiss Re Serviços de Consultoria em Seguros e Resseguros Ltda. | GENERIC LOCATION, Sao Paulo, Brazil<br>"
        "Email: LarissaAraujo_Macedo@swissre.com"
    ),
    "NE_NCO": (
        "Vivianne Souza (external) | External Staff | Contractor | Operations Corporate Solutions<br>"
        "Swiss Re Corporate Solutions Brasil Seguros S.A. | Avenida Faria Lima 3064 – 7º andar, 01451-001 Sao Paulo, Brazil<br>"
        "Direct: +55 11 3708-4571 &nbsp; Email: Vivianne_Souza@swissre.com"
    ),
    "SP_INTERIOR": (
        "Giovanna Capozzoli Martins (external) | External Staff | Contractor | Operations Corporate Solutions<br>"
        "Swiss Re Serviços de Consultoria em Seguros e Resseguros Ltda. | GENERIC LOCATION, Sao Paulo, Brazil<br>"
        "Email: Giovanna_CapozzoliMartins@swissre.com"
    ),
    "RJ_MG_ES": (
        "Giovanna Capozzoli Martins (external) | External Staff | Contractor | Operations Corporate Solutions<br>"
        "Swiss Re Serviços de Consultoria em Seguros e Resseguros Ltda. | GENERIC LOCATION, Sao Paulo, Brazil<br>"
        "Email: Giovanna_CapozzoliMartins@swissre.com"
    ),
    "SP_CAPITAL": (
        "Nelson Vale (external)<br>"
        "External Staff, Contractor, MU Ibero-America, Middle East & Africa<br>"
        "+55 11 93407-3758<br>"
        "Nelson_Vale@swissre.com<br>"
        "Swiss Re Corporate Solutions Brasil Seguros S.A.<br>"
        "Avenida Brigadeiro Faria Lima 3064 Itaim Bibi, 01451-000 Sao Paulo, Brazil"
    )
}
 
HEADERS_STACKED_VOL = [
    "Numero de Cotacao",
    "Numero da Apolice",
    "Nome segurado em cotação",
    "Data da Cotacao",
    "Inicio de Vigencia",
    "GWP",
    "Codigo Agencia Produtora",
    "Nome Agencia Produtora",
    "Nome Corretor",
    "Canal OV",
    "Codigo Corretor",
    "Telefone Corretor",
    "SUPEX",
    "Suc + Nome",
    "SUC-CPD",
    "Nome Assessoria",
    "Renovação algoritimo",
    "Status (Obrigatório)",
    "Substatus",
    "Responsável",
    "Feedback",
    "Observação",
    "Nome subscritor",
    "Email corretor",
]
 
for folder in REGION_FOLDERS:
    os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)
 
for folder in REGION_FOLDERS:
    folder_path = os.path.join(OUTPUT_DIR, folder)
    for file in os.listdir(folder_path):
        if file.lower().endswith(".html"):
            os.remove(os.path.join(folder_path, file))
 
def norm(value):
    if value is None:
        return ""
 
    return str(value).strip().replace("\ufeff", "")
 
def digits_only(value):
    return re.sub(r"\D", "", norm(value))
 
def safe_filename(name):
    txt = re.sub(r'[\\/:*?"<>|]+', "_", norm(name))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:120] or "corretor"
 
def clean_emails(value):
    txt = norm(value).replace(",", ";")
    emails = []
    seen = set()
    for part in txt.split(";"):
        email = part.strip()
        if email and email.lower() not in seen:
            emails.append(email)
            seen.add(email.lower())
    return "; ".join(emails)
 
def blocked(status, substatus):
    text = f"{norm(status)} {norm(substatus)}".upper()
    return any(token in text for token in STATUS_BLOQUEADOS)
 
def split_region(value):
    txt = norm(value).upper()
    if txt == "SUL":
        return "SUL"
    if txt in ("NORDESTE", "N/ CO", "N/CO"):
        return "NE_NCO"
    if txt == "SP CAPITAL":
        return "SP_CAPITAL"
    if txt == "SP INTERIOR":
        return "SP_INTERIOR"
    if txt == "SP I":
        return "SP_CAPITAL"
    if txt in ("RJ/ MG/ ES", "RJ/MG/ES", "MG/RJ/ES", "RJ / MG / ES"):
        return "RJ_MG_ES"
    return None
 
def format_brl(value):
    txt = norm(value)
    if not txt:
        return ""
    txt = txt.replace("R$", "").replace(" ", "")
    txt_num = txt.replace(".", "").replace(",", ".")
    try:
        num = float(txt_num)
    except Exception:
        return "R$ " + txt
    br = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {br}"
 
def warn_box(message):
    return (
        '<div style="background:#FFF3CD;border:1px solid #FFEEBA;'
        'padding:8px;margin:10px 0;font-family:Arial,sans-serif;font-size:12px;">'
        f"<b>⚠️ Atenção:</b> {escape(message)}</div>"
    )
 
def html_email_block(region, to_, cc_, subject, rows, warnings):
    style_table = "border-collapse:collapse;font-family:Arial,sans-serif;font-size:12px;width:100%;"
    style_th = "background:#D9E1F2;border:1px solid #1F4E79;padding:6px;text-align:left;"
    style_td = "border:1px solid #1F4E79;padding:6px;vertical-align:top;"
 
    header = (
        '<div style="font-family:Arial,sans-serif;font-size:12px;">'
        f"<p><b>PARA:</b> {escape(to_)}</p>"
        f"<p><b>CC:</b> {escape(cc_)}</p>"
        f"<p><b>ASSUNTO:</b> {escape(subject)}</p>"
        "<hr>"
        + "".join([warn_box(w) for w in warnings]) +
        "<p>Caro corretor, boa tarde!<br>"
        "Venho por meio deste informar que a(s) cotação(ões) se encontra(m) em sistema conforme abaixo:</p>"
        "</div>"
    )
 
    trs = []
    for row in rows:
        cot = escape(norm(row.get(V_COL_COTACAO)))
        seg = escape(norm(row.get(V_COL_SEGUR)))
        vig = escape(norm(row.get(V_COL_VIG)))
        gwp = escape(format_brl(row.get(V_COL_GWP)))
        trs.append(
            f'<tr>'
            f'<td style="{style_td}">{cot}</td>'
            f'<td style="{style_td}">{seg}</td>'
            f'<td style="{style_td}">{vig}</td>'
            f'<td style="{style_td}">{gwp}</td>'
            f'</tr>'
        )
 
    table = (
        f'<table style="{style_table}">'
        '<thead><tr>'
        f'<th style="{style_th}">Nº Cotação</th>'
        f'<th style="{style_th}">Segurado</th>'
        f'<th style="{style_th}">Início Vigência</th>'
        f'<th style="{style_th}">GWP</th>'
        '</tr></thead>'
        f"<tbody>{''.join(trs)}</tbody></table>"
    )
 
    footer = (
        '<div style="font-family:Arial,sans-serif;font-size:12px;">'
        '<p>Por gentileza, solicitamos o envio de um posicionamento sobre o andamento do processo de negociação.<br>'
        'Em caso de dúvidas ou necessidade de apoio, nossa equipe permanece à disposição.</p>'
        '<p>Ressalto que temos uma equipe preparada para atender no canal do 0800 010 0123.<br>'
        'Ficamos no aguardo.</p>'
        f"<p>Atenciosamente,<br><br>{SIGNATURES[region]}</p>"
        '</div>'
    )
    return header + table + footer



def read_delimited_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=",")
 
        rows = []
        for row in reader:
            if not row:
                continue
 
            normalized = {}
            for k, v in row.items():
                normalized[norm(k)] = v
 
            rows.append(normalized)
 
        print("✅ CSV lido corretamente (UTF-8, vírgula)")
        return rows
 
def read_stacked_export_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        raw_lines = [ln.rstrip("\n\r") for ln in f]
 
    raw_lines = [ln for ln in raw_lines if norm(ln) != ""]
 
    start = 0
    if "## Export" in raw_lines:
        start = raw_lines.index("## Export") + 1
 
    header_slice = raw_lines[start:start + len(HEADERS_STACKED_VOL)]
    if header_slice != HEADERS_STACKED_VOL:
        raise Exception("O volumetria.csv não está no formato esperado de export empilhado.")
 
    data = raw_lines[start + len(HEADERS_STACKED_VOL):]
 
    clean_data = []
    for item in data:
        txt = norm(item)
        if txt.upper() == "TOTAL" or txt.startswith("Filtros aplicados:"):
            break
        clean_data.append(txt)
 
    rows = []
    i = 0
    width = len(HEADERS_STACKED_VOL)
 
    while i + width <= len(clean_data):
        chunk = clean_data[i:i + width]
        if re.fullmatch(r"\d+", chunk[0] or ""):
            row = {HEADERS_STACKED_VOL[idx]: chunk[idx] for idx in range(width)}
            rows.append(row)
            i += width
        else:
            i += 1
 
    return rows
 
def load_volumetria(path):
    rows = read_delimited_csv(path)
    if rows and V_COL_COTACAO in rows[0] and V_COL_SUPEX in rows[0]:
        return rows
    return read_stacked_export_csv(path)
 
def main():
    hier_rows = read_delimited_csv(HIER_FILE)
    hier = {}
 
    for row in hier_rows:
        key = digits_only(row.get(H_COL_SUC))
        if not key:
            continue
        hier[key] = (
            clean_emails(row.get(H_COL_GC)),
            clean_emails(row.get(H_COL_SUP)),
        )
 
    vol_rows = load_volumetria(VOL_FILE)
    if not vol_rows:
        raise Exception("volumetria.csv vazio ou não lido corretamente.")
 
    required = [
        V_COL_COTACAO, V_COL_SEGUR, V_COL_VIG, V_COL_GWP,
        V_COL_CORRET, V_COL_SUPEX, V_COL_SUC, V_COL_STATUS,
        V_COL_SUBSTAT, V_COL_EMAIL,
    ]
    missing = [c for c in required if c not in vol_rows[0]]
    if missing:
        raise Exception(f"Colunas não encontradas no volumetria.csv: {missing}")
 
    groups = {}
    meta = {}
    pendencias_all = []
    capturadas = {region: 0 for region in REGION_FOLDERS}
 
    for row in vol_rows:
        region = split_region(row.get(V_COL_SUPEX))
        if not region:
            continue
        if blocked(row.get(V_COL_STATUS), row.get(V_COL_SUBSTAT)):
            continue
 
        capturadas[region] += 1
 
        email_corretor = clean_emails(row.get(V_COL_EMAIL))
        corretor = norm(row.get(V_COL_CORRET))
        suc_raw = norm(row.get(V_COL_SUC))
        num_cot = norm(row.get(V_COL_COTACAO))
 
        if not email_corretor:
            pendencias_all.append({
                "numero_cotacao": num_cot,
                "regiao": region,
                "corretor": corretor,
                "suc_cpd": suc_raw,
                "email_corretor": "",
                "faltando": "Sem e-mail do corretor",
            })
            continue
 
        key = (region, email_corretor.lower())
        groups.setdefault(key, []).append(row)
        if key not in meta:
            meta[key] = {"corretor": corretor, "email": email_corretor}
 
    for (region, email_key), rows in groups.items():
        corretor = meta[(region, email_key)]["corretor"]
        email_corretor = meta[(region, email_key)]["email"]
 
        sucs = sorted({norm(r.get(V_COL_SUC)) for r in rows if norm(r.get(V_COL_SUC))})
        suc_subject = ", ".join(sucs)
        suc_for_file = sucs[0] if sucs else "SEM_SUC"
 
        gc_list = []
        sup_list = []
        missing_gc_any = False
        missing_sup_any = False
 
        for suc in sucs:
            hkey = digits_only(suc)
            gc, sup = hier.get(hkey, ("", ""))
            if gc:
                gc_list.append(gc)
            else:
                missing_gc_any = True
            if sup:
                sup_list.append(sup)
            else:
                missing_sup_any = True
 
        gc = clean_emails(";".join(gc_list))
        sup = clean_emails(";".join(sup_list))
        cc_ = clean_emails(";".join([gc, sup]))
 
        warnings = []
        if not gc and not sup:
            warnings.append("GC e Superintendente não encontrados na hierarquia para as SUCs deste corretor.")
        elif missing_gc_any:
            warnings.append("GC não encontrado para uma ou mais SUCs deste corretor.")
        elif missing_sup_any:
            warnings.append("Superintendente não encontrado para uma ou mais SUCs deste corretor.")
 
        subject = f"COTAÇÃO EM SISTEMA – {corretor} – SUC: {suc_subject}"
        file_name = f"{safe_filename(corretor)}__{safe_filename(suc_for_file)}.html"
        rel_file = f"{region}/{file_name}"
        abs_file = os.path.join(OUTPUT_DIR, region, file_name)
 
        html = (
            '<!doctype html><html><head><meta charset="utf-8">'
            f"<title>{escape(subject)}</title></head><body>"
            f"{html_email_block(region, email_corretor, cc_, subject, rows, warnings)}"
            "</body></html>"
        )
        with open(abs_file, "w", encoding="utf-8") as f:
            f.write(html)
 
        meta[(region, email_key)]["arquivo_html"] = rel_file
 
        if warnings:
            for rr in rows:
                pendencias_all.append({
                    "numero_cotacao": norm(rr.get(V_COL_COTACAO)),
                    "regiao": region,
                    "corretor": corretor,
                    "suc_cpd": norm(rr.get(V_COL_SUC)),
                    "email_corretor": email_corretor,
                    "faltando": " | ".join(warnings),
                })
 
    controle_by_region = {}
 
    for region in REGION_FOLDERS:
        controle_path = os.path.join(OUTPUT_DIR, region, f"controle_envio_{region}.csv")
        pend_path = os.path.join(OUTPUT_DIR, region, f"pendencias_{region}.csv")
 
        prev_map = {}
        if os.path.exists(controle_path):
            prev_rows = read_delimited_csv(controle_path)
            for row in prev_rows:
                num = norm(row.get("numero_cotacao"))
                if num:
                    prev_map[num] = row
 
        controle_rows = []
 
        for (reg, email_key), rows in groups.items():
            if reg != region:
                continue
 
            corretor = meta[(reg, email_key)]["corretor"]
            email_corretor = meta[(reg, email_key)]["email"]
            arquivo_html = meta[(reg, email_key)].get("arquivo_html", "")
 
            for rr in rows:
                num = norm(rr.get(V_COL_COTACAO))
                if not num:
                    continue
 
                prev = prev_map.get(num, {})
 
                controle_rows.append({
                    "numero_cotacao": num,
                    "regiao": region,
                    "corretor": corretor,
                    "email_corretor": email_corretor,
                    "suc_cpd": norm(rr.get(V_COL_SUC)),
                    "arquivo_html": arquivo_html,
                    "enviado": prev.get("enviado", "NAO"),
                    "data_envio": prev.get("data_envio", ""),
                    "observacao": prev.get("observacao", ""),
                })
 
        with open(controle_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "numero_cotacao", "regiao", "corretor", "email_corretor",
                    "suc_cpd", "arquivo_html", "enviado", "data_envio", "observacao",
                ],
            )
            writer.writeheader()
            writer.writerows(controle_rows)
 
        with open(pend_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["numero_cotacao", "regiao", "corretor", "suc_cpd", "email_corretor", "faltando"],
            )
            writer.writeheader()
            writer.writerows([p for p in pendencias_all if p["regiao"] == region])
 
        controle_by_region[region] = controle_rows
 
    def status_icon(value):
        return "✅" if norm(value).upper() == "SIM" else "⏳"
 
    region_titles = {
        "SUL": "SUL",
        "NE_NCO": "NE.N.CO (Nordeste + N/ CO)",
        "SP_CAPITAL": "SP CAPITAL",
        "SP_INTERIOR": "SP INTERIOR",
        "RJ_MG_ES": "RJ/MG/ES",
    }
 
    html_index = []
    html_index.append("<!doctype html>")
    html_index.append('<html><head><meta charset="utf-8"><title>FUP - Index</title></head>')
    html_index.append('<body style="font-family:Arial,sans-serif;font-size:14px;">')
    html_index.append("<h2>FUP Automático</h2>")
    html_index.append("<p><b>Como usar:</b> Clique no corretor → Ctrl+A → Ctrl+C → cole no Outlook.</p>")
    html_index.append("<p><b>Como marcar enviado:</b> Abra o controle da região e altere a coluna <code>enviado</code> para <b>SIM</b>.</p>")
    html_index.append("<hr>")
 
    for region in REGION_FOLDERS:
        html_index.append(f"<h3>{region_titles[region]}</h3>")
        html_index.append(f"<p>output/{region}/controle_envio_{region}.csv | output/{region}/pendencias_{region}.csv</p>")
        html_index.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:12px;width:100%;">')
        html_index.append('<tr style="background:#D9E1F2;"><th>Status</th><th>Corretor</th><th>Email</th><th>SUC-CPD</th><th>Qtde</th><th>Abrir</th></tr>')
 
        region_rows = controle_by_region.get(region, [])
        by_html = {}
        for row in region_rows:
            html_file = row.get("arquivo_html", "")
            by_html.setdefault(html_file, []).append(row)
 
        items = []
        for html_file, rows2 in by_html.items():
            if not html_file:
                continue
            all_sent = all(norm(r.get("enviado")).upper() == "SIM" for r in rows2)
            items.append({
                "status": "SIM" if all_sent else "NAO",
                "corretor": rows2[0]["corretor"],
                "email": rows2[0]["email_corretor"],
                "sucs": ", ".join(sorted({r["suc_cpd"] for r in rows2 if norm(r["suc_cpd"])})),
                "qtd": len(rows2),
                "html": html_file,
            })
 
        items.sort(key=lambda x: (x["status"] == "SIM", x["corretor"]))
 
        if not items:
            html_index.append('<tr><td colspan="6"><i>Sem itens para esta região.</i></td></tr>')
        else:
            for item in items:
                html_index.append(
                    f'<tr>'
                    f'<td style="text-align:center">{status_icon(item["status"])}</td>'
                    f'<td>{escape(item["corretor"])}</td>'
                    f'<td>{escape(item["email"])}</td>'
                    f'<td>{escape(item["sucs"])}</td>'
                    f'<td style="text-align:center">{item["qtd"]}</td>'
                    f'<td><a href="{item["html"]}">Abrir HTML</a></td>'
                    f'</tr>'
                )
 
        html_index.append("</table><br>")
 
    html_index.append("</body></html>")
 
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_index))
 
    print("✅ FINALIZADO")
    for region in REGION_FOLDERS:
        print(f" - {region}: {capturadas.get(region, 0)} linhas capturadas")
    print("✅ HTMLs em:", os.path.abspath(OUTPUT_DIR))
    print("✅ Index:", os.path.abspath(index_path))
 
if __name__ == "__main__":
    main()

