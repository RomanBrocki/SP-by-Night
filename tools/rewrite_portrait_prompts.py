from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"
FROZEN_STEMS_PATH = ROOT / "tools" / "frozen_portrait_stems.txt"


def load_frozen_stems() -> set[str]:
    if not FROZEN_STEMS_PATH.exists():
        return set()
    out: set[str] = set()
    for line in FROZEN_STEMS_PATH.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


def die(msg: str) -> None:
    raise SystemExit(msg)


def hpick(eid: str, items: list[str]) -> str:
    if not items:
        return ""
    h = hashlib.sha256(eid.encode("utf-8")).digest()
    n = int.from_bytes(h[:4], "little")
    return items[n % len(items)]


def hpick_n(eid: str, items: list[str], n: int) -> list[str]:
    # Deterministic unique picks. We may need to probe beyond n because hashing can collide.
    want = max(0, n)
    if want <= 0:
        return []

    seen: set[str] = set()
    uniq: list[str] = []
    # Probe more than n attempts to reduce duplicates without introducing randomness.
    for i in range(want * 6):
        x = hpick(f"{eid}:{i}", items)
        if not x or x in seen:
            continue
        seen.add(x)
        uniq.append(x)
        if len(uniq) >= want:
            break

    while len(uniq) < want:
        uniq.append("")
    return uniq


def infer_gender(e: dict) -> str:
    # Prefer name cues first; job titles are unreliable (e.g. a female Xerife).
    name = (e.get("display_name") or "").strip().lower()
    tokens = re.findall(r"[a-zà-ÿ]+", name)

    female_tokens = {
        "ana",
        "bia",
        "rafaela",
        "clara",
        "cecilia",
        "helena",
        "isabel",
        "luiza",
        "marcia",
        "miriam",
        "patricia",
        "regina",
        "soraia",
        "talita",
        "vanessa",
        "lara",
        "paula",
        "camila",
        "jessica",
        "teresa",
        "silvia",
        "marcela",
        "sofia",
        "larissa",
        "beatriz",
        "keiko",
        "hiroko",
        "nara",
        "taina",
        "livia",
        "irene",
        "nina",
        "katia",
        "bruna",
        "vivi",
        "celia",
        "samira",
        "nadia",
        "maya",
        "sabrina",
        "renata",
        "raimunda",
        "vovo",
        "vovó",
        "irma",
        "irmã",
        "delegada",
        "dra",
        "doutora",
    }

    male_tokens = {
        "rodrigo",
        "joao",
        "josé",
        "jose",
        "pedro",
        "paulo",
        "lucas",
        "gabriel",
        "rafael",
        "tiago",
        "victor",
        "vitor",
        "henrique",
        "daniel",
        "bruno",
        "eduardo",
        "augusto",
        "artur",
        "dante",
        "hector",
        "igor",
        "yuri",
        "yusuf",
        "samir",
        "farid",
        "donato",
        "raul",
        "otavio",
        "rui",
        "severino",
        "damiao",
        "elias",
        "wesley",
        "caua",
        "afonso",
        "dario",
        "mateus",
        "nando",
        "nico",
        "ravi",
        "renato",
        "ricardo",
        "helio",
        "bento",
        "caio",
        "jonas",
        "vlado",
        "padre",
    }

    if any(t in female_tokens for t in tokens):
        return "f"
    if any(t in male_tokens for t in tokens):
        return "m"

    role = (e.get("role") or "").lower()
    feminine_role_markers = [
        "baronesa",
        "primógena",
        "primogena",
        "harpia",
        "senescal",
        "curadora",
        "guardiã",
        "guardia",
    ]
    masculine_role_markers = [
        "barão",
        "barao",
        "primógeno",
        "primogeno",
        "príncipe",
        "principe",
        "xerife",
        "hound",
        "executor",
    ]
    for m in feminine_role_markers:
        if m in role:
            return "f"
    for m in masculine_role_markers:
        if m in role:
            return "m"

    # Prefer explicit cues already in the prompt only as a true last resort. This is fragile:
    # a single bad prompt should not keep propagating forever.
    p = str(e.get("portrait_prompt") or "").lower()
    if "mulher com forma feminina" in p and "homem com forma masculina" not in p:
        return "f"
    if "homem com forma masculina" in p and "mulher com forma feminina" not in p:
        return "m"
    return "m"


