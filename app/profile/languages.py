"""Fixed catalog of supported languages and their accents.

`LanguageName` and `AccentName` are the single source of truth for what values are valid — every layer (Pydantic models, DB, iOS UI) references these Literal types, never raw `str`. Each value is the human-readable name itself: stored verbatim in the DB, sent verbatim in API payloads, displayed verbatim in the UI. The `LANGUAGES` tuple declares which accents belong to which language; the module-load asserts at the bottom guarantee the Literal types and the tuple data stay in agreement."""

from dataclasses import dataclass
from typing import Literal, get_args

LanguageName = Literal[
    "English",
    "Spanish",
    "Mandarin Chinese",
    "Cantonese",
    "French",
    "German",
    "Japanese",
    "Korean",
    "Italian",
    "Portuguese",
    "Russian",
    "Arabic",
    "Hindi",
    "Bengali",
    "Vietnamese",
    "Thai",
    "Indonesian",
    "Turkish",
    "Polish",
    "Dutch",
    "Swedish",
    "Norwegian",
    "Danish",
    "Finnish",
    "Greek",
    "Hebrew",
    "Hungarian",
    "Czech",
    "Slovak",
    "Ukrainian",
    "Romanian",
    "Persian",
    "Tagalog",
    "Swahili",
    "Malay",
    "Urdu",
    "Latin",
    "Irish",
    "Scottish Gaelic",
    "Welsh",
    "Hawaiian",
    "Zulu",
    "Haitian Creole",
    "Yiddish",
    "Navajo",
    "Esperanto",
    "High Valyrian",
    "Klingon",
]


AccentName = Literal[
    # English
    "American",
    "British",
    "Australian",
    "Canadian",
    "Irish English",
    "Scottish English",
    "South African",
    "New Zealand",
    "Indian English",
    "Singaporean",
    # Spanish
    "Castilian",
    "Mexican",
    "Argentinian",
    "Colombian",
    "Andalusian",
    "Caribbean",
    "Chilean",
    "Peruvian",
    # Mandarin Chinese
    "Beijing Standard",
    "Taiwanese",
    "Singaporean Mandarin",
    "Northeastern Mandarin",
    # Cantonese
    "Hong Kong",
    "Guangzhou",
    # French
    "Parisian",
    "Québécois",
    "Belgian French",
    "Swiss French",
    "African French",
    # German
    "Hochdeutsch",
    "Austrian",
    "Swiss German",
    "Bavarian",
    "Berliner",
    # Japanese
    "Tokyo Standard",
    "Kansai",
    "Tohoku",
    "Kyushu",
    "Hokkaido",
    "Okinawan",
    # Korean
    "Seoul Standard",
    "Gyeongsang",
    "Jeolla",
    "Chungcheong",
    "Jeju",
    # Italian
    "Standard Italian",
    "Roman",
    "Neapolitan",
    "Sicilian",
    "Milanese",
    "Venetian",
    # Portuguese
    "European Portuguese",
    "Brazilian (Carioca)",
    "Brazilian (Paulista)",
    "African Portuguese",
    # Russian
    "Moscow Standard",
    "Saint Petersburg",
    "Southern Russian",
    "Northern Russian",
    # Arabic
    "Modern Standard Arabic",
    "Egyptian",
    "Levantine",
    "Gulf",
    "Maghrebi",
    "Iraqi",
    # Hindi
    "Standard Hindi",
    "Mumbai",
    "Delhi Hindi",
    "Hyderabadi",
    # Bengali
    "Kolkata Standard",
    "Dhaka Standard",
    "Sylheti",
    # Vietnamese
    "Northern (Hanoi)",
    "Central (Hue)",
    "Southern (Saigon)",
    # Thai
    "Central (Bangkok)",
    "Northern (Lanna)",
    "Northeastern (Isan)",
    "Southern Thai",
    # Indonesian
    "Jakartan Standard",
    "Javanese",
    "Sundanese",
    "Balinese",
    # Turkish
    "Istanbul Standard",
    "Anatolian",
    "Cypriot Turkish",
    # Polish
    "Standard Polish",
    "Silesian Polish",
    "Goral",
    # Dutch
    "Hollands Standard",
    "Flemish",
    "Surinamese Dutch",
    # Swedish
    "Rikssvenska",
    "Finland Swedish",
    "Skanska",
    "Gotlandic",
    # Norwegian
    "Bokmål Standard",
    "Nynorsk",
    "Bergen",
    # Danish
    "Rigsdansk",
    "Jutlandic",
    "Bornholmsk",
    # Finnish
    "Standard Finnish",
    "Savonian",
    "Ostrobothnian",
    # Greek
    "Athenian Standard",
    "Cypriot Greek",
    "Cretan",
    # Hebrew
    "Modern Israeli",
    "Ashkenazi",
    "Sephardic",
    "Mizrahi",
    # Hungarian
    "Standard Hungarian",
    "Székely",
    "Csángó",
    # Czech
    "Bohemian Standard",
    "Moravian",
    "Silesian Czech",
    # Slovak
    "Western Slovak",
    "Central Slovak",
    "Eastern Slovak",
    # Ukrainian
    "Standard Ukrainian",
    "Western Ukrainian",
    "Eastern Ukrainian",
    "Polissian",
    # Romanian
    "Muntenian Standard",
    "Moldavian",
    "Transylvanian",
    "Bănățean",
    # Persian
    "Tehrani Standard",
    "Afghan Dari",
    "Tajik",
    # Tagalog
    "Manila Standard",
    "Batangas",
    "Marinduque",
    # Swahili
    "Kenyan Swahili",
    "Tanzanian Swahili",
    "Ugandan Swahili",
    "Congolese Swahili",
    # Malay
    "Malaysian Standard",
    "Kelantanese",
    "Kedahan",
    "Sarawakian",
    # Urdu
    "Lucknowi",
    "Karachi",
    "Delhi Urdu",
    # Latin
    "Classical Latin (Reconstructed)",
    "Ecclesiastical Latin",
    # Irish (Gaelic)
    "Munster Irish",
    "Connacht Irish",
    "Ulster Irish",
    # Scottish Gaelic
    "Lewis Gaelic",
    "Skye Gaelic",
    "Argyll Gaelic",
    # Welsh
    "North Welsh",
    "South Welsh",
    "Patagonian Welsh",
    # Hawaiian
    "Niʻihau Hawaiian",
    "Standard Hawaiian",
    # Zulu
    "Standard Zulu",
    "Lala",
    "Qwabe",
    # Haitian Creole
    "Cap-Haïtien",
    "Port-au-Prince",
    "Les Cayes",
    # Yiddish
    "YIVO Standard",
    "Galician Yiddish",
    "Litvish",
    "Polish Yiddish",
    # Navajo
    "Western Navajo",
    "Eastern Navajo",
    # Esperanto (constructed)
    "Standard Esperanto",
    # High Valyrian (constructed)
    "Standard High Valyrian",
    # Klingon (constructed)
    "Standard Klingon",
]


