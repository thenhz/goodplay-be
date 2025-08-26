# GoodPlay Backend

Backend REST API sviluppato con Flask, MongoDB, JWT Authentication e CORS.

## Architettura

Il progetto segue il pattern **Repository + Service Layer** con la seguente struttura:

- **Models**: Definizione delle entità (User)
- **Repositories**: Accesso ai dati e operazioni CRUD su MongoDB
- **Services**: Logica di business e validazioni
- **Controllers**: Gestione delle route e richieste HTTP
- **Utils**: Utility, decoratori e helper functions

## Funzionalità

- ✅ Registrazione utenti
- ✅ Login e logout
- ✅ Autenticazione JWT (Access + Refresh Token)  
- ✅ Gestione profilo utente
- ✅ Validazione input
- ✅ Logging strutturato
- ✅ CORS configurabile
- ✅ Configurazione per ambienti (dev/prod/test)

## Setup

1. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configura le variabili d'ambiente:**
   ```bash
   cp .env.example .env
   # Modifica .env con i tuoi valori
   ```

3. **Avvia MongoDB:**
   ```bash
   # Se hai Docker:
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

4. **Avvia l'applicazione:**
   ```bash
   python app.py
   ```

## Endpoints API

### Autenticazione

- `POST /api/auth/register` - Registrazione nuovo utente
- `POST /api/auth/login` - Login utente
- `POST /api/auth/refresh` - Rinnovo access token
- `GET /api/auth/profile` - Ottieni profilo utente (richiede auth)
- `PUT /api/auth/profile` - Aggiorna profilo utente (richiede auth)
- `POST /api/auth/logout` - Logout utente (richiede auth)

### Health Check

- `GET /api/health` - Status dell'API

## Configurazione

Tutte le configurazioni sono gestite tramite variabili d'ambiente nel file `.env`:

- `SECRET_KEY`: Chiave segreta Flask
- `JWT_SECRET_KEY`: Chiave segreta per JWT
- `MONGO_URI`: URI di connessione MongoDB
- `CORS_ORIGINS`: Domini autorizzati per CORS
- `LOG_LEVEL`: Livello di logging

## Struttura del Progetto

```
├── app/
│   ├── __init__.py              # Factory app Flask
│   ├── models/
│   │   └── user.py              # Modello User
│   ├── repositories/
│   │   ├── base_repository.py   # Repository base
│   │   └── user_repository.py   # Repository User
│   ├── services/
│   │   └── auth_service.py      # Service autenticazione
│   ├── controllers/
│   │   └── auth_controller.py   # Controller autenticazione
│   └── utils/
│       ├── decorators.py        # Decoratori (auth_required, etc.)
│       ├── responses.py         # Helper per risposte HTTP
│       └── logger.py            # Configurazione logging
├── config/
│   └── settings.py              # Configurazioni app
├── app.py                       # Entry point applicazione
├── requirements.txt             # Dipendenze Python
└── .env.example                 # Template variabili d'ambiente
```

## Aggiungere Nuovi Endpoint

Per aggiungere nuovi endpoint REST:

1. **Crea il modello** in `app/models/`
2. **Implementa il repository** in `app/repositories/`
3. **Crea il service** con la logica business in `app/services/`
4. **Aggiungi il controller** con le route in `app/controllers/`
5. **Registra il blueprint** in `app/__init__.py`

Esempio di nuovo endpoint:
```python
# In app/controllers/example_controller.py
from flask import Blueprint
from app.utils.decorators import auth_required
from app.utils.responses import success_response

example_bp = Blueprint('example', __name__)

@example_bp.route('/items', methods=['GET'])
@auth_required
def get_items(current_user):
    # La logica business va nel service
    return success_response("Items retrieved", items)
```