from dataclasses import dataclass

from bot.texts import LANG_TJ

CITY_DUSHANBE = "dushanbe"
CITY_KHUJAND = "khujand"


@dataclass(frozen=True)
class Store:
    name: str
    address_ru: str
    address_tj: str
    phone: str
    hours: str


STORES: dict[str, list[Store]] = {
    CITY_DUSHANBE: [
        Store("Avrang", "ул. Джаббора Расулова, 9", "кӯчаи Ҷаббора Расулова, 9",
              "48 888 22 22", "08:00–18:30"),
        Store("Avrang", "ул. Мирзо Турсунзаде, 9", "кӯчаи Мирзо Турсунзода, 9",
              "88 886 91 23", "10:00–20:00"),
        Store("Avrang Kushanyon", "проспект Х. Шерози, рынок Кушониён",
              "хиёбони Х. Шерозӣ, бозори Кушониён", "48 888 22 22", "08:00–18:00"),
        Store("Volna", "пр. Дж. Расулова, 55/1", "хиёбони Ҷ. Расулова, 55/1",
              "44 600 70 64", "08:00–19:00"),
        Store("Volna", "ул. А. Навои, 112 мкр.", "кӯчаи А. Навоӣ, микрорайони 112",
              "44 600 79 33", "08:00–19:00"),
        Store("Volna", "ул. Бехзод, 47, Ашан", "кӯчаи Беҳзод, 47, Ашан",
              "44 600 70 01", "10:00–21:00"),
        Store("Volna", "ул. Н. Мухаммад, 1/1", "кӯчаи Н. Муҳаммад, 1/1",
              "44 600 12 65", "08:00–19:00"),
        Store("Volna", "пр. Н. Карабаева, 2/1", "хиёбони Н. Карабоев, 2/1",
              "44 600 05 47", "08:00–19:00"),
        Store("Kontakt / WAK", "Kontakt Premium Shop, ул. Мирзо Турсунзаде, 14/21",
              "Kontakt Premium Shop, кӯчаи Мирзо Турсунзода, 14/21",
              "+992 940 450 101", "09:00–22:00"),
    ],
    CITY_KHUJAND: [
        Store("Mechta", "ул. Исмоила Сомони, 10", "кӯч. Исмоили Сомонӣ, 10",
              "92 444 88 22", "09:00–19:00"),
        Store("Mechta", "ул. Исмоила Сомони, 53", "кӯч. Исмоили Сомонӣ, 53",
              "92 444 88 22", "09:00–19:00"),
        Store("Avrang", "проспект И. Сомони, 9", "хиёбони И. Сомонӣ, 9",
              "98 999 78 17", "08:00–19:00"),
    ],
}

CITY_TITLES_RU = {CITY_DUSHANBE: "Душанбе:", CITY_KHUJAND: "Худжанд:"}
CITY_TITLES_TJ = {
    CITY_DUSHANBE: "Мағозаҳои расмии LG дар Душанбе",
    CITY_KHUJAND: "Мағозаҳои расмии LG дар Хуҷанд",
}


def format_stores(city: str, lang: str) -> str:
    stores = STORES[city]
    if lang == LANG_TJ:
        blocks = [
            f"{s.name}\nСуроға: {s.address_tj}\nТелефон: {s.phone}\nСоатҳои корӣ: {s.hours}"
            for s in stores
        ]
        return CITY_TITLES_TJ[city] + "\n\n" + "\n\n".join(blocks)
    lines = [
        f"{i}. {s.name} — {s.address_ru} — {s.phone} — {s.hours}"
        for i, s in enumerate(stores, start=1)
    ]
    return CITY_TITLES_RU[city] + "\n" + "\n".join(lines)
