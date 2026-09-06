# Draaiboek — Deploy RMW (Roadmap-fase 7)

Stap-voor-stap draaiboek om de applicatie op een verse on-premises VM te zetten,
inclusief back-up. Bedoeld voor de beheerder van de VM (Stric) samen met de
ontwikkelaar.

> **Status (03-09-2026): vooruitlopend opgesteld.** De bouw staat nu bij fase 2
> (restpunten net afgerond); dit draaiboek is alvast klaargezet naar het voorbeeld
> van het vergelijkbare project ReplayCalcTool, zodat fase 7 straks een kwestie is
> van uitvoeren in plaats van uitvinden. Twee dingen zijn nog niet definitief:
> - **VM-gegevens** (IP/hostname, paden) staan als placeholder — in te vullen zodra
>   Stric de VM heeft klaargezet.
> - **De back-upfunctie** in §8 (het `backup_db`-commando en de bijbehorende
>   volume in `docker-compose.yml`) **is nog niet gebouwd.** De aanpak staat hier
>   wel al vast (zie `docs/decisions.md`, 03-09-2026) — het commando volgt in fase 7.
> - **§7 (eerste inrichting)** kan pas ingevuld worden zodra de beheerschermen
>   (koppeltabellen, tolerantietabel — fase 4) en het uitzonderingen-scherm (fase 5)
>   gebouwd zijn.
>
> Volledige achtergrond: `GUIDELINES.md`, `docs/architecture.md` en
> `docs/decisions.md`.

---

## 0. Overzicht & rolverdeling

De app draait als twee Docker-containers op één VM, uit hetzelfde image:

- **`web`** — Django, geserveerd door gunicorn (poort 8000 in de container).
  Statische bestanden zitten al in de image (WhiteNoise). Migraties draaien
  **nooit** automatisch bij het opstarten — dat is een aparte, bewuste stap.
- **`scheduler`** — dezelfde image, draait `scripts/scheduler.sh`: controleert elke
  `POLL_INTERVAL_MINUTES` de servermap op nieuwe/gewijzigde bestanden.

Eén SQLite-bestand (`db.sqlite3`) op een *named volume* (`rmw-data`), gedeeld door
beide services — geen aparte databaseservice, in lijn met "lichte, zelfstandige
container" uit het OvO. Zie `docs/decisions.md` (03-09-2026) voor de afweging
SQLite vs. PostgreSQL.

Andere kantoor-pc's gebruiken de app via de browser op het interne netwerk (LAN),
over gewone `http`. De VM is alleen intern bereikbaar, niet vanaf het internet.

**Rolverdeling:**

- **Stric:** levert en beheert de VM, het besturingssysteem (incl.
  beveiligingsupdates), het netwerk, de koppeling/mount van de servermap
  `\\stroes-1909\atrium\Autoprint\RUUDS`, en de veilige (off-site) bewaring van
  back-ups.
- **Ontwikkelaar (wij):** de Docker-containers, de applicatie, en het aanmaken van
  de back-ups.

Stric levert een kale VM; het installeren van Docker en de app doen wij.

---

## 1. Vereisten (vooraf regelen met Stric)

- [ ] VM: **Debian 12** (of Ubuntu Server 24.04 LTS), lichte specificaties volstaan
      (1–2 vCPU / 2–4 GB RAM / 20 GB schijf — RMW heeft geen zware workload).
- [ ] Een gebruikersaccount met **sudo**-rechten en **SSH**-toegang (bij voorkeur
      met SSH-sleutel).
- [ ] Een **vast LAN-IP** (of hostname).
- [ ] Poort **80** (of 8000) open op het LAN. De VM is **niet** vanaf internet
      bereikbaar.
- [ ] Toegang tot de broncode: leesrechten op de private GitHub-repo
      (`RogerH72/stroes-rit-match`) via een deploy-key/token.
- [ ] **Specifiek voor RMW:** de servermap `\\stroes-1909\atrium\Autoprint\RUUDS`
      moet als leesbare map in de VM beschikbaar zijn (netwerk-mount), zodat de
      container `SERVERMAP_PATH` daarnaar kan laten wijzen. Dit is een taak van
      Stric, niet iets dat de app zelf regelt (zie `docs/architecture.md`).

Noteer alvast:

| Gegeven | Waarde |
|---|---|
| LAN-IP / hostname van de VM | `__________________` |
| Projectmap op de VM | `/opt/stroes-rit-match` (aanbevolen) |
| Back-upmap op de VM | `/opt/rmw-backups` (aanbevolen) |
| Mountpad van de servermap op de VM | `__________________` |