def beauty_for(e: dict, g: str) -> str:
    clan = (e.get("clan") or "").lower()
    kind = (e.get("kind") or "").lower()
    role = (e.get("role") or "").lower()
    tier = (e.get("tier") or "").upper()

    def gm(m: str, f: str) -> str:
        return f if g == "f" else m

    if kind == "kindred":
        if "nosferatu" in clan:
            return hpick(
                e["id"],
                [
                    gm("feio", "feia") + " (tracos duros, memoravel)",
                    gm("horroroso", "horrorosa") + " (deformidade, cicatrizes)",
                    gm("feio", "feia") + " (assimetrico, marcante)",
                ],
            )
        if "toreador" in clan:
            return hpick(
                e["id"],
                [
                    gm("muito belo", "muito bela") + " (atracao marcante)",
                    gm("extremamente belo", "extremamente bela") + " (presenca quase hipnotica)",
                ],
            )
        if tier in ("S", "A"):
            return hpick(
                e["id"],
                [
                    gm("bonito", "bonita") + " (atracao fria)",
                    gm("muito belo", "muito bela") + " (presenca de poder)",
                ],
            )
        if "harpia" in role or "senescal" in role:
            return gm("muito belo", "muito bela") + " (estilo impecavel)"
        return hpick(
            e["id"],
            [
                gm("bonito", "bonita") + " (atraente)",
                "comum (nao chama atencao ate falar)",
            ],
        )

    # ghouls / mortals
    return hpick(
        e["id"],
        [
            "comum (rosto de rua)",
            gm("bonito", "bonita") + " (aparencia cuidada)",
        ],
    )