@dataclass(frozen=True)
class Language:
    name: LanguageName
    accents: tuple[AccentName, ...]


LANGUAGES: tuple[Language, ...] = (
    Language(
        name="English",
        accents=(
            "American",
            "British",
            "Australian",
            "Canadian",
            "Irish English",
            "Scottish English",
            "South African",
            "New Zealand",
            "Indian English",
            "Singaporean",
        ),
    ),
    Language(
        name="Spanish",
        accents=(
            "Castilian",
            "Mexican",
            "Argentinian",
            "Colombian",
            "Andalusian",
            "Caribbean",
            "Chilean",
            "Peruvian",
        ),
    ),
    Language(
        name="Mandarin Chinese",
        accents=("Beijing Standard", "Taiwanese", "Singaporean Mandarin", "Northeastern Mandarin"),
    ),
    Language(
        name="Cantonese",
        accents=("Hong Kong", "Guangzhou"),
    ),
    Language(
        name="French",
        accents=("Parisian", "Québécois", "Belgian French", "Swiss French", "African French"),
    ),
    Language(
        name="German",
        accents=("Hochdeutsch", "Austrian", "Swiss German", "Bavarian", "Berliner"),
    ),
    Language(
        name="Japanese",
        accents=("Tokyo Standard", "Kansai", "Tohoku", "Kyushu", "Hokkaido", "Okinawan"),
    ),
    Language(
        name="Korean",
        accents=("Seoul Standard", "Gyeongsang", "Jeolla", "Chungcheong", "Jeju"),
    ),
    Language(
        name="Italian",
        accents=("Standard Italian", "Roman", "Neapolitan", "Sicilian", "Milanese", "Venetian"),
    ),
    Language(
        name="Portuguese",
        accents=(
            "European Portuguese",
            "Brazilian (Carioca)",
            "Brazilian (Paulista)",
            "African Portuguese",
        ),
    ),
    Language(
        name="Russian",
        accents=("Moscow Standard", "Saint Petersburg", "Southern Russian", "Northern Russian"),
    ),
    Language(
        name="Arabic",
        accents=("Modern Standard Arabic", "Egyptian", "Levantine", "Gulf", "Maghrebi", "Iraqi"),
    ),
    Language(
        name="Hindi",
        accents=("Standard Hindi", "Mumbai", "Delhi Hindi", "Hyderabadi"),
    ),
    Language(
        name="Bengali",
        accents=("Kolkata Standard", "Dhaka Standard", "Sylheti"),
    ),
    Language(
        name="Vietnamese",
        accents=("Northern (Hanoi)", "Central (Hue)", "Southern (Saigon)"),
    ),
    Language(
        name="Thai",
        accents=("Central (Bangkok)", "Northern (Lanna)", "Northeastern (Isan)", "Southern Thai"),
    ),
    Language(
        name="Indonesian",
        accents=("Jakartan Standard", "Javanese", "Sundanese", "Balinese"),
    ),
    Language(
        name="Turkish",
        accents=("Istanbul Standard", "Anatolian", "Cypriot Turkish"),
    ),
    Language(
        name="Polish",
        accents=("Standard Polish", "Silesian Polish", "Goral"),
    ),
    Language(
        name="Dutch",
        accents=("Hollands Standard", "Flemish", "Surinamese Dutch"),
    ),
    Language(
        name="Swedish",
        accents=("Rikssvenska", "Finland Swedish", "Skanska", "Gotlandic"),
    ),
    Language(
        name="Norwegian",
        accents=("Bokmål Standard", "Nynorsk", "Bergen"),
    ),
    Language(
        name="Danish",
        accents=("Rigsdansk", "Jutlandic", "Bornholmsk"),
    ),
    Language(
        name="Finnish",
        accents=("Standard Finnish", "Savonian", "Ostrobothnian"),
    ),
    Language(
        name="Greek",
        accents=("Athenian Standard", "Cypriot Greek", "Cretan"),
    ),
    Language(
        name="Hebrew",
        accents=("Modern Israeli", "Ashkenazi", "Sephardic", "Mizrahi"),
    ),
    Language(
        name="Hungarian",
        accents=("Standard Hungarian", "Székely", "Csángó"),
    ),
    Language(
        name="Czech",
        accents=("Bohemian Standard", "Moravian", "Silesian Czech"),
    ),
    Language(
        name="Slovak",
        accents=("Western Slovak", "Central Slovak", "Eastern Slovak"),
    ),
    Language(
        name="Ukrainian",
        accents=("Standard Ukrainian", "Western Ukrainian", "Eastern Ukrainian", "Polissian"),
    ),
    Language(
        name="Romanian",
        accents=("Muntenian Standard", "Moldavian", "Transylvanian", "Bănățean"),
    ),
    Language(
        name="Persian",
        accents=("Tehrani Standard", "Afghan Dari", "Tajik"),
    ),
    Language(
        name="Tagalog",
        accents=("Manila Standard", "Batangas", "Marinduque"),
    ),
    Language(
        name="Swahili",
        accents=("Kenyan Swahili", "Tanzanian Swahili", "Ugandan Swahili", "Congolese Swahili"),
    ),
    Language(
        name="Malay",
        accents=("Malaysian Standard", "Kelantanese", "Kedahan", "Sarawakian"),
    ),
    Language(
        name="Urdu",
        accents=("Lucknowi", "Karachi", "Delhi Urdu"),
    ),
    Language(
        name="Latin",
        accents=("Classical Latin (Reconstructed)", "Ecclesiastical Latin"),
    ),
    Language(
        name="Irish",
        accents=("Munster Irish", "Connacht Irish", "Ulster Irish"),
    ),
    Language(
        name="Scottish Gaelic",
        accents=("Lewis Gaelic", "Skye Gaelic", "Argyll Gaelic"),
    ),
    Language(
        name="Welsh",
        accents=("North Welsh", "South Welsh", "Patagonian Welsh"),
    ),
    Language(
        name="Hawaiian",
        accents=("Niʻihau Hawaiian", "Standard Hawaiian"),
    ),
    Language(
        name="Zulu",
        accents=("Standard Zulu", "Lala", "Qwabe"),
    ),
    Language(
        name="Haitian Creole",
        accents=("Cap-Haïtien", "Port-au-Prince", "Les Cayes"),
    ),
    Language(
        name="Yiddish",
        accents=("YIVO Standard", "Galician Yiddish", "Litvish", "Polish Yiddish"),
    ),
    Language(
        name="Navajo",
        accents=("Western Navajo", "Eastern Navajo"),
    ),
    Language(
        name="Esperanto",
        accents=("Standard Esperanto",),
    ),
    Language(
        name="High Valyrian",
        accents=("Standard High Valyrian",),
    ),
    Language(
        name="Klingon",
        accents=("Standard Klingon",),
    ),
)


LANGUAGE_NAMES: frozenset[LanguageName] = frozenset(get_args(LanguageName))
ALL_ACCENT_NAMES: frozenset[AccentName] = frozenset(get_args(AccentName))


# Module-load invariant: the Literal types and the LANGUAGES catalog must agree exactly. A drift here means someone added an entry to one side and forgot the other.
assert {lang.name for lang in LANGUAGES} == LANGUAGE_NAMES, (
    "LanguageName Literal disagrees with LANGUAGES tuple names"
)
assert {a for lang in LANGUAGES for a in lang.accents} == ALL_ACCENT_NAMES, (
    "AccentName Literal disagrees with LANGUAGES tuple accents"
)
