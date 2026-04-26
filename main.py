import os
import json
import secrets
import string
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
def generiere_key_aus_passwort(passwort, salt):
    """Erzeugt den mathematischen Schlüssel aus Passwort und Salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passwort.encode()))
def setup_master():
    """Ersteinrichtung: Erstellt Master-Passwort und Recovery Key."""
    print("\n" + "="*40)
    print("   WILLKOMMEN BEIM FINKE-VAULT SETUP")
    print("="*40)
    while True:
        pw = input("Neues Master-Passwort festlegen: ")
        pw_check = input("Passwort wiederholen: ")
        if pw == pw_check and len(pw) >= 4:
            break
        print("\n[!] Fehler: Passwörter ungleich oder zu kurz.")
    salt = os.urandom(16)
    recovery_key = secrets.token_hex(16).upper()
    config = {
        "salt": salt.hex(),
        "recovery_check": recovery_key 
    }
    
    with open(".vault_config", "w") as f:
        json.dump(config, f)
    print("\n" + "!"*40)
    print(f"DEIN RECOVERY KEY: {recovery_key}")
    print("NOTIERE DIR DIESEN KEY! Er ist dein einziger")
    print("Notausgang, wenn du das Passwort vergisst.")
    print("!"*40)
    input("\nDrücke Enter, wenn du bereit bist...")
    return pw, salt
def daten_laden():
    if not os.path.exists("passwoerter.json"):
        return {}
    try:
        with open("passwoerter.json", "r") as f:
            return json.load(f)
    except:
        return {}
def passwort_speichern(dienst, passwort, f_obj):
    daten = daten_laden()
    verschluesselt = f_obj.encrypt(passwort.encode())
    daten[dienst] = verschluesselt.decode()
    with open("passwoerter.json", "w") as f:
        json.dump(daten, f, indent=4)
    print(f"\n[OK] {dienst} wurde sicher im Tresor verstaut.")
def main():
    if not os.path.exists(".vault_config"):
        master_pw, salt = setup_master()
    else:
        with open(".vault_config", "r") as f:
            config = json.load(f)
        salt = bytes.fromhex(config["salt"])
        saved_recovery = config["recovery_check"]
        print("\n" + "="*30)
        print("   FINKE-VAULT: LOGIN")
        print("="*30)
        eingabe = input("Passwort (oder Recovery Key): ")
        if eingabe.upper() == saved_recovery.upper():
            print("\n[RECOVERY] Notausgang erkannt!")
            master_pw = input("Bitte neues Master-Passwort festlegen: ")
        else:
            master_pw = eingabe
    key = generiere_key_aus_passwort(master_pw, salt)
    f_obj = Fernet(key)
    while True:
        print("\n" + "="*40)
        print("      FINKE-VAULT PRO v1.3")
        print("="*40)
        print("[1] Passwort speichern")
        print("[2] Passwort generieren") 
        print("[3] Tresor öffnen")
        print("[4] Beenden")
        wahl = input("\nAktion: ") 
        if wahl == "1":
            d = input("Dienst: ")
            p = input(f"Passwort für {d}: ")
            passwort_speichern(d, p, f_obj)     
        elif wahl == "2":
            d = input("Dienst: ")
            gen_pw = ''.join(secrets.choice(string.ascii_letters + string.digits + "!$%") for _ in range(16))
            print(f"\nGeneriert: {gen_pw}")
            passwort_speichern(d, gen_pw, f_obj)
        elif wahl == "3":
            daten = daten_laden()
            if not daten:
                print("\nDer Tresor ist leer.")
            else:
                print("\n" + "-"*50)
                print(f"{'DIENST':<20} | {'PASSWORT'}")
                print("-" * 50)
                for d, s in daten.items():
                    try:
                        entsperrt = f_obj.decrypt(s.encode()).decode()
                        print(f"{d:<20} | {entsperrt}")
                    except:
                        print(f"{d:<20} | [FEHLER: Falsches Passwort]")
                print("-" * 50)
        elif wahl == "4":
            print("\nTresor gesperrt. Bis zum nächsten Mal!")
            break
if __name__ == "__main__":
    main()