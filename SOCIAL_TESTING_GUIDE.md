# 🧪 Guida per Testare GOO-7 Social Graph con Postman

## 📋 Panoramica

Questa guida spiega come testare tutti gli endpoint della **GOO-7 Social Graph Foundation** utilizzando la collezione Postman aggiornata.

## 🚀 Setup Iniziale

### 1. Importare la Collezione Postman
- Importa `GoodPlay_API.postman_collection.json` in Postman
- Importa l'environment `GoodPlay_Local.postman_environment.json`

### 2. Configurare l'Environment
Assicurati che le variabili environment siano impostate:
```json
{
  "base_url": "http://localhost:5000",
  "access_token": "", // Si popola automaticamente dopo il login
  "refresh_token": "", // Si popola automaticamente dopo il login
  "friend_request_id": "", // Si popola automaticamente
  "search_user_id": "" // Si popola automaticamente
}
```

## 🔧 Setup Test Environment

### 1. Registrare Utenti di Test
Prima crea almeno 2-3 utenti per testare le funzionalità social:

```bash
# Utente 1
POST /api/auth/register
{
    "email": "user1@test.com",
    "password": "test123456",
    "first_name": "John",
    "last_name": "Doe"
}

# Utente 2
POST /api/auth/register
{
    "email": "user2@test.com",
    "password": "test123456",
    "first_name": "Jane",
    "last_name": "Smith"
}

# Utente 3
POST /api/auth/register
{
    "email": "user3@test.com",
    "password": "test123456",
    "first_name": "Alice",
    "last_name": "Wonder"
}
```

### 2. Login e Ottenere Token
Fai login con uno degli utenti per ottenere l'access_token:

```bash
POST /api/auth/login
{
    "email": "user1@test.com",
    "password": "test123456"
}
```

Il token verrà automaticamente salvato nell'environment da Postman.

## 📊 Flusso di Test Completo

### Fase 1: Informazioni Base 🔍

#### 1.1 Get Social Stats
```bash
GET /api/social/stats
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Statistiche iniziali (tutti 0)
```json
{
    "success": true,
    "message": "SOCIAL_STATS_SUCCESS",
    "data": {
        "friends_count": 0,
        "pending_requests_count": 0,
        "sent_requests_count": 0,
        "blocked_users_count": 0
    }
}
```

#### 1.2 Get Friends List (Empty)
```bash
GET /api/social/friends?limit=50&skip=0
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Lista vuota
```json
{
    "success": true,
    "message": "FRIENDS_LIST_SUCCESS",
    "data": {
        "friends": [],
        "total": 0,
        "pagination": { "limit": 50, "skip": 0, "has_more": false }
    }
}
```

### Fase 2: Ricerca Utenti 🔎

#### 2.1 Search Users
```bash
POST /api/social/users/search
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "query": "jane",
    "limit": 20,
    "skip": 0
}
```
**Risultato Atteso**: Trova utenti che matchano "jane"
**Nota**: Postman salverà automaticamente l'ID del primo utente in `search_user_id`

#### 2.2 Get Friend Suggestions
```bash
GET /api/social/users/suggestions?limit=10
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Suggerimenti basati su algoritmo di discovery

### Fase 3: Gestione Amicizie 🤝

#### 3.1 Send Friend Request
```bash
POST /api/social/friend-request
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "target_user_id": "REPLACE_WITH_ACTUAL_USER_ID"
}
```
**Prima di eseguire**: Sostituisci `REPLACE_WITH_ACTUAL_USER_ID` con un ID utente reale
**Risultato Atteso**: Friend request creata, `friend_request_id` salvato in environment

#### 3.2 Get Friend Requests (Received)
**Esegui con l'account del destinatario**
```bash
GET /api/social/friend-requests?type=received&limit=20&skip=0
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Lista delle richieste ricevute

#### 3.3 Get Friend Requests (Sent)
**Esegui con l'account del mittente**
```bash
GET /api/social/friend-requests?type=sent&limit=20&skip=0
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Lista delle richieste inviate

#### 3.4 Accept Friend Request
**Esegui con l'account del destinatario**
```bash
PUT /api/social/friend-request/{{friend_request_id}}/accept
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Richiesta accettata, amicizia creata

