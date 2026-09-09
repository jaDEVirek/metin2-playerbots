# ⚔️ Metin2 Playerbots

**Polski** | [English (README_EN.md)](README_EN.md)

Lokalny świat Metin2 singleplayer, w którym po mapie biegają i autentycznie grają autonomiczne postacie (Playerbots): zdobywają poziomy, walczą solo i w party, zbierają łup, ulepszają ekwipunek u Kowala, polują na Metiny i zapisują swój postęp w standardowej bazie danych.

## 💬 Społeczność i wsparcie projektu

- **[Dołącz do serwera Discord](https://discord.gg/6v4WkDY6a)** — porozmawiaj o projekcie, podziel się testami i pomysłami oraz śledź aktualności z rozwoju botów.
- **[Wesprzyj rozwój na buycoffee.to](https://buycoffee.to/metin2-playerbots)** — dobrowolne wpłaty pomagają pokrywać koszty narzędzi i modeli AI wykorzystywanych podczas rozwijania projektu.

Każda forma wsparcia — testy, zgłoszenia błędów, propozycje, kod lub wpłata — pomaga nam tworzyć coraz bardziej samodzielny i żywy świat Metin2.

> [!IMPORTANT]
> Projekt działa wyłącznie z **natywnym klientem Windows**. Nie zawiera ani nie pobiera automatycznie plików Metin2, pakietu r40250 lub wycofanego WebClienta. Do instalacji potrzebujesz własnej zgodnej kopii plików. Zobacz [pochodzenie projektu i atrybucję](docs/ATTRIBUTION.md).

W przeciwieństwie do tradycyjnych botów-klientów, boty w tym projekcie są **pełnoprawnymi bytami PC sterowanymi przez AI bezpośrednio wewnątrz silnika serwera (`game core`)**. Oznacza to, że zwykły gracz po wejściu do gry widzi ich naturalny ruch, animacje ataków, skille oraz ekwipunek przez standardowy protokół gry.

---

## 🌟 Możliwości botów

- ⚔️ **Inteligentna walka**: Obsługa wszystkich klas (Wojownik, Sura BM/WP, Ninja Dagger/Archer, Szaman), płynne animacje kombosów, ataki z łuku z uwzględnieniem strzał, utrzymywanie buffów i rotacje skilli.
- 🗺️ **Globalna nawigacja 2D NavGrid (A*)**: Własna siatka kolizji generowana z atrybutów mapy (`server_attr`) oraz algorytm A* z wygładzaniem tras (*String Pulling*). Boty sprawnie omijają góry, rzeki i mury miejskie.
- 🚪 **Podróże między mapami**: Autonomiczne przejścia M1 ↔ M2 ↔ M3, Łatwy Loch Małp, Dolina Orków, Pustynia Yongbi, Góra Sohan i Loch Pająków V1. Boty dobierają mapę do poziomu, a hub na mapie według wspólnej pamięci populacji o tym, gdzie stoi najwięcej potworów.
- 🏹 **Misje polowań do 55 poziomu i Ząb Orka**: Oficjalne misje z `levelup` przyjmowane bez okna dialogowego, opcja dobrana do mapy, na której bot stoi; u Biologa siedem misji z Zębem Orka i Kamieniem Duszy włącznie.
- 🎁 **Szkatułki i bossy**: Szkatułki Księżycowe i szkatułki bossów są otwierane, a ich zawartość używana (zwoje bonusów, mikstury szybkości, Zwój Błogosławieństwa przy ulepszaniu od +6). Drużyny, najpierw ze współgildianami, ruszają na Wodza Orków i Królową Pająków.
- 💎 **Polowanie na Metiny**: Dedykowana rola łowców Metinów patrolujących całą mapę, niszczących kamienie i czyszczących fale potworów.
- 🎒 **Loot i ekonomia miejska**: Zbieranie Yang i przedmiotów po walce, automatyczne ubieranie lepszego ekwipunku wraz z tarczami, regularne powroty do odpowiednich handlarzy, uzupełnianie mikstur i ulepszanie u **Kowala**.
- 🐴 **Rozwój konia**: Wyprawy po prawdziwe Medale Konne do Lochu Małp, oddawanie ich najbliższemu Stajennemu i używanie konia do długich podróży.
- 👥 **Grupy i Party**: Dynamiczne drużyny 2–3 osobowe, a w Dolinie Orków do 8 osób na obozy Czarnych Orków; formacje bojowe i wspólne expienie w gęstych obozach potworów.
- 🏪 **Stragany i rynek bot–bot**: Boty otwierają prywatne stragany w Bokjung i **kupują od siebie nawzajem** — ulepszacze, których akurat komuś brakuje, i sprzęt lepszy od noszonego. Przedmiot na +7 lub wyżej nigdy nie trafia do handlarza NPC.
- 🧬 **Misje Biologa**: Zbieranie okazów i oddawanie ich Biologowi, etapami, bez okna dialogowego questa.
- 🎣 **Łowienie ryb**: Pełna sesja z przynętą w gnieździe wędki, czekaniem na branie i wyciąganiem w oknie 6 sekund.
- ✨ **Przerzucanie bonusów**: Boty używają Kamieni Zmiany i Dodania Bonusu na sprzęcie, którego akurat nie mają założonego.
- 🧠 **Osobowość i cele**: Każdy bot ma własny charakter i ambicję (łowca Metinów, kolekcjoner, hodowca konia, „Dropek” od Metinów, M3, M2 lub medali), które decydują, co robi w danej godzinie.
- 🎛️ **Panel steruje zachowaniem na żywo**: suwaki wag celów, wyłącznik napisów botów nad głową, boty złomiarze wystawiające tani złom do palenia u kowala oraz szansa na Szkatułki Księżycowe — wszystko odczytywane przez rdzeń w pięć sekund, bez restartu.
- 💾 **Trwały zapis w bazie**: Każdy bot posiada własne konto i postać w bazie MariaDB — zachowuje poziom, przedmioty, Yang i postępy po restarcie serwera.

---

## 📊 Status projektu

Projekt jest w fazie aktywnego rozwoju.

> [!NOTE]
> **Obsługiwane Królestwo:** Obecnie autonomiczny świat obejmuje **Chunjo**: Joan (M1, mapa 21), Bokjung (M2, mapa 23), Waryong/M3 (mapa 24), Łatwy Loch Małp (mapa 25, poziomy 18–26), **Dolinę Orków** (mapa 64, wszystkie 23 wyspy z mostami), **Pustynię Yongbi** (mapa 63), **Górę Sohan** (mapa 61, od 48 poziomu) oraz **Loch Pająków V1** (mapa 104, od 48 poziomu). Obsługa pozostałych królestw (*Shinsoo – Czerwoni* oraz *Jinno – Niebiescy*) jest zaplanowana w dalszych etapach.

### Zużycie zasobów (pomiar przy 843 żywych botach)
- **Serwer gry (`game core`)**: ~1.8 GiB RAM, ~25–38% jednego rdzenia (planer tras z własną siatką i pamięcią policzonych tras)
- **Baza danych (`MariaDB`)**: ~89 MiB RAM
- **Panel Webowy Live Map**: ~270 MiB RAM
- Całość bez problemu działa lokalnie w tle na maszynie deweloperskiej.
- Liczbę botów ustawia `PLAYERBOT_AUTOSPAWN_COUNT`, ale sufitem jest liczba kanonicznych tożsamości w bazie (`BOT_COUNT` w `generate_seed.py`), a nie sam suwak.

---

## 🚀 Szybki start (Quickstart)

### 1. Przygotowanie plików

Przygotuj lokalnie zgodne archiwum serwera r40250. Opcjonalnie przygotuj także archiwum natywnego klienta Windows, najlepiej z dokładnie tego samego wydania. Sama etykieta „r40250” nie gwarantuje zgodności protokołu i plików proto. Żaden z tych plików nie może być publikowany w tym repozytorium.

### 2. Klonowanie i instalacja (Windows)
```powershell
git clone https://github.com/TieruYT/metin2-playerbots.git
Set-Location .\metin2-playerbots
& .\installer\install.ps1 `
    -Archive 'C:\ścieżka\Reference_Server.zip' `
    -ClientArchive 'C:\ścieżka\Reference_Client.zip' `
    -NoWebClient
```

Jeśli masz już skonfigurowanego klienta, użyj zamiast `-ClientArchive` przełącznika `-NoClient`.

### 3. Uruchomienie serwera po instalacji
```powershell
Set-Location "$env:USERPROFILE\Metin2Server"
docker compose up -d
```

Po starcie działają dwa panele w przeglądarce: klasyczny panel administracyjny pod `http://127.0.0.1:7788` oraz **Metin2 Singleplayer Panel** autorstwa seban latino pod `http://127.0.0.1:7790` — mapa świata botów na żywo, profile postaci z ekwipunkiem i tooltipami przedmiotów, rankingi, historia gospodarki, telemetria hosta, sterowanie botami i masowe nadawanie przedmiotów. Przy pierwszym wejściu na `/setup` wybierasz nazwę, motyw i opcjonalne hasło.

### 4. Wejście do gry
Skonfiguruj klienta z tego samego kompatybilnego zestawu r40250 na adres `127.0.0.1` (port Auth `11000`, porty gry `13000–13002`) i ciesz się tętniącym życiem światem w Chunjo!

👉 **Szczegółowy przewodnik instalacji, konfiguracji `.env` i klienta znajdziesz w: [docs/INSTALL.md](docs/INSTALL.md)**

---

## 🗄️ Dostęp do bazy danych (Navicat, HeidiSQL, DBeaver)

Baza serwera to MariaDB w kontenerze, wystawiona **tylko na tym komputerze**
(`127.0.0.1`, port `3306` — albo inny, jeśli w `.env` ustawiono `M2_DB_PUBLISH_PORT`).
Nowe połączenie w kliencie bazy: typ MySQL/MariaDB, host `127.0.0.1`, port `3306`.

| Konto | Do czego | Hasło |
|---|---|---|
| `root` | wszystko | `M2_DB_ROOT_PASSWORD` w `linux-port\docker\.env` |
| `metin2` | tylko bazy gry (`account`, `player`, `log`, `common`, `hotbackup`) | `M2_DB_PASSWORD` w tym samym pliku |

Najszybciej: w launcherze GUI przycisk **DANE DO BAZY (NAVICAT)** pokazuje
host, port i oba hasła w polach do skopiowania (w konsoli: akcja `DbAccess`,
pozycja 16 menu). Hasła są losowane przy pierwszym uruchomieniu i nie ma
żadnego „domyślnego” — nie wklejaj ich na Discordzie.

Jeśli klient odpowiada `1045 - Access denied for user 'root'@'172.18.0.1'`,
baza została zainicjalizowana pod innym hasłem niż to, które jest teraz w `.env`.
Kliknij **NAPRAW DOSTĘP DO BAZY** (akcja `RepairDb`): zatrzymuje serwer i
ustawia konta `metin2` i `root` na hasła z `.env`; postacie, przedmioty i boty
zostają nietknięte. Potem GRAJ i zaloguj się jeszcze raz.

## 🎮 Komendy w grze (GM Commands)

Zarządzanie botami bezpośrednio z poziomu czatu w grze (dla konta GM / Administratora):

| Komenda | Uprawnienia | Opis | Przykład |
|---|---|---|---|
| `/bot_spawn <id> <królestwo: 1-3>` | GM | Ręczny spawn konkretnego bota o danym ID (`1` = Shinsoo, `2` = Chunjo, `3` = Jinno). | `/bot_spawn 4 2` |
| `/bot_despawn <id>` | GM | Usunięcie / wylogowanie bota ze świata. | `/bot_despawn 4` |
| `/bot_spawn_many <start_id> <ilość> <królestwo>` | GM | Masowe zespawnowanie grupy botów. | `/bot_spawn_many 4 350 2` |
| `/bot_despawn_many <start_id> <ilość>` | GM | Masowe wylogowanie grupy botów. | `/bot_despawn_many 4 350` |
| `/bot_rank` | Wszyscy | Wyświetla na czacie aktualny ranking poziomów aktywnych botów. | `/bot_rank` |

---

## 🗺️ Roadmapa rozwoju

- [x] **Faza 1**: Pełne animacje wszystkich klas, łucznicy z pociskami, siatka 2D NavGrid (A*), ulepszanie u Kowala i 32 huby expienia w Chunjo.
- [x] **Faza 2A**: Przejścia M1/M2/M3, expienie strefowe, Łatwy Loch Małp i rzeczywiste wyprawy po Medale Konne.
- [ ] **Faza 2B**: Dolina Orków ✅ i Pustynia Yongbi ✅ — pozostają wyprawy na **Wieżę Demonów (DT)**.
- [ ] **Faza 3**: Czytanie Ksiąg Umiejętności (KU) i Kamieni Duchowych (KD), zaawansowane buildy skilli.
- [x] **Faza 4A**: Podstawowe misje Biologa i pierwszy etap konia oparty na prawdziwym dropie Medali Konnych.
- [x] **Faza 4B**: Ząb Orka i Kamień Duszy u Biologa (z szansą na spalenie zęba jak w queście), misje polowań do 55 poziomu, koń bojowy z pustynnej próby.
- [ ] **Faza 4C** *(następne w kolejce)*: dalsze misje Biologa, trzy królestwa i wojny królestw.
- [ ] **Faza 5**: Łowienie ryb ✅ — pozostają kilof, wydobywanie rud i alchemia.
- [x] **Faza 6**: Prywatne stragany botów w mieście i handel bot–bot. Wycena opiera się na razie na stałych progach, nie na popycie.

---

## 📚 Dokumentacja projektu

Szczegółowe informacje podzielone na dedykowane poradniki:

- 📖 **[Instalacja i Konfiguracja (docs/INSTALL.md)](docs/INSTALL.md)** – Docker, WSL2, Linux, `.env`, podłączanie klienta.
- 💻 **[Przewodnik Deweloperski (docs/DEVELOPMENT.md)](docs/DEVELOPMENT.md)** – Szybka kompilacja C++ w 8s (`fast-game-build`), debugowanie i logi AI.
- 🧩 **[Architektura i refaktoryzacja (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md)** – granice modułów oraz bezpieczny plan dzielenia AI na testowalne części.
- 🧾 **[Pochodzenie i atrybucja (docs/ATTRIBUTION.md)](docs/ATTRIBUTION.md)** – historia forka, granice licencji i status WebClienta.

---

## 🤝 Podziękowania i Credits

- **AzzlackSyndicate** — autor pierwotnej bazy linuksowego portu, instalatorów i panelu. Repozytorium źródłowe jest obecnie prywatne; zachowujemy historię Git i pełną atrybucję.
- **OskarPWA** — okno magazynu bota i ikony umiejętności na stronie pochodzą z panelu, który zbudował i udostępnił do przeniesienia.
- **seban latino** — autor Metin2 Singleplayer Panel (`linux-port/docker/seban-panel`), drugiego panelu w tej instalacji: mapa na żywo, profile, rankingi, gospodarka, telemetria i masowe nadania.
- [DadsMmoLab/dads-mmo-lab](https://github.com/DadsMmoLab/dads-mmo-lab) — Inspiracja badawcza dla autonomicznych agentów w grach MMO.
- Społeczność badaczy i entuzjastów platformy Metin2.
