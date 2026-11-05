# Prvky chytré domácnosti s ESP32 používající protokol Thread

*Smart home components based on ESP32 using the Thread protocol*

Bakalářská práce, VUT v Brně, FEKT, Ústav telekomunikací, 2026/2027.

- **Autor:** David Šindelář
- **Vedoucí:** doc. Ing. Ivo Lattenberg, Ph.D.
- **Detail práce:** https://www.vut.cz/studenti/zav-prace/detail/179908

## Výkresy DPS a schémata

| Zařízení | Schéma zapojení | Osazovací výkres DPS | Další |
|---|---|---|---|
| Čidlo teploty | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/esp_thread/schema_zapojeni.pdf) | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/esp_thread/plots/esp_thread__Assembly.pdf) | [projekt KiCad](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/tree/main/esp_thread) |
| Chytré světlo | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/chytre_svetlo/schema_zapojeni.pdf) | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/chytre_svetlo/plots/chytre_svetlo__Assembly.pdf) | [projekt KiCad](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/tree/main/chytre_svetlo) |
| Bateriový vypínač | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/Chytre_Tlacitko_BMS/schema_zapojeni.pdf) | [PDF](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/blob/main/Chytre_Tlacitko_BMS/plots/Chytre_Tlacitko_BMS__Assembly.pdf) | [projekt KiCad](https://github.com/cryptonhd2004/bap-smart_home_thread_esp/tree/main/Chytre_Tlacitko_BMS) |

## O projektu

Návrh a realizace tří zařízení chytré domácnosti, která komunikují protokolem
Matter přes síť Thread (IEEE 802.15.4) a jsou integrována do Home Assistant:

| Zařízení | Napájení | Poznámka |
|---|---|---|
| Čidlo teploty | ze sítě | měření teploty, výběr čidla na základě porovnání |
| Chytré světlo | ze sítě | Router v síti Thread, RGB LED WS2812B (Matter light endpoint) |
| Bateriový vypínač | baterie | ošetření zákmitů, nízká spotřeba |

Všechna zařízení jsou postavena na čipu Espressif ESP32-C6
(modul Seeed Studio XIAO ESP32-C6).

## Struktura repozitáře

| Složka / soubor | Obsah |
|---|---|
| `bap_text/` | text práce (LaTeX, šablona VUT) |
| `chytre_svetlo/` | KiCad: chytré světlo (schéma, DPS, PDF schématu a osazení) |
| `Chytre_Tlacitko_BMS/` | KiCad: bateriový vypínač (schéma, DPS, PDF, iBOM) |
| `esp_thread/` | KiCad: chytrý teploměr (schéma, DPS, PDF, výrobní soubory v `production/`) |
| `test_builds/` | testovací firmware: `c6-matter-teplomer-firmware.factory.bin`, konfigurace `test-teplomer.yaml` a `tlacitko-thread.yaml` |
| `logs_for_debuging/` | logy z ladění, data a skripty porovnání čidel (`output/` – grafy) |
| `github_qr.*` | QR kód repozitáře pro osazení na DPS |

## Stav

| Část | Stav |
|---|---|
| Teoretický úvod (IEEE 802.15.4, CSA) | hotovo |
| Porovnání čidel teploty a vlhkosti | hotovo |
| Schéma a DPS – teploměr, světlo, vypínač | hotovo, připraveno k odsouhlasení |
| Firmware | testovací buildy (teploměr, tlačítko), RGB světlo rozpracováno |
| Text práce | rozpracováno (výsledky, návrh schémat) |

### Porovnání čidel

Referenční čidlo je SHT40 (jen klidné minuty). Rozdíl je počítán jako čidlo minus SHT40.

**Teplota** (n = 3292)

| Čidlo | střední rozdíl [°C] | s_d [°C] | RMSE [°C] | podíl \|d\| ≤ 0,7 °C |
|---|---|---|---|---|
| ALPSTUGA (SEN63C) | 0,19 | 0,18 | 0,26 | 100,0 % |
| BMP180 | −0,74 | 0,02 | 0,74 | 8,3 % |
| DHT11 | 0,00 | 0,04 | 0,04 | 100,0 % |
| TIMMERFLOTTE | −0,52 | 0,07 | 0,53 | 99,4 % |

**Vlhkost** (n = 2882)

| Čidlo | střední rozdíl [%RH] | s_d [%RH] | RMSE [%RH] | podíl \|d\| ≤ 3,0 %RH |
|---|---|---|---|---|
| ALPSTUGA (SEN63C) | −8,86 | 0,69 | 8,89 | 0,0 % |
| DHT11 | −1,70 | 0,94 | 1,94 | 99,9 % |
| TIMMERFLOTTE | −6,21 | 0,87 | 6,27 | 0,0 % |

## Sestavení textu

Hlavní soubor je `bap_text/sablona-prace.tex`. Překlad: pdfLaTeX dvakrát.
Seznam literatury je psán ručně v `bap_text/text/literatura.tex`.