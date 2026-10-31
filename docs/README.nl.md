# Wanneer Aanzetten Home Assistant-integratie installeren met HACS

Gebruik **wanneeraanzetten.nl in Home Assistant**: bekijk actuele dynamische stroomprijzen en
ontvang per opgeslagen apparaat een aan/uit-advies voor het goedkoopste beschikbare startmoment.
Koppel je account, bekijk de eigen prijsgrafiek met logo en gebruik prijs- en apparaatsensoren in
je dashboard of automatiseringen.

## Installeren via HACS

Vereist: Home Assistant 2025.1.3 of nieuwer, HACS en een account op
[wanneeraanzetten.nl](https://wanneeraanzetten.nl/?view=account).
Bewaar je apparaten online in je account; apparaten die alleen in je browser staan zijn niet zichtbaar.

[Voeg de integratie toe aan HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=MikeBrachten&repository=wanneeraanzetten-home-assistant-integration&category=integration).
Of voeg onder **HACS → Aangepaste repositories** deze URL toe met categorie **Integratie**:

```text
https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration
```

1. Download **Wanneer Aanzetten** in HACS en herstart Home Assistant.
2. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
3. Kies **Wanneer Aanzetten**, log in en selecteer je stroommarkt.
4. Rond zo nodig tweestapsverificatie af met een authenticatorcode of herstelcode.

Dit is een aangepaste HACS-repository. De integratie staat niet standaard in de HACS-catalogus.

## Wat betekenen de sensoren?

| Sensor | Betekenis |
| --- | --- |
| Spotprijs stroom | Actuele beursprijs in EUR/kWh, exclusief energiebelasting, btw en leverancierskosten |
| Geschatte all-in prijs | Geschatte variabele prijs per kWh met de tarieven uit je account; vaste kosten tellen niet mee |
| Apparaat: Nu aanzetten | Aan wanneer nu starten het goedkoopste beschikbare moment binnen je opgeslagen uitstelinstellingen is |

**Aan is een planningsadvies, geen meting dat je wasmachine, vaatwasser of ander apparaat draait.**
Uit betekent dat een later geldig startmoment goedkoper is. Bij ontbrekende prijsdekking of een
verbindingsfout wordt de sensor niet beschikbaar. De integratie schakelt zelf geen apparaten.

De aanbeveling houdt rekening met looptijd, maximaal uitstel en de gekozen stappen voor start- of
einduitstel. De planner vergelijkt vandaag en morgen zodra prijzen beschikbaar zijn. Elke minuut
wordt het advies opnieuw berekend en worden nieuwe apparaten automatisch ontdekt.

## Eigen prijsgrafiek op je dashboard

Na installatie registreert Home Assistant de kaart automatisch. Kies **Wanneer Aanzetten · Prijsgrafiek**
bij **Kaart toevoegen**. De grafiek toont het prijsverloop voor de komende 24 uur, markeert de huidige
periode en gebruikt je opgeslagen Nederlandse tariefinstellingen voor een all-in schatting. Zonder
volledige tariefinstellingen toont de kaart de spotprijs en een rechtstreekse link naar de instellingen.

Je kunt de kaart ook met YAML toevoegen. Vervang de entiteit door de spotprijssensor in jouw Home Assistant:

```yaml
type: custom:wanneeraanzetten-price-card
entity: sensor.jouw_spotprijssensor
```

Je website-instellingen synchroniseren met je account zodra je bent ingelogd. Home Assistant gebruikt
dezelfde instellingen voor de geschatte all-in-prijssensor. Vaste maand- of dagkosten zijn niet inbegrepen.

## Begin met je apparaten

- [Bekijk stroomprijzen vandaag](https://wanneeraanzetten.nl/stroomprijzen-vandaag/).
- [Plan je wasmachine op een goedkoper moment](https://wanneeraanzetten.nl/wanneer-wasmachine-aanzetten/).
- [Plan je vaatwasser](https://wanneeraanzetten.nl/wanneer-vaatwasser-aanzetten/).
- [Zoek een goedkoper laadvenster voor je elektrische auto](https://wanneeraanzetten.nl/wanneer-elektrische-auto-opladen/).

Je wachtwoord wordt niet bewaard. Home Assistant bewaart een alleen-lezen toegangstoken dat na een
jaar verloopt. Bij verlopen of ingetrokken toegang vraagt Home Assistant je opnieuw in te loggen.
Wijzig je stroommarkt via **Configureren** bij de integratie. Beheer leveranciersopslag, energiebelasting
en btw op [de tariefinstellingen van je account](https://wanneeraanzetten.nl/?view=settings).

Bekijk de [Engelse handleiding en automatisering](../README.md),
[probleemoplossing](troubleshooting.md) en [privacy-uitleg](security-and-privacy.md).

## Logo in HACS

De integratie bevat het logo op 256 en 512 pixels. Home Assistant ondersteunt lokale
merklogo’s vanaf versie 2026.3. Sommige HACS-versies halen het lijsticoon nog bij de oude
CDN op. Daardoor kan HACS “icon not available” tonen terwijl het logo bij de geïnstalleerde
integratie wel werkt. Dit is een [bekend HACS-probleem](https://github.com/hacs/integration/issues/5223).

## Apparaatpictogrammen

De sensor **Nu aanzetten** gebruikt het apparaatpictogram uit je Wanneer Aanzetten-account.
De apparatenlijst onder **Instellingen → Apparaten & diensten** toont een vast standaardpictogram
dat Home Assistant zelf bepaalt. Integraties kunnen dit via de ondersteunde API nog niet aanpassen.
Hiervoor bestaat een [voorstel bij Home Assistant](https://github.com/home-assistant/architecture/discussions/1507).