def build_prompt(e: dict) -> str:
    eid = e["id"]
    kind = (e.get("kind") or "kindred").lower()
    clan = (e.get("clan") or "").strip()
    sect = (e.get("sect") or "").strip()
    role = (e.get("role") or "").strip()
    domain = (e.get("domain") or "").strip()
    appearance = (e.get("appearance_explicit") or "").strip()
    if not appearance:
        # If missing, keep explicit but neutral to avoid nonsense.
        appearance = "pessoa brasileira (pele e tracos nao especificados)"

    g = infer_gender(e)
    gender_txt = "mulher com forma feminina" if g == "f" else "homem com forma masculina"
    beauty = beauty_for(e, g)
    signature_style = (e.get("signature_style") or "").strip()

    clan_l = clan.lower()
    # Visual cues per clan: make the prompt "read" like the clan without becoming generic.
    clan_cues = ""
    if kind == "kindred" and "gangrel" in clan_l:
        clan_cues = hpick(
            eid,
            [
                "Arquetipo visual: predador feral urbano, postura alerta, olhos com brilho animal (sem parecer cosplay).",
                "Arquetipo visual: caçador de fronteira, vibe de lobo de rua, cicatrizes de mato e asfalto.",
            ],
        )
    elif kind == "kindred" and ("banu" in clan_l or "haqim" in clan_l):
        clan_cues = hpick(
            eid,
            [
                "Arquetipo visual: juiz noturno, autocontrole rigido, olhar avaliador; devocao discreta (contas pretas sem simbolos legiveis).",
                "Arquetipo visual: assassino disciplinado, elegancia contida; presenca de perigo frio.",
            ],
        )
    elif kind == "kindred" and "nosferatu" in clan_l:
        clan_cues = hpick(
            eid,
            [
                "Arquetipo visual: goblin urbano (fantasia), criatura de esgoto em foto realista; desconfortavel de olhar.",
                "Arquetipo visual: bruxa do concreto (fantasia), figura encurvada, sombra viva; rosto inquietante.",
                "Arquetipo visual: orc esguio (fantasia urbana), pele acinzentada, olhos brilhantes; vibe subterranea.",
            ],
        )
    elif kind == "kindred" and "tzimisce" in clan_l:
        clan_cues = hpick(
            eid,
            [
                "Arquetipo visual: cirurgiao bruxo (fantasia sombria), beleza errada, olhar de taxidermista; higiene quase clinica.",
                "Arquetipo visual: aristocrata de horror (fantasia), gestos precisos, inquietante como uma estatua viva.",
            ],
        )
    elif kind == "kindred" and "tremere" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: ocultista academico, disciplina ritual, frieza calculada."])
    elif kind == "kindred" and "malkavian" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: vidente quebrado, olhar que nao bate com o sorriso; estranheza sutil."])
    elif kind == "kindred" and "ministry" in clan_l:
        clan_cues = hpick(
            eid,
            [
                "Arquetipo visual: sedutor de culto, sorriso serpentino, brilho de boate e templo; charme perigoso.",
                "Arquetipo visual: pregador de prazer e culpa, olhar magnetico; insinuacao de serpente (sem fantasia literal).",
            ],
        )
    elif kind == "kindred" and "hecata" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: agente funerario, elegancia sombria, calma de necropole."])
    elif kind == "kindred" and "lasombra" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: sombra social, fe impecavel ou cinismo impecavel; perigo silencioso."])
    elif kind == "kindred" and "brujah" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: revolucionario noturno, tensao nos ombros, energia de briga contida."])
    elif kind == "kindred" and "ravnos" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: trapaceiro elegante, sorriso rapido, olhos que medem saidas."])
    elif kind == "kindred" and "salubri" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: curador maldito, serenidade cansada; bondade perigosa."])
    elif kind == "kindred" and "thin blood" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: sobrevivente da margem, improviso, paranoia e rua."])
    elif kind == "kindred" and "caitiff" in clan_l:
        clan_cues = hpick(eid, ["Arquetipo visual: sem selo, sem uniforme; adaptacao e raiva fria."])

    # Face/hair variations
    face_shapes = ["rosto oval", "rosto angular", "rosto quadrado", "rosto alongado", "rosto em coracao"]
    eyes = [
        "olhos castanhos escuros, olhar atento",
        "olhos castanhos, olhar firme",
        "olhos verde-avelanados, olhar predatorio contido",
        "olhos azul-acinzentados, olhar frio",
        "olhos negros (castanho muito escuro), olhar cansado",
    ]
    hair = [
        "cabelo preto liso",
        "cabelo castanho-escuro ondulado",
        "cabelo cacheado curto",
        "cabelo raspado nas laterais com topo curto",
        "cabelo preso em coque baixo",
        "cabelo preso em rabo baixo",
        "cabelo comprido preso em tranca baixa",
    ]
    details = [
        "cicatriz pequena no supercilio",
        "piercing discreto no nariz",
        "brincos pequenos (um ponto de luz)",
        "anel simples de metal escovado",
        "olheiras leves",
        "sobrancelhas bem definidas",
        "barba curta bem aparada",
        "sem sorriso",
        "pinta pequena proxima a boca",
        "sardas discretas no nariz",
        "cicatriz fina na bochecha (quase apagada)",
    ]
    # Avoid generating prompts with incoherent anatomy/traits for the chosen presentation.
    details_f = [d for d in details if "barba" not in d and "bigode" not in d]
    details_m = details

    # Clan-specific face cues.
    if kind == "kindred" and "nosferatu" in clan_l:
        eyes = [
            "olhos castanhos escuros, olhar atento e estranho (quase predatorio)",
            "olhos brilhantes, olhar de bicho em tunel (sem parecer lente de contato)",
            "olhos amarelados/castanhos, olhar inquieto e desconfortavel",
        ]
        hair = [
            "cabelo ralo e escuro, desalinhado",
            "cabelo curto arrepiado e irregular",
            "cabelo grudado pela umidade, mechas finas",
        ]
        # Fantasy-monster cues (explicitly requested). Still keep it photo-realistic.
        details_m += [
            "pele acinzentada e fria (fantasia urbana, sem parecer maquiagem)",
            "orelhas levemente pontudas (fantasia sutil)",
            "dentes irregulares quando entreabre a boca (sem gore)",
            "postura encurvada, ombros para frente",
        ]
        details_f = [d for d in details_m if "barba" not in d and "bigode" not in d]

    # Clothing/props by clan/role
    if kind == "kindred" and "ventrue" in clan.lower():
        outfit = hpick(eid, ["terno grafite fosco", "terno azul-marinho bem cortado", "blazer escuro e camisa clara sem padrao"])
        prop = hpick(eid, ["", "", "relogio simples", "pasta de couro sem marca", "cartao sem texto entre os dedos"])
        bg = hpick(eid, ["hall de condominio de luxo a noite", "sala de reuniao corporativa escura", "sacada com luzes da cidade e chuva fina"])
        light = hpick(eid, ["iluminacao fria de thriller", "luz lateral dura e contraste alto", "luz quente de interior com sombras"])
    elif kind == "kindred" and "toreador" in clan.lower():
        outfit = hpick(eid, ["roupa de gala minimalista", "vestido/terno preto geometrico", "casaco elegante sobre os ombros"])
        prop = hpick(eid, ["", "", "taca de vinho tinto sem etiqueta", "luvas finas dobradas na mao", "convite dobrado sem texto"])
        bg = hpick(eid, ["vernissage noturno com bokeh de lustres", "corredor de teatro com luz quente", "rua de Pinheiros com neon desfocado"])
        light = hpick(eid, ["luz quente de evento", "recorte suave no rosto", "contraluz com bokeh"])
    elif kind == "kindred" and "nosferatu" in clan.lower():
        outfit = hpick(eid, ["capuz impermeavel escuro", "moletom grande e jaqueta surrada", "casaco pesado com gola alta"])
        prop = hpick(eid, ["", "lanterna industrial", "celular antigo sem marca", "fita isolante no pulso (improviso)"])
        bg = hpick(eid, ["tunel de manutencao com concreto molhado", "sala tecnica com canos e vapor", "escadaria de metro com luz verde"])
        light = hpick(eid, ["chiaroscuro com contraste alto", "luz de sodio amarela", "luz fria dura lateral"])
    elif kind == "kindred" and "tremere" in clan.lower():
        outfit = hpick(eid, ["sueter escuro e jaleco amassado", "blazer vinho e camisa grafite", "roupa discreta com luvas nitrilicas"])
        # Keep books rare; avoid everyone holding one. Empty hands often read better for portraits.
        prop = hpick(
            eid,
            [
                "",
                "",
                "frasco de vidro ambar sem rotulo",
                "pasta com lacre (sem texto)",
                "anel simples de metal escovado",
                "livro antigo de capa de couro sem simbolos legiveis",
            ],
        )
        bg = hpick(eid, ["corredor de laboratorio frio", "biblioteca com estantes altas", "sala de arquivo com luz de abajur"])
        light = hpick(eid, ["luz fria fluorescente", "luz baixa de abajur com sombras", "luz lateral controlada"])
    elif kind == "kindred" and ("lasombra" in clan.lower()):
        outfit = hpick(eid, ["terno preto sem brilho", "sobretudo escuro", "camisa branca simples e casaco preto"])
        prop = hpick(eid, ["", "", "terco discreto no bolso", "anel de prata simples", "rosario de bolso (sem simbolos legiveis)"])
        bg = hpick(eid, ["corredor antigo com luz amarela", "sala de confissao com sombras profundas", "igreja vazia a noite (bancos desfocados)"])
        light = hpick(eid, ["contraste alto com sombras densas", "luz amarela de corredor", "luz lateral dura"])
    elif kind == "kindred" and ("hecata" in clan.lower()):
        outfit = hpick(eid, ["sobretudo preto pesado", "roupa social escura sem brilho", "casaco cinza com gola alta"])
        prop = hpick(eid, ["", "agenda preta sem texto", "luvas finas de couro", "terco de contas gastas"])
        bg = hpick(eid, ["portao de cemiterio com neblina", "capela pequena com luz de vela", "sala de funeraria com cortina pesada"])
        light = hpick(eid, ["luz amarela com neblina", "luz baixa e fria", "luz de vela com sombras"])
    elif kind == "kindred" and ("malkavian" in clan.lower()):
        outfit = hpick(eid, ["blazer texturizado e gola alta", "jaqueta jeans com detalhe unico", "roupa discreta de consultorio"])
        prop = hpick(eid, ["", "", "bloquinho e caneta", "camera pequena sem marca", "recorte de jornal dobrado (sem texto legivel)"])
        bg = hpick(eid, ["cafe 24h com neon e chuva na janela", "estacao de metro com luz verde", "consultorio a noite com arquivos desfocados"])
        light = hpick(eid, ["luz fria de consultorio", "neon colorido desfocado", "luz lateral suave"])
    elif kind == "kindred" and ("banu" in clan.lower() or "haqim" in clan.lower()):
        outfit = hpick(eid, ["blazer preto bem cortado", "terno escuro sem gravata", "jaqueta curta e roupa neutra"])
        prop = hpick(eid, ["", "luvas finas pretas", "contas pretas (devocao discreta)", "adaga curta embainhada (discreta, sem sangue)"])
        bg = hpick(eid, ["corredor de cartorio antigo", "sala de arquivos juridicos", "rua vazia com azulejos antigos"])
        light = hpick(eid, ["luz amarela velha", "luz lateral dura", "luz fria controlada"])
    elif kind == "kindred" and "tzimisce" in clan.lower():
        outfit = hpick(eid, ["camisa social escura e avental de couro fino", "sobretudo escuro impecavel", "roupa escura com luvas finas (cirurgicas ou de couro)"])
        prop = hpick(eid, ["", "fita metrica antiga", "estojo fino (bisturi guardado, nao visivel)", "alfinete/pino de lapela em osso (sem gore)"])
        bg = hpick(eid, ["sala de cirurgia antiga (sem sangue)", "atelier de taxidermia com frascos desfocados", "corredor frio de clinica vazia"])
        light = hpick(eid, ["luz fria cirurgica", "luz baixa e recorte duro", "luz lateral controlada"])
    elif kind == "kindred" and "ministry" in clan.lower():
        outfit = hpick(eid, ["roupa preta sedosa com detalhe dourado discreto", "jaqueta de couro bem cortada e gola alta", "vestido/terno preto com acessorio de cobra (sutil)"])
        prop = hpick(eid, ["", "", "anel com motivo de serpente (sutil)", "taça de vinho tinto sem etiqueta", "lenço perfumado dobrado (sem texto)"])
        bg = hpick(eid, ["boate com neon dourado desfocado", "sala de culto luxuosa (velas, sem simbolos legiveis)", "corredor de hotel com luz quente"])
        light = hpick(eid, ["neon quente e sombras", "luz de vela com recortes", "luz quente de interior com sombras"])
    elif kind in ("ghoul", "mortal"):
        outfit = hpick(eid, ["roupa de trabalho discreta", "jaqueta surrada e camiseta lisa", "uniforme sem insignia"])
        # Avoid the clipboard/caderno monotony: many portraits read better with empty hands or small everyday props.
        prop = hpick(
            eid,
            [
                "",
                "",
                "celular com tela apagada",
                "radio pequeno",
                "cigarro apagado entre os dedos",
                "copo descartavel de cafe (sem marca)",
                "chaveiro simples (sem logos)",
                "fones de ouvido pendurados no pescoco",
                "crachá virado (sem texto legivel)",
            ],
        )
        bg = hpick(eid, ["portaria com luz fria", "doca/galpao com containers desfocados", "rua molhada com poste de luz"])
        light = hpick(eid, ["luz fria", "luz amarela de rua", "contraste alto"])
    else:
        outfit = hpick(eid, ["roupa escura discreta", "jaqueta urbana", "blazer simples"])
        prop = hpick(
            eid,
            [
                "",
                "",
                "cigarro apagado",
                "isqueiro metalico simples",
                "celular antigo sem marca",
                "chaveiro simples (sem logos)",
                "anel simples",
            ],
        )
        bg = hpick(eid, ["rua molhada com neon desfocado", "sala escura com luz lateral", "corredor antigo"])
        light = hpick(eid, ["luz lateral", "neon", "luz quente"])

    f0 = hpick(eid, face_shapes)
    e0 = hpick(eid, eyes)
    h0 = hpick(eid, hair)
    dpool = details_f if g == "f" else details_m
    d0, d1 = hpick_n(eid, dpool, 2)

    # Build final prompt (no HTML/tags, clear and explicit).
    parts = []
    parts.append("Retrato individual realista, meio-corpo, camera ao nivel dos olhos, lente 50mm, alta definicao.")
    parts.append(f"{gender_txt}, {appearance}. {beauty}.")
    if clan_cues:
        parts.append(clan_cues)
    parts.append(f"Rosto: {f0}; {e0}; {d0}; {d1}.")
    parts.append(f"Cabelo: {h0}.")
    if g == "f":
        if "toreador" in clan.lower():
            parts.append("Detalhes: unhas pintadas em cor escura (vinho ou preto), maquiagem bem acabada.")
        else:
            parts.append(hpick(eid, ["Detalhes: maquiagem discreta, unhas bem cuidadas.", "Detalhes: sem maquiagem evidente, unhas bem cuidadas.", "Detalhes: maquiagem leve, unhas sem esmalte."]))
    if role:
        parts.append(f"Vibe/funcao: {role}.")
    if sect:
        parts.append(f"Contexto: {('Kindred ' if kind=='kindred' else '')}{sect}.")
    if domain:
        parts.append(f"Cenario: {domain}. Fundo: {bg}.")
    if signature_style:
        ss = signature_style
        if ss and ss[-1] not in ".!?":
            ss += "."
        parts.append(f"Assinatura pessoal: {ss}")
    parts.append(f"Roupa: {outfit}.")
    if prop:
        parts.append(f"Objeto: {prop}.")
    parts.append(f"Iluminacao: {light}. Estilo: cinematic noir, textura de filme, cores naturais.")
    parts.append("Regras: sem texto na imagem, sem logotipos, sem marcas d'agua, sem rabiscos nas maos, sem dedos extras, sem artefatos estranhos, sem simbolos aleatorios.")

    return " ".join(p.strip() for p in parts if p.strip())


def main() -> int:
    if not SRC.exists():
        die(f"missing {SRC}")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    frozen = load_frozen_stems()
    changed = 0
    for e in entities:
        if not e.get("id"):
            continue
        if (e.get("file_stem") or "") in frozen:
            continue
        # Always rewrite to enforce the strict style requirements and remove legacy low-detail prompts.
        e["portrait_prompt"] = build_prompt(e)
        changed += 1

    data["entities"] = entities
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"rewrote prompts for {changed} entities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
