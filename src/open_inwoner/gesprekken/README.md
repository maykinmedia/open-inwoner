# Mijn gesprekken (experimenteel)

Gesprekken tussen inwoner en gemeente op de detailpagina van een zaak. De
gesprekken staan in een Gesprekken API volgens de concept-standaard
MijnGesprekken; de portal bewaart er geen kopie van. Lokaal staat alleen wat de
portal zelf nodig heeft: de positie in de eventstroom, verwerkte event-id's en
wanneer een gebruiker een gesprek voor het laatst zag.

## Wat de inwoner kan

- Gesprekken over de zaak lezen en reageren, met een bijlage.
- Een gesprek starten op een open zaak.
- Een open gesprek afsluiten met de knop "Vraag beantwoord".
- Automatische antwoorden herkenbaar tonen; daarvoor gaat geen e-mail uit.
- Vertegenwoordiging tonen: "naam, namens partij" als een deelname `namens`
  heeft.

## Instellen

Via "Mijn gesprekken configuratie" in de admin:

- **Gesprekken API**: de service, en het vinkje om de sectie aan te zetten.
- **Bijlagen ingeschakeld**: de inwoner mag bijlagen toevoegen.
- **Inwoner mag een gesprek starten**, met de **ontvanger**: URL en naam van de
  Actor in Klantinteracties. Het formulier verschijnt alleen als ook de Partij
  van de inwoner bekend is, dus met OpenKlant2.

Wijzigingen komen binnen via `python src/manage.py volg_gesprekken_events`. Dit
commando draait doorlopend, onthoudt zijn positie en verbindt na een
onderbreking opnieuw. De browser ververst door te pollen; zolang er niets is
veranderd, krijgt die een 204.

## Bijlagen

Uploaden volgt `patterns/file-upload`: upload-sessie aanmaken, bestand met `PUT`
naar de pre-signed URL, en wachten tot het bestand `beschikbaar` is. De `PUT`
gaat buiten de API-client om, zodat er geen API-authenticatie meegaat. De
wachttijd is begrensd en valt binnen het verzoek van de inwoner.

Naam, icoon en grootte komen uit de weergavegegevens van de bijlage. Downloaden
gaat via de portal: die controleert of het gesprek bij de zaak hoort en of een
bijdrage dit bestand draagt, en stuurt dan door naar de tijdelijke
`downloadUrl`.

## E-mail

Na een nieuwe bijdrage van de gemeente krijgt de inwoner na een instelbare
vertraging een e-mail, als hij de bijdrage nog niet heeft gezien. Het adres komt
uit de digitale adressen van de Partij in Klantinteracties, het standaardadres
eerst. Is OpenKlant2 niet ingesteld, is er geen Partij of e-mailadres, of is er
een storing, dan valt de portal terug op het adres uit het profiel van de
gebruiker. Heeft de gebruiker daar alleen een gegenereerd adres, dan gaat er
geen e-mail uit.

## Relatie met VNG API Lab

Deze app volgt de MijnGesprekken API uit
[VNG-API-Lab PR #47](https://github.com/VNG-Realisatie/VNG-API-Lab/pull/47), die
nog niet is vastgesteld. Relevante issues in VNG-Realisatie/VNG-API-Lab:

- [#7](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/7): MijnGesprekken.
- [#5](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/5): file upload,
  voor de bijlagen.
- [#4](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/4): paginering. De
  portal volgt de `next`-links.
- [#51](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/51) en
  [#13](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/13): autorisatie.
- [#16](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/16) en
  [PR #53](https://github.com/VNG-Realisatie/VNG-API-Lab/pull/53): queryen. De
  portal gebruikt alleen het filter `aanleidingZaak`.
- [#48](https://github.com/VNG-Realisatie/VNG-API-Lab/issues/48) en
  [PR #49](https://github.com/VNG-Realisatie/VNG-API-Lab/pull/49): atomiciteit.
  Gesprek, ontvanger en eerste bijdrage ontstaan in één `POST /gesprekken`; de
  portal gebruikt geen JSON Commit.

Bewust niet gebouwd:

- **Autorisatie per gesprek.** Die is in de spec nog open. De portal gebruikt
  één service-account en controleert zelf: de gebruiker heeft toegang tot de
  zaak, het gesprek hoort bij die zaak, en voor schrijven heeft de gebruiker een
  actieve deelname.
- **Server-Sent Events naar de browser.** Alleen de portal volgt `GET /events`;
  de browser pollt.
- **Ontvanger per zaak (open vraag C1).** Een gesprek van de inwoner gaat naar
  één ingestelde Actor.
- **Bijlagen aan de zaak koppelen (open vraag C5).** Een bijlage staat alleen in
  de Gesprekken API en verschijnt niet bij de documenten van de zaak.
- **ZGW-notificaties.** Die horen niet bij de spec; er is geen webhook meer.
- **`laatsteBijdrage`.** De sectie toont de bijdragen van het geopende gesprek
  en haalt daarvoor toch het detail op, dus dit veld scheelt nu geen werk.
