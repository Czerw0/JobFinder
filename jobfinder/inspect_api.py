'''
Szybki skrypt do sprawdzenia struktury odpowiedzi API RemoteOK.
Pobiera dane API i drukuje czytelny, sformatowany JSON, abyś mógł sprawdzić klucze i zawartość.
'''

import requests
import json
import sys


# Punkt końcowy API RemoteOK
API_URL = "https://remoteok.com/api"


HEADERS = {
    "User-Agent": "API-Inspector-Script/1.0"
}

def inspect_remoteok_api():
    """
    Wywołaj API RemoteOK, zweryfikuj odpowiedź i wydrukuj przyjazną dla człowieka analizę
    plus pełny ładnie sformatowany JSON.
    """
    print(f"Łączenie z punktem końcowym API: {API_URL}")

    try:
        # Wykonaj żądanie GET z timeoutem, aby nie wisiało w nieskończoność.
        response = requests.get(API_URL, headers=HEADERS, timeout=20)

        # Jeśli serwer odpowiedział błędnym statusem, wywołaj wyjątek.
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        print(f"\nBłąd HTTP: Serwer zwrócił kod statusu {e.response.status_code}")
        print(f"   Powód: {e.response.reason}")
        print(f"   Tekst odpowiedzi: {e.response.text}")
        sys.exit(1)  # Wyjdź z kodem niezerowym, aby wskazać błąd
    except requests.exceptions.RequestException as e:
        # Łapie problemy związane z siecią, takie jak timeouty lub błędy DNS.
        print(f"\nBłąd sieci: Nie można połączyć się z API.")
        print(f"   Szczegóły błędu: {e}")
        sys.exit(1)

    print(f"Sukces! Otrzymano odpowiedź (Kod statusu: {response.status_code}).")
    print("Parsowanie danych JSON...")

    try:
        # Parsuj ciało odpowiedzi jako JSON.
        data = response.json()
    except json.JSONDecodeError:
        print("\nJSON Error: The response from the API was not valid JSON.")
        print("Raw Response Text (first 500 characters)")
        print(response.text[:500])
        sys.exit(1)

    # Odpowiedź sparsowana pomyślnie — podaj szybką analizę.
    print("\nAnaliza odpowiedzi API")
    if isinstance(data, list):
        print(f"Główny element JSON to LISTA zawierająca {len(data)} elementów.")
        if data:
            # W RemoteOK pierwszy element to zwykle powiadomienie; drugi to pierwsza oferta pracy.
            item_to_inspect = data[1] if len(data) > 1 else data[0]
            print("\nKlucze znalezione w drugim elemencie (przykładowa oferta pracy):")
            for key in item_to_inspect.keys():
                print(f"  - {key}")
    elif isinstance(data, dict):
        print(f"Główny element JSON to SŁOWNIK (obiekt) z {len(data)} kluczami.")
        print("\nKlucze znalezione w słowniku:")
        for key in data.keys():
            print(f"  - {key}")
    else:
        print("JSON to pojedyncza wartość (np. string, liczba).")

    # Sprawdzanie zawartości
    print("\nPełna odpowiedź JSON (Sformatowana)")
    pretty_json = json.dumps(data, indent=2)
    print(pretty_json)


if __name__ == "__main__":
    inspect_remoteok_api()