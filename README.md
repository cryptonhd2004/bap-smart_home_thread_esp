# Prvky chytré domácnosti s ESP32 používající protokol Thread

*Smart home components based on ESP32 using the Thread protocol*

Semestrální práce, VUT v Brně, FEKT, Ústav telekomunikací, 2026/2027.

- **Autor:** David Šindelář
- **Vedoucí:** doc. Ing. Ivo Lattenberg, Ph.D.
- **Detail práce:** https://www.vut.cz/studenti/zav-prace/detail/179908

## O projektu

Návrh a výroba tří jednoduchých zařízení chytré domácnosti s ESP32 komunikujících přes Thread (Matter): čidla teploty, žárovky a vypínače. Zařízení se budou integrovat do Home Assistant nebo Google Home.

## Struktura repozitáře

| Složka | Obsah |
|---|---|
| `bap_text/` | text práce (LaTeX) |
| `esp_thread/` | projekt v KiCadu (schéma a DPS) |
| `test_builds/` | testovací buildy firmwaru |
| `logs_for_debuging/` | logy z ladění |

## Stav
Porovnání IKEA Alpstuga (referenční) a BMP180 na ESP32 přes Thread. Data pocházejí z Home Assistant, měřilo se 3 dny 10 h (1.–5. 10. 2026).

| Veličina | Hodnota |
|---|---|
| Střední rozdíl (BMP180 − Alpstuga) | −0,31 °C |
| Směrodatná odchylka rozdílu | 0,18 °C |
| RMSE | 0,36 °C |
| Rozsah rozdílu | −1,54 až +1,11 °C |
| Korelace | 0,89 |

Pravděpodobně bude třeba vyměnit senzor a porovnat s etalonovým měřidlem.

Práce je rozpracovaná.