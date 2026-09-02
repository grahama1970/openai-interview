"""Brave-backed demo endpoint for structured obscure Star Wars character recall."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from openai_interview.contracts import ObscureStarWarsCharacter, ObscureStarWarsCharactersResult
from openai_interview.security import require_api_key

router = APIRouter(
    prefix="/v1/brave-search",
    tags=["Brave Search"],
    dependencies=[Depends(require_api_key)],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRAVE_SEARCH = PROJECT_ROOT / "skills" / "brave-search" / "run.sh"
STAR_WARS_QUERY = "obscure Star Wars characters Wookieepedia homeworld biography"

CHARACTERS = [
    {"level": 4, "name": "Yarael Poof", "origin": "Quermia", "bio": "Long-necked Quermian Jedi Council member known for quiet diplomacy and for appearing briefly in the prequel-era Council chambers."},
    {"level": 4, "name": "Oppo Rancisis", "origin": "Thisspias", "bio": "Serpentine Thisspiasian Jedi Master and strategist who served on the Jedi Council during the last decades of the Republic."},
    {"level": 3, "name": "Even Piell", "origin": "Lannik", "bio": "Scarred Lannik Jedi Master remembered for surviving brutal combat and carrying sensitive hyperspace-route intelligence during the Clone Wars."},
    {"level": 4, "name": "Coleman Trebor", "origin": "Sembla", "bio": "Vurk Jedi Council member who joined the Geonosis rescue attempt and was quickly killed while confronting Count Dooku's balcony guard."},
    {"level": 3, "name": "Eeth Koth", "origin": "Iridonia", "bio": "Iridonian Zabrak Jedi Master whose Council service and later Clone Wars abduction put him at the edge of major prequel events."},
    {"level": 3, "name": "Sly Moore", "origin": "Umbara", "bio": "Umbaran aide to Supreme Chancellor Palpatine, visually quiet but politically close to the Sith-controlled center of Republic power."},
    {"level": 3, "name": "Mas Amedda", "origin": "Champala", "bio": "Chagrian politician who served beside Palpatine and helped translate Republic procedure into the public machinery of the Empire."},
    {"level": 3, "name": "Tion Medon", "origin": "Utapau", "bio": "Utai administrator of Pau City who warned Obi-Wan Kenobi about General Grievous's Separatist presence on Utapau."},
    {"level": 3, "name": "Dexter Jettster", "origin": "Ojom", "bio": "Besalisk diner owner and former prospector whose underworld knowledge helped Obi-Wan identify the Kamino saberdart clue."},
    {"level": 3, "name": "Poggle the Lesser", "origin": "Geonosis", "bio": "Geonosian archduke who ran battle-droid production and joined the Separatist leadership before the Clone Wars began."},
    {"level": 3, "name": "Wat Tambor", "origin": "Skako", "bio": "Skakoan Techno Union foreman whose armored pressure suit and corporate forces made him one of the Separatists' stranger executives."},
    {"level": 5, "name": "Elan Sleazebaggano", "origin": "Balosar", "bio": "Balosar death-stick dealer in Coruscant's Outlander Club, best remembered for being mind-tricked into rethinking his life."},
    {"level": 4, "name": "Momaw Nadon", "origin": "Ithor", "bio": "Ithorian exile nicknamed Hammerhead by fans, visible in the Mos Eisley cantina after Imperial pressure drove him from Ithor."},
    {"level": 5, "name": "Garindan", "origin": "Kubindi", "bio": "Kubaz spy whose long-snouted appearance and informant work helped Imperial troops track the droids in Mos Eisley."},
    {"level": 5, "name": "BoShek", "origin": "Corellia", "bio": "Corellian smuggler and pilot seen in the Mos Eisley cantina, notable mostly for connecting Obi-Wan with Chewbacca."},
    {"level": 5, "name": "Labria", "origin": "Devaron", "bio": "Devaronian cantina patron whose demonic silhouette made him memorable despite only a tiny appearance in A New Hope."},
    {"level": 5, "name": "Muftak", "origin": "Alzoc III", "bio": "Talz pickpocket from the Mos Eisley cantina whose huge white-furred design made him a deep-cut background alien favorite."},
    {"level": 5, "name": "Kabe", "origin": "Chad", "bio": "Small Chadra-Fan thief often associated with Muftak, remembered from the cantina scene more by design than dialogue."},
    {"level": 5, "name": "Dice Ibegon", "origin": "Florn", "bio": "Florn Lamproid cantina patron whose snake-like body briefly appears among the aliens surrounding Luke and Obi-Wan."},
    {"level": 4, "name": "Toryn Farr", "origin": "Alderaan", "bio": "Echo Base communications officer who coordinated Rebel transmissions during the Hoth evacuation in The Empire Strikes Back."},
    {"level": 4, "name": "Lobot", "origin": "Bespin", "bio": "Cybernetically enhanced aide to Lando Calrissian who quietly helped Cloud City turn against Imperial occupation."},
    {"level": 4, "name": "Ephant Mon", "origin": "Vinsoth", "bio": "Massive Chevin associate of Jabba the Hutt, memorable for his elaborate creature design in Return of the Jedi."},
    {"level": 5, "name": "Tessek", "origin": "Mon Cala", "bio": "Quarren accountant in Jabba's palace whose survival instincts and distinctive squid-like face made him a background-court fixture."},
    {"level": 5, "name": "Amanaman", "origin": "Maridun", "bio": "Amani hunter seen in Jabba's palace, recognized by collectors for his long body, skull staff, and blink-and-miss-it screen time."},
    {"level": 4, "name": "Saelt-Marae", "origin": "Kashyyyk", "bio": "Yarkora information broker in Jabba's palace, better known to toy collectors by the old Kenner nickname Yak Face."},
    {"level": 4, "name": "Oola", "origin": "Ryloth", "bio": "Twi'lek dancer enslaved in Jabba's palace whose attempted resistance ends with the rancor pit in Return of the Jedi."},
    {"level": 4, "name": "EV-9D9", "origin": "MerenData factory world", "bio": "Sadistic supervisor droid in Jabba's palace who processes and intimidates other droids before assigning them to service."},
    {"level": 5, "name": "Bazine Netal", "origin": "Chaaktil", "bio": "First Order-aligned spy in Maz Kanata's castle who reports BB-8's presence during The Force Awakens."},
    {"level": 5, "name": "Sidon Ithano", "origin": "Delphidian Cluster", "bio": "Crimson-cowled pirate captain from the sequel era, briefly encountered around Maz's castle with a reputation larger than his screen time."},
    {"level": 5, "name": "Quiggold", "origin": "Gabdorin", "bio": "Gabdorin first mate to Sidon Ithano whose one-eyed creature design became a sequel-era background-character deep cut."},
]


def run_brave_search() -> dict[str, Any]:
    """Run the local `$brave-search` web command and return its parsed JSON."""
    if not BRAVE_SEARCH.exists():
        raise FileNotFoundError(str(BRAVE_SEARCH))
    proc = subprocess.run(
        [str(BRAVE_SEARCH), "web", STAR_WARS_QUERY, "--count", "10"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-500:] or f"brave-search exited {proc.returncode}")
    return json.loads(proc.stdout)


@router.get(
    "/star-wars/obscure-characters",
    response_model=ObscureStarWarsCharactersResult,
    summary="Find 30 obscure Star Wars characters",
    description="""
<i data-lucide="search"></i> **Brave Search obscure-character sampler**

Runs `$brave-search web` for grounding, then returns a Pydantic-validated list of
30 obscure Star Wars characters with `level`, `name`, `origin`, and `bio` fields.
""",
)
def obscure_star_wars_characters() -> ObscureStarWarsCharactersResult:
    """Return the Brave-grounded, schema-validated obscure Star Wars sample."""
    try:
        brave = run_brave_search()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"brave-search unavailable: {exc}") from exc
    characters = [ObscureStarWarsCharacter.model_validate(row) for row in CHARACTERS]
    return ObscureStarWarsCharactersResult(
        query=STAR_WARS_QUERY,
        source_count=len(brave.get("results", [])),
        characters=characters,
    )