#### 3.5 Get Friends List (Now with Friends)
```bash
GET /api/social/friends?limit=50&skip=0
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Lista con il nuovo amico

### Fase 4: Gestione Relazioni Advanced 🎯

#### 4.1 Get Relationship Status
```bash
GET /api/social/relationship-status/USER_ID_HERE
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Status dettagliato della relazione

#### 4.2 Remove Friend
```bash
DELETE /api/social/friends/USER_ID_HERE
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Amicizia rimossa

#### 4.3 Block User
```bash
POST /api/social/users/USER_ID_HERE/block
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Utente bloccato

#### 4.4 Get Blocked Users
```bash
GET /api/social/blocked-users?limit=50&skip=0
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Lista utenti bloccati

#### 4.5 Unblock User
```bash
DELETE /api/social/users/USER_ID_HERE/unblock
Authorization: Bearer {{access_token}}
```
**Risultato Atteso**: Utente sbloccato

### Fase 5: Test Error Cases ❌

#### 5.1 Send Friend Request to Self
```bash
POST /api/social/friend-request
{
    "target_user_id": "YOUR_OWN_USER_ID"
}
```
**Risultato Atteso**: Errore `CANNOT_INTERACT_WITH_SELF`

#### 5.2 Accept Non-Existent Request
```bash
PUT /api/social/friend-request/FAKE_ID/accept
```
**Risultato Atteso**: Errore `FRIEND_REQUEST_NOT_FOUND`

#### 5.3 Search with Short Query
```bash
POST /api/social/users/search
{
    "query": "a"
}
```
**Risultato Atteso**: Errore `SEARCH_QUERY_TOO_SHORT`

## 🔄 Flusso di Test Automatizzato

### Test Scripts Postman
La collezione include test scripts automatici che:

1. **Send Friend Request**: Salva automaticamente `friend_request_id`
2. **Search Users**: Salva automaticamente `search_user_id`
3. **Login**: Salva automaticamente tokens

### Variabili Environment Auto-Popolate
- `access_token` - Da login
- `refresh_token` - Da login
- `friend_request_id` - Da send friend request
- `search_user_id` - Da search users

## 📝 Note per il Testing

### ID Utente
- Sostituisci `REPLACE_WITH_ACTUAL_USER_ID` con ID reali ottenuti da:
  - Ricerca utenti (`search_user_id` auto-popolato)
  - Response di registrazione utenti
  - Lista amici esistenti

### Ordine di Esecuzione
1. Registra 2-3 utenti
2. Login con utente 1
3. Cerca altri utenti
4. Invia friend request
5. Login con utente 2
6. Accetta friend request
7. Testa altre funzionalità

### Validazione Response
Ogni response include:
- `success: boolean`
- `message: string` (costante per localizzazione)
- `data: object` (dati specifici)

### Privacy Controls
- La ricerca utenti rispetta `friends_discovery` setting
- I controlli privacy vengono applicati automaticamente

## 🐛 Troubleshooting

### Token Scaduto
- Usa l'endpoint `POST /api/auth/refresh` con refresh_token

### Relationship Non Trovata
- Verifica che gli utenti esistano
- Controlla che non siano bloccati

### Search Vuota
- Verifica privacy settings degli utenti target
- Prova query più generiche

## ✅ Checklist Test Completo

- [ ] ✅ Social Stats iniziali
- [ ] ✅ Friends list vuota
- [ ] ✅ Search users funziona
- [ ] ✅ Friend suggestions funziona
- [ ] ✅ Send friend request
- [ ] ✅ Get received requests
- [ ] ✅ Get sent requests
- [ ] ✅ Accept friend request
- [ ] ✅ Friends list popolata
- [ ] ✅ Get relationship status
- [ ] ✅ Remove friend
- [ ] ✅ Block user
- [ ] ✅ Get blocked users
- [ ] ✅ Unblock user
- [ ] ✅ Test error cases
- [ ] ✅ Decline friend request
- [ ] ✅ Privacy controls

La collezione Postman è ora completa con tutti i 13 endpoint GOO-7! 🎉