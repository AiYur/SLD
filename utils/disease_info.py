"""
utils/disease_info.py
---------------------
Plain-language notes shown next to a prediction: what the class means, what
to look for on the leaf, and what a grower can reasonably do next. English
and Filipino text live side by side so the page can switch languages without
another round trip.

These notes are general guidance for a school/extension setting, not a
prescription. Chemical control, varietal choice, and quarantine decisions
should be confirmed with a local agricultural technician (e.g. the municipal
agriculture office or SRA), because recommendations vary by variety, region,
and what is actually registered for use.
"""

DISEASE_INFO = {
    "Healthy": {
        "en": {
            "title": "Healthy",
            "summary": "No disease symptoms detected on this leaf.",
            "symptoms": [
                "Even green color across the blade",
                "No streaks, spots, pustules, or reddening",
                "Firm leaf with normal width and upright growth",
            ],
            "actions": [
                "Keep monitoring weekly, especially after heavy rain",
                "Maintain field sanitation and balanced fertilization",
                "Continue to source planting material from clean, certified seed cane",
            ],
            "severity": "none",
        },
        "fil": {
            "title": "Malusog",
            "summary": "Walang nakitang sintomas ng sakit sa dahong ito.",
            "symptoms": [
                "Pantay na berdeng kulay ng buong dahon",
                "Walang guhit, batik, o pamumula",
                "Matibay na dahon na may normal na laki at tayo",
            ],
            "actions": [
                "Magpatuloy sa lingguhang pagsusuri, lalo na pagkatapos ng malakas na ulan",
                "Panatilihin ang kalinisan ng taniman at tamang pataba",
                "Gumamit pa rin ng malinis at sertipikadong punla",
            ],
            "severity": "none",
        },
    },
    "Mosaic": {
        "en": {
            "title": "Mosaic Virus",
            "summary": (
                "Sugarcane mosaic is a viral disease (commonly SCMV). It spreads through "
                "infected planting material and by aphids, and it lowers yield quietly "
                "rather than killing the plant outright."
            ),
            "symptoms": [
                "Patchy light-green to yellow areas mixed with normal green",
                "Pattern runs along the leaf, clearest on young leaves",
                "Stunted growth and thinner stalks when infection is heavy",
            ],
            "actions": [
                "Do not take seed cane from affected stools",
                "Rogue out badly infected stools where practical",
                "Plant resistant or tolerant varieties in the next cycle",
                "Control aphids and nearby grass hosts that carry the virus",
            ],
            "severity": "moderate",
        },
        "fil": {
            "title": "Mosaic (Virus)",
            "summary": (
                "Ang mosaic ay sakit na dulot ng virus (karaniwan ay SCMV). Kumakalat ito "
                "sa pamamagitan ng may sakit na punla at ng mga aphid, at dahan-dahang "
                "binabawasan ang ani."
            ),
            "symptoms": [
                "Magkahalong maputlang berde at dilaw na bahagi ng dahon",
                "Pahaba ang pattern sa dahon, mas kitang-kita sa batang dahon",
                "Bansot na paglaki at manipis na tangkay kapag malala",
            ],
            "actions": [
                "Huwag kumuha ng punla mula sa apektadong tanim",
                "Tanggalin ang malubhang apektadong tanim kung kaya",
                "Gumamit ng varayting matibay sa sakit sa susunod na tanim",
                "Kontrolin ang aphids at mga damong nagtataglay ng virus",
            ],
            "severity": "moderate",
        },
    },
    "RedRot": {
        "en": {
            "title": "Red Rot",
            "summary": (
                "Red rot (Colletotrichum falcatum) is the most damaging sugarcane disease "
                "in many areas. Leaf symptoms are an early warning; the real damage is "
                "inside the stalk, so split a suspect stalk to confirm."
            ),
            "symptoms": [
                "Reddish lesions on the midrib, often with a pale center",
                "Drying and withering of leaves from the top down",
                "Inside the split stalk: red tissue crossed by white patches, with a sour alcohol smell",
            ],
            "actions": [
                "Split a few suspect stalks to confirm before acting",
                "Remove and destroy infected stools; do not leave them in the field",
                "Never use cane from an affected field as seed",
                "Improve drainage, and avoid replanting cane after cane in a hot spot",
                "Consult your agricultural technician about resistant varieties and seed treatment",
            ],
            "severity": "high",
        },
        "fil": {
            "title": "Red Rot",
            "summary": (
                "Ang red rot (Colletotrichum falcatum) ang isa sa pinakamapaminsalang sakit "
                "ng tubo. Maagang babala ang sintomas sa dahon; nasa loob ng tangkay ang "
                "tunay na pinsala, kaya biyakin ang pinaghihinalaang tangkay."
            ),
            "symptoms": [
                "Mapupulang sugat sa gitnang ugat ng dahon, madalas may maputlang gitna",
                "Pagkatuyo ng mga dahon mula sa itaas pababa",
                "Sa loob ng tangkay: pulang laman na may puting batik at maasim na amoy",
            ],
            "actions": [
                "Biyakin ang ilang tangkay upang makumpirma bago kumilos",
                "Tanggalin at sirain ang apektadong tanim; huwag iwan sa bukid",
                "Huwag gamiting punla ang tubo mula sa apektadong taniman",
                "Ayusin ang drainage at iwasang ulit-ulitin ang tubo sa parehong lugar",
                "Kumonsulta sa agricultural technician tungkol sa varayti at seed treatment",
            ],
            "severity": "high",
        },
    },
    "Rust": {
        "en": {
            "title": "Rust",
            "summary": (
                "Sugarcane rust is a fungal disease (commonly Puccinia melanocephala). "
                "It thrives in humid weather and reduces photosynthesis, cutting yield "
                "when outbreaks are severe."
            ),
            "symptoms": [
                "Small elongated orange to reddish-brown pustules on the leaf",
                "Pustules rub off as powder on a finger or tissue",
                "Heavy infection makes the whole leaf look rusty-brown and dries it early",
            ],
            "actions": [
                "Check the underside of leaves to gauge how widespread it is",
                "Avoid excess nitrogen, which makes soft growth more susceptible",
                "Improve air movement: correct spacing and remove excess trash",
                "For severe outbreaks, ask an extension officer about registered fungicides and timing",
                "Favor resistant varieties in the next planting",
            ],
            "severity": "moderate",
        },
        "fil": {
            "title": "Rust (Kalawang)",
            "summary": (
                "Ang rust ay sakit na dulot ng fungus (karaniwan ay Puccinia melanocephala). "
                "Lumalala ito sa mahalumigmig na panahon at binabawasan ang ani."
            ),
            "symptoms": [
                "Maliliit at pahabang kulay-kahel hanggang pula-kayumangging butlig sa dahon",
                "Napapahid ang butlig na parang pulbos",
                "Kapag malala, nagmumukhang kalawangin at maagang natutuyo ang dahon",
            ],
            "actions": [
                "Tingnan ang ilalim ng dahon upang masukat ang lawak",
                "Iwasan ang sobrang nitrogen na pataba",
                "Pagandahin ang daloy ng hangin: tamang espasyo at alisin ang sobrang dayami",
                "Kung malala, magtanong sa extension officer tungkol sa rehistradong fungicide",
                "Piliin ang varayting matibay sa rust sa susunod na tanim",
            ],
            "severity": "moderate",
        },
    },
    "Yellow": {
        "en": {
            "title": "Yellow Leaf",
            "summary": (
                "Yellowing of the midrib and blade. This can be yellow leaf disease "
                "(ScYLV, spread by aphids and infected setts) but similar yellowing also "
                "comes from nitrogen shortage, waterlogging, or salinity - so confirm the cause."
            ),
            "symptoms": [
                "Yellowing that starts on the underside of the midrib",
                "Yellowing spreads into the blade, usually on older leaves first",
                "Shortened top internodes and reduced vigor in a bad case",
            ],
            "actions": [
                "Rule out the simple causes first: check soil moisture, drainage, and nitrogen status",
                "If yellowing follows the midrib and clusters in patches, suspect ScYLV",
                "Use certified, heat-treated seed cane for the next planting",
                "Control aphid populations",
                "Have a sample confirmed by a laboratory if the field is large or the loss is repeated",
            ],
            "severity": "moderate",
        },
        "fil": {
            "title": "Yellow Leaf (Paninilaw)",
            "summary": (
                "Paninilaw ng gitnang ugat at dahon. Maaari itong yellow leaf disease "
                "(ScYLV, kumakalat sa aphids at may sakit na punla), ngunit kahawig din "
                "ang paninilaw dahil sa kulang na nitrogen, baha, o alat - kaya kumpirmahin."
            ),
            "symptoms": [
                "Paninilaw na nagsisimula sa ilalim ng gitnang ugat",
                "Kumakalat ang dilaw sa buong dahon, mas una sa matandang dahon",
                "Pagiksi ng itaas na buko at panghihina kapag malala",
            ],
            "actions": [
                "Suriin muna ang simpleng dahilan: tubig sa lupa, drainage, at nitrogen",
                "Kung sumusunod sa gitnang ugat at pakumpol-kumpol, maghinala ng ScYLV",
                "Gumamit ng sertipikado at heat-treated na punla sa susunod na tanim",
                "Kontrolin ang aphids",
                "Magpasuri sa laboratoryo kung malawak ang taniman o paulit-ulit ang pinsala",
            ],
            "severity": "moderate",
        },
    },
    "Dry": {
        "en": {
            "title": "Dry / Withered",
            "summary": (
                "The leaf is dried or withered. This is often natural senescence of older "
                "leaves, or water stress - but it is also how several diseases end, so "
                "check the stalk and the younger leaves before deciding it is harmless."
            ),
            "symptoms": [
                "Brown, brittle, curled, or papery leaf tissue",
                "Drying from the leaf tip and margins inward",
                "Loss of green color with no distinct pustules or mosaic pattern",
            ],
            "actions": [
                "Check whether only the oldest leaves are affected - that is usually normal",
                "Check soil moisture and irrigation; drought and salinity both cause this",
                "Split a stalk to rule out red rot if drying is spreading from the top",
                "Look at younger leaves for the disease that may have caused the dieback",
            ],
            "severity": "low",
        },
        "fil": {
            "title": "Tuyo / Lanta",
            "summary": (
                "Tuyo o lantang dahon. Madalas ito ay natural sa matandang dahon o dulot "
                "ng kakulangan sa tubig - ngunit ganito rin ang dulo ng ilang sakit, kaya "
                "suriin ang tangkay at ang mga batang dahon bago sabihing walang problema."
            ),
            "symptoms": [
                "Kayumanggi, malutong, kulubot, o parang papel na dahon",
                "Nagsisimula ang pagkatuyo sa dulo at gilid ng dahon",
                "Nawawalang berde na walang butlig o mosaic na pattern",
            ],
            "actions": [
                "Tingnan kung ang matatandang dahon lang ang apektado - madalas normal ito",
                "Suriin ang tubig sa lupa at patubig; tuyot at alat ay parehong sanhi",
                "Biyakin ang tangkay upang maalis ang hinala ng red rot",
                "Tingnan ang batang dahon para sa sakit na posibleng sanhi",
            ],
            "severity": "low",
        },
    },
}

DISCLAIMER = {
    "en": (
        "This app supports field scouting; it does not replace laboratory diagnosis. "
        "Confirm findings with your local agricultural technician before applying any treatment."
    ),
    "fil": (
        "Tulong lang ang app na ito sa pagsusuri sa bukid; hindi nito pinapalitan ang "
        "laboratoryo. Kumpirmahin sa inyong agricultural technician bago gumamit ng anumang lunas."
    ),
}


def get_info(class_name: str, lang: str = "en") -> dict:
    lang = lang if lang in ("en", "fil") else "en"
    entry = DISEASE_INFO.get(class_name)
    if not entry:
        return {
            "title": class_name,
            "summary": "No notes available for this class.",
            "symptoms": [],
            "actions": [],
            "severity": "unknown",
            "disclaimer": DISCLAIMER[lang],
        }
    info = dict(entry[lang])
    info["disclaimer"] = DISCLAIMER[lang]
    return info


def all_info(lang: str = "en") -> dict:
    return {name: get_info(name, lang) for name in DISEASE_INFO}
