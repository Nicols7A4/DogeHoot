# generar_token.py
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # --- CAMBIO CLAVE AQUÍ ---
            # Ahora usamos 'InstalledAppFlow.from_client_secrets_file'
            # y le decimos que el redirect_uri es 'out-of-band'
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')

            print('Por favor, abre esta URL en tu navegador web:')
            print(auth_url)

            code = input('Pega el código de autorización que recibiste de Google aquí: ')

            flow.fetch_token(code=code)
            creds = flow.credentials

        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    print("\n¡El archivo token.json se ha creado con éxito!")

if __name__ == "__main__":
    main()