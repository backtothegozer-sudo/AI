#!/usr/bin/env python3
"""
Normalize common missing French accents in FR HTML pages.

By default, the script applies fixes in place.
Use --check to only report files that would change.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PHRASE_REPLACEMENTS = {
    "jusqu'a": "jusqu'à",
    "d'apres": "d'après",
    "a grande echelle": "à grande échelle",
    "a court terme": "à court terme",
    "a l'usage": "à l'usage",
    "a operer": "à opérer",
    "a deployer": "à déployer",
    "des la": "dès la",
    "au dela": "au-delà",
    "au-dela": "au-delà",
    "etats-unis": "États-Unis",
}

WORD_REPLACEMENTS = {
    "souverainete": "souveraineté",
    "donnees": "données",
    "capacite": "capacité",
    "capacites": "capacités",
    "securite": "sécurité",
    "conformite": "conformité",
    "deploiement": "déploiement",
    "deployer": "déployer",
    "controle": "contrôle",
    "acces": "accès",
    "auditabilite": "auditabilité",
    "residence": "résidence",
    "chaine": "chaîne",
    "complete": "complète",
    "evolutives": "évolutives",
    "equipes": "équipes",
    "criticite": "criticité",
    "reversibilite": "réversibilité",
    "fonde": "fondé",
    "recente": "récente",
    "maitrise": "maîtrise",
    "maitriser": "maîtriser",
    "reduire": "réduire",
    "dependance": "dépendance",
    "continuite": "continuité",
    "operationnelle": "opérationnelle",
    "operationnel": "opérationnel",
    "operation": "opération",
    "operations": "opérations",
    "europeennes": "européennes",
    "theorique": "théorique",
    "etat": "état",
    "cyberdefense": "cyberdéfense",
    "ecosysteme": "écosystème",
    "regulees": "régulées",
    "regules": "régulés",
    "evite": "évite",
    "generalisation": "généralisation",
    "disponibilite": "disponibilité",
    "generale": "générale",
    "gere": "géré",
    "meme": "même",
    "regionalises": "régionalisés",
    "tres": "très",
    "tot": "tôt",
    "detaille": "détaille",
    "reduction": "réduction",
    "arrivee": "arrivée",
    "securise": "sécurisé",
    "securisee": "sécurisée",
    "montee": "montée",
    "priorites": "priorités",
    "priorite": "priorité",
    "metier": "métier",
    "actualite": "actualité",
    "strategie": "stratégie",
    "strategique": "stratégique",
    "strategiques": "stratégiques",
    "regionale": "régionale",
    "regions": "régions",
    "references": "références",
    "reference": "référence",
    "numerique": "numérique",
    "numeriques": "numériques",
    "operable": "opérable",
    "operateurs": "opérateurs",
    "factures": "facturés",
    "regionales": "régionales",
    "europeens": "européens",
    "qualite": "qualité",
    "editoriale": "éditoriale",
    "diversite": "diversité",
    "executer": "exécuter",
    "renforcees": "renforcées",
    "cooperation": "coopération",
    "controles": "contrôles",
    "regles": "règles",
    "integre": "intègre",
    "francais": "français",
    "recoit": "reçoit",
    "unites": "unités",
    "appuyee": "appuyée",
    "leve": "lève",
    "economique": "économique",
    "resilience": "résilience",
    "debut": "début",
    "execution": "exécution",
    "demarrer": "démarrer",
    "reduit": "réduit",
    "ecart": "écart",
    "executable": "exécutable",
    "deconnectees": "déconnectées",
    "degradees": "dégradées",
    "interoperables": "interopérables",
    "accelerer": "accélérer",
    "alignes": "alignés",
    "aligne": "aligné",
    "revendique": "revendiqué",
    "communique": "communiqué",
    "dependances": "dépendances",
    "continuites": "continuités",
    "cle": "clé",
    "cybersecurite": "cybersécurité",
    "avancees": "avancées",
    "adaptees": "adaptées",
    "ancrage": "ancrage",
    "fevrier": "février",
    "aout": "août",
    "decembre": "décembre",
    "cree": "créé",
    "evenement": "évènement",
}

META_KEYS = (
    'name="description"',
    'property="og:description"',
    'name="twitter:description"',
    'property="og:title"',
    'name="twitter:title"',
)

SCRIPT_OR_STYLE_RE = re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>)", re.IGNORECASE)
TEXT_NODE_RE = re.compile(r">([^<]+)<")
META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
CONTENT_ATTR_RE = re.compile(r'(\bcontent=")([^"]*)(")', re.IGNORECASE)


def _match_case(src: str, dst: str) -> str:
    if src.isupper():
        return dst.upper()
    if src[:1].isupper():
        return dst[:1].upper() + dst[1:]
    return dst


def apply_dictionary(text: str) -> str:
    updated = text

    for src, dst in PHRASE_REPLACEMENTS.items():
        pattern = re.compile(re.escape(src), re.IGNORECASE)
        updated = pattern.sub(lambda m: _match_case(m.group(0), dst), updated)

    for src, dst in WORD_REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(src)}\b", re.IGNORECASE)
        updated = pattern.sub(lambda m: _match_case(m.group(0), dst), updated)

    return updated


def fix_meta_tag(tag: str) -> str:
    low = tag.lower()
    if not any(key in low for key in META_KEYS):
        return tag
    return CONTENT_ATTR_RE.sub(lambda m: f'{m.group(1)}{apply_dictionary(m.group(2))}{m.group(3)}', tag)


def process_html(html: str) -> str:
    chunks = SCRIPT_OR_STYLE_RE.split(html)
    for i, chunk in enumerate(chunks):
        if i % 2 == 1:
            continue
        chunk = TEXT_NODE_RE.sub(lambda m: f">{apply_dictionary(m.group(1))}<", chunk)
        chunk = META_TAG_RE.sub(lambda m: fix_meta_tag(m.group(0)), chunk)
        chunks[i] = chunk
    return "".join(chunks)


def iter_fr_files(site_dir: Path) -> list[Path]:
    return sorted(
        p for p in site_dir.rglob("*.html")
        if "/en/" not in p.as_posix() and not p.as_posix().endswith("/en.html")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", default="site", help="Site root directory")
    parser.add_argument("--check", action="store_true", help="Only check, do not write files")
    args = parser.parse_args()

    site_dir = Path(args.site_dir).resolve()
    if not site_dir.exists():
        raise SystemExit(f"Site directory not found: {site_dir}")

    changed: list[Path] = []
    for path in iter_fr_files(site_dir):
        original = path.read_text(encoding="utf-8")
        updated = process_html(original)
        if updated != original:
            changed.append(path)
            if not args.check:
                path.write_text(updated, encoding="utf-8")

    if changed:
        mode = "would change" if args.check else "updated"
        print(f"{len(changed)} file(s) {mode}.")
        for item in changed:
            print(item.relative_to(site_dir.parent))
        return 1 if args.check else 0

    print("No accent corrections needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