---

## 2. VM voorbereiden — Docker installeren

Inloggen op de VM via SSH, dan Docker Engine + de Compose-plugin installeren
(officiële Docker-repository):

> Pas `linux/debian` hieronder aan naar `linux/ubuntu` als de VM Ubuntu draait.

```bash
# Systeem bijwerken
sudo apt-get update && sudo apt-get upgrade -y

# Docker's officiële repository toevoegen
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker Engine + Compose-plugin installeren
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker starten én inschakelen op boot (herstart-bestendig)
sudo systemctl enable --now docker

# Je gebruiker aan de docker-groep toevoegen (zodat 'docker' zonder sudo werkt)
sudo usermod -aG docker "$USER"
# → log daarna één keer uit en weer in, zodat de groep actief wordt.
```

Controle:

```bash
docker --version
docker compose version
docker run --rm hello-world   # moet "Hello from Docker!" tonen
```

---

## 3. Broncode op de VM zetten

```bash
sudo mkdir -p /opt/stroes-rit-match && sudo chown "$USER" /opt/stroes-rit-match
cd /opt

git clone --branch main https://github.com/RogerH72/stroes-rit-match.git
cd /opt/stroes-rit-match
```

> Gebruik altijd de **`main`**-branch voor een productie-deploy — dat is de
> vrijgegeven, geteste versie.

---

## 4. Configuratie — `.env` aanmaken

De echte `.env` staat **niet** in git (git-ignored). Kopieer het voorbeeld en vul
echte waarden in:

```bash
cd /opt/stroes-rit-match
cp .env.example .env

# Genereer een sterke SECRET_KEY:
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Bewerk daarna `.env` (`nano .env`):

```ini
RMW_SECRET_KEY=<plak hier de gegenereerde sleutel>

# In productie ALTIJD 0:
RMW_DEBUG=0

# Het LAN-IP én/of de hostname van de VM (komma-gescheiden). NIET leeg laten:
RMW_ALLOWED_HOSTS=192.168.1.50,rmw-sbtt

# Alleen nodig achter een proxy/andere hostname — hier meestal leeg laten:
# RMW_CSRF_TRUSTED_ORIGINS=

# SQLite-bestand op het gedeelde volume (standaardwaarde is meestal prima):
RMW_DB_PATH=/app/data/db.sqlite3

# Mountpad van de servermap op déze VM (door Stric geregeld, zie §1):
SERVERMAP_PATH=<mountpad op de VM>

POLL_INTERVAL_MINUTES=5
STABILITY_MINUTES=30
RMW_LOG_LEVEL=INFO
```

> **Let op:** `RMW_ALLOWED_HOSTS` mag **niet leeg** zijn bij `RMW_DEBUG=0` —
> anders geeft elke pagina een **400 Bad Request**. Anders dan bij ReplayCalcTool
> heeft RMW momenteel **geen fail-fast guard** die een ontbrekende
> `RMW_SECRET_KEY` blokkeert — een vergeten sleutel valt stilzwijgend terug op de
> onveilige dev-waarde. Controleer dit dus zelf vóór livegang (zie de checklist in
> §10); het toevoegen van zo'n guard is een mogelijke verbetering voor later.

Beveilig het bestand:

```bash
chmod 600 .env
```

---

## 5. Bouwen, database migreren, superuser aanmaken

```bash
cd /opt/stroes-rit-match

# 1. De image bouwen
docker compose build

# 2. Database-schema aanmaken (aparte, bewuste stap — draait NOOIT vanzelf)
docker compose run --rm web python manage.py migrate

# 3. De eerste beheerder (superuser) aanmaken
docker compose run --rm web python manage.py createsuperuser
```

---

## 6. Starten & verifiëren

```bash
# De stack starten (op de achtergrond)
docker compose up -d

# Status controleren — beide services moeten "running"/"healthy" zijn
docker compose ps

# Live meekijken met de logs (Ctrl+C om te stoppen)
docker compose logs -f web
docker compose logs -f scheduler
```

Open in een browser op een kantoor-pc: **`http://192.168.1.50`** (het LAN-IP van
de VM). Dat kale adres stuurt door naar `/weekoverzicht/` en, zolang je niet bent
ingelogd, vandaar naar het inlogscherm — log in met de superuser en je komt op het
weekoverzicht uit. `/health/` moet 200 geven.

---

## 7. Eerste inrichting van de app

**Nog niet in te vullen (03-09-2026).** Dit hoofdstuk beschrijft straks: de
koppeltabellen invullen (bekende locaties, monteur–voertuig,
personeelsnummer–naam, relaties) en de tolerantietabel instellen — gebouwd in
roadmap-fase 4. Aan te vullen zodra die schermen er zijn.

