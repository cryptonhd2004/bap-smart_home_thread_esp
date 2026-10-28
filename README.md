# Prvky chytré domácnosti s ESP32 používající protokol Thread

*Smart home components based on ESP32 using the Thread protocol*

Bakalářská práce, VUT v Brně, FEKT, Ústav telekomunikací, 2026/2027.

- **Autor:** David Šindelář
- **Vedoucí:** doc. Ing. Ivo Lattenberg, Ph.D.
- **Detail práce:** https://www.vut.cz/studenti/zav-prace/detail/179908

## O projektu

Návrh a realizace tří zařízení chytré domácnosti, která komunikují protokolem
Matter přes síť Thread (IEEE 802.15.4) a jsou integrována do Home Assistant:

| Zařízení | Napájení | Poznámka |
|---|---|---|
| Čidlo teploty | ze sítě | měření teploty, výběr čidla na základě porovnání |
| Chytré světlo | ze sítě | Router v síti Thread, PWM stmívání |
| Bateriový vypínač | baterie | ošetření zákmitů, nízká spotřeba |

Všechna zařízení jsou postavena na čipu Espressif ESP32-C6
(modul Seeed Studio XIAO ESP32-C6).

## Struktura repozitáře

| Složka / soubor | Obsah |
|---|---|
| `bap_text/` | text práce (LaTeX, šablona VUT) |
| `chytre_svetlo/` | projekt KiCad: chytré světlo (schéma, DPS) |
| `Chytre_Tlacitko_BMS/` | projekt KiCad: bateriový vypínač (schéma, DPS) |
| `esp_thread/` | projekt KiCad: chytrý teploměr |
| `test_builds/` | testovací firmware: `c6-matter-teplomer-firmware.factory.bin`, konfigurace `test-teplomer.yaml` a `tlacitko-thread.yaml` |
| `logs_for_debuging/` | logy z ladění |

## Stav

Hotové je porovnání čidel teploty a vlhkosti vůči referenčnímu SHT40
(jen klidné minuty). Rozdíl je počítán jako čidlo minus SHT40.

**Teplota** (n = 1916)

| Čidlo | střední rozdíl [°C] | s_d [°C] | RMSE [°C] | podíl \|d\| ≤ 0,7 °C |
|---|---|---|---|---|
| ALPSTUGA (SEN63C) | 0,43 | 0,07 | 0,44 | 100,0 % |
| BMP180 | −0,75 | 0,02 | 0,75 | 0,5 % |
| DHT11 | 0,00 | 0,04 | 0,04 | 100,0 % |
| TIMMERFLOTTE | −0,43 | 0,08 | 0,44 | 100,0 % |

**Vlhkost** (n = 1690)

| Čidlo | střední rozdíl [%RH] | s_d [%RH] | RMSE [%RH] | podíl \|d\| ≤ 3,0 %RH |
|---|---|---|---|---|
| ALPSTUGA (SEN63C) | −7,53 | 0,45 | 7,55 | 0,0 % |
| DHT11 | −0,22 | 0,55 | 0,60 | 100,0 % |
| TIMMERFLOTTE | −4,88 | 0,25 | 4,88 | 0,0 % |

Práce je rozpracovaná. Hotový je teoretický úvod (IEEE 802.15.4, CSA),
další kapitoly se doplňují.

## Sestavení textu

Hlavní soubor je `bap_text/sablona-prace.tex`. Překlad: pdfLaTeX dvakrát.
Seznam literatury je psán ručně v `bap_text/text/literatura.tex`.