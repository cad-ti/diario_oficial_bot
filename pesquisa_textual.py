import re
import unicodedata


def _remover_acentos(txt: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )
    

def _normalizar_token(w: str) -> str:
    # Remove pontuação no início/fim, baixa caixa e tira acentos
    w = re.sub(r'^\W+|\W+$', '', w.lower())
    return _remover_acentos(w)


def _achar_ocorrencias_frase(seq_palavras, palavras_busca):
    """
    Encontra ocorrências contíguas de uma frase (lista de palavras normalizadas)
    dentro de seq_palavras = [(idx_token, token_norm), ...].
    Retorna lista de (start_token_idx, end_token_idx, ord_inicio).
    """
    n = len(palavras_busca)
    if n == 0:
        return []

    ocorrencias = []
    for k in range(len(seq_palavras) - n + 1):
        janela = [w for _, w in seq_palavras[k:k + n]]
        if janela == palavras_busca:
            i_ini = seq_palavras[k][0]
            i_fim = seq_palavras[k + n - 1][0]
            ocorrencias.append((i_ini, i_fim, k))
    return ocorrencias


def localizar_termo(texto, termo, contexto=100):
    """
    Retorna trechos com todas as ocorrências do termo (palavra, frase ou padrão p1+p2~N),
    destacando as ocorrências com <span>.
    As frases são sempre pesquisadas em ocorrências exatas
    """
    # Tokenizar preservando spans
    matches = list(re.finditer(r"\S+|\n", texto))
    tokens = [m.group(0) for m in matches]
    token_spans = [(m.start(), m.end()) for m in matches]
    tokens_norm = [_normalizar_token(t) for t in tokens]
    
    termo_norm = _normalizar_token(termo)
    
    seq_palavras = [(i, t) for i, t in enumerate(tokens_norm) if t]
    trechos_idx = []

    # --- 1) Padrão p1+p2~dist (p1 e p2 podem ser frases compostas) ---
    match = re.match(r'^(.+)\+(.+)~(\d+)$', termo_norm)
    if match:
        p1, p2, dist_str = match.groups()
        distancia_max = int(dist_str)
        p1_words = p1.split()
        p2_words = p2.split()

        occ1 = _achar_ocorrencias_frase(seq_palavras, p1_words)
        occ2 = _achar_ocorrencias_frase(seq_palavras, p2_words)
        if not occ1 or not occ2:
            return []

        for (i1_ini, i1_fim, ord1), (i2_ini, i2_fim, ord2) in (
            (o1, o2) for o1 in occ1 for o2 in occ2
        ):
            if i1_ini < i2_ini and (ord2 - ord1) <= distancia_max:
                inicio = max(i1_ini - contexto, 0)
                fim = min(i2_fim + contexto + 1, len(tokens))
                trechos_idx.append((inicio, fim, [(i1_ini, i1_fim), (i2_ini, i2_fim)]))

    else:
        # --- 2) Termo simples (palavra ou frase sem +~) ---
        palavras_busca = termo_norm.split()

        if len(palavras_busca) == 1:
            alvo = palavras_busca[0]
            indices = [i for i, w in enumerate(tokens_norm) if w == alvo]
            for idx in indices:
                inicio = max(idx - contexto, 0)
                fim = min(idx + contexto + 1, len(tokens))
                trechos_idx.append((inicio, fim, [(idx, idx)]))

        else:
            occ = _achar_ocorrencias_frase(seq_palavras, palavras_busca)
            for (i_ini, i_fim, _ord) in occ:
                inicio = max(i_ini - contexto, 0)
                fim = min(i_fim + contexto + 1, len(tokens))
                trechos_idx.append((inicio, fim, [(i_ini, i_fim)]))

    if not trechos_idx:
        return []

    # --- Unir janelas sobrepostas ---
    trechos_idx.sort(key=lambda x: x[0])
    trechos_unidos = []
    for inicio, fim, spans in trechos_idx:
        if trechos_unidos and inicio <= trechos_unidos[-1][1]:
            trechos_unidos[-1][1] = max(trechos_unidos[-1][1], fim)
            trechos_unidos[-1][2].extend(spans)
        else:
            trechos_unidos.append([inicio, fim, spans[:]])

    for t in trechos_unidos:
        seen = set()
        t[2] = [x for x in t[2] if not (x in seen or seen.add(x))]

    # --- Montar HTML preservando texto original ---
    trechos_final = []
    for inicio, fim, spans_tok in trechos_unidos:
        spans_ord = []
        for s, e in sorted(spans_tok):
            if not spans_ord or s > spans_ord[-1][1]:
                spans_ord.append([s, e])
            else:
                spans_ord[-1][1] = max(spans_ord[-1][1], e)

        span_chars = [(token_spans[s][0], token_spans[e][1]) for s, e in spans_ord]

        win_start = token_spans[inicio][0]
        win_end = token_spans[fim - 1][1]

        partes = []
        cursor = win_start
        for s_char, e_char in sorted(span_chars):
            if s_char >= win_end or e_char <= win_start:
                continue
            s_clip = max(s_char, win_start)
            e_clip = min(e_char, win_end)
            if cursor < s_clip:
                partes.append(texto[cursor:s_clip])
            partes.append(
                '<span class="highlight" style="background:#FFA;">'
                + texto[s_clip:e_clip]
                + "</span>"
            )
            cursor = e_clip
        if cursor < win_end:
            partes.append(texto[cursor:win_end])

        trechos_final.append("".join(partes))

    return trechos_final