---

## 8. Back-up — geplande SQLite-back-up op de VM

**Nog te bouwen (03-09-2026) — dit hoofdstuk beschrijft het vastgelegde ontwerp,
niet een werkend commando.** Zie `docs/decisions.md` (03-09-2026) voor de
afweging.

**Waarom niet gewoon het bestand kopiëren.** `db.sqlite3` staat op een volume dat
door twee processen tegelijk gebruikt wordt (`web` en `scheduler`). Een gewone
`cp` tijdens een schrijfactie kan een inconsistente kopie opleveren. SQLite heeft
hiervoor een ingebouwde, veilige oplossing: de *online backup API*
(`sqlite3.Connection.backup()` in Python's standaardbibliotheek), die een
consistente kopie maakt terwijl de database in gebruik blijft — zonder extra
databaseserver of extra pakket in de image.

**8.1 Het `backup_db`-commando (te bouwen, fase 7)**

Een Django management command, naar het voorbeeld van `check_imports`:

- Maakt via `sqlite3.connect(bron).backup(doel)` een kopie van `db.sqlite3` naar
  een apart pad, bijvoorbeeld `/app/backups/rmw_<timestamp>.sqlite3`, en
  comprimeert die (gzip).
- Ruimt zelf back-ups op ouder dan een bewaartermijn (standaard 30 dagen,
  instelbaar via een omgevingsvariabele — zelfde patroon als
  `POLL_INTERVAL_MINUTES`/`STABILITY_MINUTES`).
- Loopt handmatig te draaien (`manage.py backup_db`) en vanuit cron (zie §8.2).

**8.2 Aparte back-uplocatie (te bouwen, fase 7)**

De back-ups horen **niet** op het `rmw-data`-volume te staan — dat zou betekenen
dat `docker compose down -v` zowel de live database als alle back-ups in één klap
wist. In plaats daarvan: een eigen bind-mount op de VM, los van het volume:

```yaml
# docker-compose.yml, service "web" — toe te voegen naast het bestaande "rmw-data"-volume:
    volumes:
      - rmw-data:/app/data
      - ${BACKUP_DIR:-/opt/rmw-backups}:/app/backups
```

**8.3 Dagelijkse cron-job (02:00, op de VM zelf, niet in de container)**

```bash
sudo mkdir -p /opt/rmw-backups && sudo chown "$USER" /opt/rmw-backups

crontab -e
# Voeg toe:
0 2 * * * cd /opt/stroes-rit-match && docker compose exec -T web python manage.py backup_db >> /opt/rmw-backups/backup.log 2>&1
```

**8.4 Herstellen**

Anders dan bij een `pg_dump`-restore (die "over" een draaiende database heen kan)
moet de container stilstaan terwijl het SQLite-bestand vervangen wordt:

```bash
cd /opt/stroes-rit-match
docker compose down

# Het gekozen back-upbestand uitpakken en op het volume zetten:
gunzip -c /opt/rmw-backups/<bestand>.sqlite3.gz > /tmp/restore.sqlite3
docker run --rm -v stroes-rit-match_rmw-data:/data -v /tmp:/restore \
  alpine cp /restore/restore.sqlite3 /data/db.sqlite3

docker compose up -d
```

> Test de herstelprocedure minimaal één keer bij de oplevering, zodat je zeker
> weet dat een back-up ook echt terug te zetten is. Stric neemt de back-upmap
> (`/opt/rmw-backups`) én de VM mee in hun off-site back-uproutine.

---

## 9. Een nieuwe versie uitrollen (updates)

```bash
cd /opt/stroes-rit-match

# 1. Nieuwe code ophalen
git pull origin main

# 2. Opnieuw bouwen en herstarten
docker compose up -d --build

# 3. ALTIJD migreren (onschadelijke no-op als er niets openstaat)
docker compose run --rm web python manage.py migrate
```

Draai stap 3 als vast onderdeel van **elke** update — dan kun je 'm nooit
vergeten. Optioneel eerst kijken wat er openstaat:
`docker compose run --rm web python manage.py showmigrations`.

**Soms is migreren niet genoeg.** Een migratie die alleen een kolom toevoegt aan
een importtabel (zoals `WerkbonControle`) vult die kolom niet met terugwerkende
kracht — bestaande rijen krijgen een lege standaardwaarde totdat het bronbestand
opnieuw wordt ingelezen. `docs/changelog.md` vermeldt per wijziging of dit nodig
is; op het moment dat dit draaiboek geschreven is, geldt dit voor de
Werkbonnen.xlsx-postcode (03-09-2026, zie `docs/decisions.md` en
`docs/business-rules.md`). Check bij twijfel de laatste `docs/changelog.md`-
entries vóór het uitrollen. Zo ja, na stap 3:

```bash
# 4. Bronbestanden herverwerken zodat nieuwe/gewijzigde velden gevuld worden
docker compose run --rm web python manage.py check_imports --force --reprocess
docker compose run --rm web python manage.py run_matching --force
```

---

## 10. Go-live checklist

- [ ] **`RMW_DEBUG=0`** in `.env` op de VM.
- [ ] **`RMW_ALLOWED_HOSTS`** gezet op het LAN-IP/hostname van de VM (niet leeg).
- [ ] **`RMW_SECRET_KEY`** expliciet gezet (niet de dev-fallback) — er is geen
      automatische guard die dit afdwingt, dus dit is een handmatige controle.
- [ ] **`SERVERMAP_PATH`** wijst naar de door Stric gemounte servermap en is
      leesbaar vanuit de container.
- [ ] **`.env`** staat niet in git; rechten op `600`.
- [ ] **Automatische SQLite-back-up** ingepland (cron, §8) én een eerste back-up
      bevestigd; back-upmap + VM in de off-site routine van Stric.
- [ ] **Restore getest** (§8.4).
- [ ] **Geen pagina bereikbaar zonder inloggen** — laatste controle.
- [ ] **Docker ingeschakeld op boot** (`systemctl enable docker`); app bevestigd
      terug na een test-reboot van de VM.

**Test-reboot:**

```bash
sudo reboot
# na het opnieuw opstarten, zonder handmatige actie:
docker compose ps      # web + scheduler moeten weer draaien
```

---

## 11. Problemen oplossen

| Symptoom | Oorzaak / oplossing |
|---|---|
| **400 Bad Request** op elke pagina | `RMW_ALLOWED_HOSTS` is leeg of mist het gebruikte IP/hostname. Vul aan, dan `docker compose up -d --force-recreate web`. |
| **Wijziging in `.env` doet niets** | `.env` wordt bij container-*start* ingelezen. Een gewone `restart` is niet genoeg — gebruik `docker compose up -d --force-recreate web scheduler`. |
| **Wijziging in de code doet niets** | Code zit in de image. Rebuild: `docker compose up -d --build`. |
| **Scheduler meldt "server share not available"** | Verwacht gedrag als `SERVERMAP_PATH` (nog) niet bereikbaar is — geen crash, probeert het de volgende ronde opnieuw. Controleer de mount bij Stric als dit blijft aanhouden. |
| **Migratie vergeten na update** | Draai altijd `docker compose run --rm web python manage.py migrate` na een deploy. |
| **`db.sqlite3` lijkt "locked"** | Kortstondig mogelijk bij gelijktijdige schrijfacties van `web` en `scheduler`; Django/SQLite handelt dit af met een retry. Aanhoudend? Controleer of er nog een oud, hangend proces draait: `docker compose ps`. |

**Handige commando's**

```bash
docker compose ps                 # status van de containers
docker compose logs -f web        # live app-logs
docker compose logs -f scheduler  # live scheduler-logs
docker compose down               # stoppen (data blijft in het rmw-data-volume)
docker compose down -v            # LET OP: verwijdert óók de database (rmw-data)!
```

---

## Bijlage — verschillen met het ReplayCalcTool-draaiboek

RMW volgt dezelfde aanpak (lokaal bouwen → Docker-container → VM van de
IT-partner, geplaatst vanuit GitHub), met een paar verschillen die uit de eigen
scope van RMW volgen:

| | ReplayCalcTool | RMW |
|---|---|---|
| Database | PostgreSQL (aparte `db`-service) | SQLite (op het `rmw-data`-volume) |
| Back-up | `pg_dump` via cron | SQLite online-backup-API via een management command, cron |
| Extra service naast `web` | — | `scheduler` (bestandsdetectie) |
| Cloud-schakelaar (`DEPLOY_MODE`) | Aanwezig, voor een eventuele cloud-stap later | Nog niet — LAN-only is voorlopig het enige scenario |
| Fail-fast bij ontbrekende secret | Aanwezig (§11, `RUNNING_IN_CONTAINER`-guard) | Nog niet — handmatige controle in de checklist (§10) |

---

*Referenties: `GUIDELINES.md`, `docs/architecture.md`, `docs/decisions.md`
(03-09-2026). Configuratie-voorbeeld: `.env.example`.*
