Xiaomi MiIO bedient Xiaomi-apparaten vanuit Homey via het lokale miIO-protocol. Alles draait op je Homey en je lokale netwerk. Er wordt niets naar de cloud gestuurd.

Ondersteunde apparaten
- Mi Bedlamp 2: aan/uit, helderheid, kleur, kleurtemperatuur en stand
- Mi Smart staande ventilator (zhimi.fan.za4): aan/uit, snelheid, natuurlijke wind, oscillatie en hoek, LED-display, zoemer en kinderslot
- Mi Smart luchtbevochtiger (zhimi.humidifier.ca1 en cb1): aan/uit, stand, doelvochtigheid, droogstand, vochtigheid en temperatuur, LED-display, zoemer en kinderslot

Aan de slag
1. Zoek het IP-adres en de apparaattoken (32 hexadecimale tekens) van je apparaat op. De token kun je uit je Xiaomi-account halen met een token-extractor.
2. Kies in Homey Apparaat toevoegen, kies deze app en het type van je apparaat.
3. Vul een naam, het IP-adres, de token en hoe vaak het apparaat wordt uitgelezen in. De app controleert of het apparaat antwoordt voordat het wordt toegevoegd.

Goed om te weten
- Geef je apparaat een vast IP-adres in je router, zodat de app het blijft vinden.
- Het apparaat wordt om de paar seconden uitgelezen (minimaal elke 5 seconden). Een apparaat dat niet antwoordt, staat als niet beschikbaar en komt vanzelf terug.
- Problemen en ideeën zijn welkom op de GitHub-pagina van de app (zie de links van deze app).

Xiaomi en Mi zijn handelsmerken van Xiaomi Corporation. Xiaomi MiIO is een onafhankelijke app en is niet verbonden aan of goedgekeurd door Xiaomi.
