# [FRONTEND] Sistema Notifiche Multiplayer - Implementazione Completa

**Status:** 🆕 To Do
**Priority:** 1 (High - Critical UX)
**Estimate:** 8 punti story
**Labels:** `multiplayer`, `notifications`, `ux-improvement`, `firebase`, `websocket`

---

## 📋 Background

### Problema Attuale
- ✅ **Backend completo e funzionante** - Sistema notifiche implementato con FCM, inbox persistente, e preferenze utente
- ❌ **Frontend mancante** - Gli inviti multiplayer non vengono visualizzati all'utente invitato
- ❌ **Notifiche limitate** - Il banner appare solo in HomePage quando lo stato è `InvitationsLoaded`
- ❌ **Mancanza offline support** - Nessuna notifica quando l'app è in background o chiusa
- ❌ **Nessun feedback visivo/sonoro** - Mancanza di notifiche push e suoni per nuovi inviti

### Obiettivo
Implementare un sistema completo di notifiche multiplayer con supporto **real-time (WebSocket)**, **push notifications (FCM)**, **inbox persistente**, e **preferenze utente** per garantire che gli utenti ricevano sempre gli inviti anche quando l'app è chiusa.

---

## 🎯 Requisiti Funzionali

### 1. Setup Iniziale Firebase & Dependencies ✨

#### Task 1.1: Aggiungere Dependencies
```yaml
# pubspec.yaml
dependencies:
  firebase_core: ^3.10.0
  firebase_messaging: ^15.3.0
  flutter_local_notifications: ^18.0.0
  socket_io_client: ^2.0.0
  connectivity_plus: ^6.0.0
  shared_preferences: ^2.3.0
  timezone: ^0.9.0
  flutter_app_badger: ^1.5.0
```

#### Task 1.2: Configurare Firebase
- [ ] Scaricare `google-services.json` (Android) e `GoogleService-Info.plist` (iOS) dal backend team
- [ ] Aggiungere file Firebase al progetto (seguire `docs/FIREBASE_SETUP.md` dal backend)
- [ ] Generare Firebase configuration con FlutterFire CLI:
  ```bash
  flutterfire configure
  ```
- [ ] Inizializzare Firebase in `main.dart`:
  ```dart
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  ```

**Acceptance Criteria:**
- ✅ Firebase inizializzato senza errori
- ✅ App si avvia correttamente su Android e iOS
- ✅ Permessi notifiche richiesti correttamente (iOS)

**Time Estimate:** 1 punto

---

### 2. FCM Token Registration & Management 🔐

#### Task 2.1: Creare NotificationService Singleton
File: `lib/core/services/notification_service.dart`

Implementare:
- Metodo `registerFCMToken()` - Registra token FCM con backend
- Metodo `deleteFCMToken()` - Elimina token al logout
- Gestione permessi iOS
- Salvataggio token locale in SharedPreferences

Endpoint Backend da chiamare:
```dart
POST /api/devices/register
Body: {
  "device_token": "FCM_TOKEN",
  "platform": "android" | "ios",
  "device_info": {
    "model": "iPhone 13",
    "os_version": "iOS 16.0",
    "app_version": "1.0.0"
  }
}
```

#### Task 2.2: Integrare con Login/Logout
- [ ] Chiamare `registerFCMToken()` dopo login riuscito
- [ ] Chiamare `deleteFCMToken()` prima del logout
- [ ] Gestire errori di registrazione gracefully

**Acceptance Criteria:**
- ✅ Token FCM registrato al login
- ✅ Token eliminato al logout
- ✅ Token salvato localmente per retry in caso di errore
- ✅ Device info inclusa nella registrazione

**Time Estimate:** 1.5 punti

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 2

---

### 3. WebSocket Reconnection con Exponential Backoff 🔌

#### Task 3.1: Migliorare GlobalMultiplayerListener
File: `lib/features/games/multiplayer/presentation/services/global_multiplayer_listener.dart`

Implementare:
- **Exponential backoff:** 1s, 2s, 4s, 8s, 16s, max 30s
- **Connectivity monitoring:** Reconnect automatico quando network torna disponibile
- **Connection status stream:** Stream<bool> per indicatore UI
- **Logging dettagliato:** Per debug connessione
- **Graceful degradation:** App funziona anche se WebSocket offline

```dart
class WebSocketService {
  int _reconnectDelay = 1000;

  void _scheduleReconnect() {
    Timer(Duration(milliseconds: _reconnectDelay), () {
      socket.connect();
      _reconnectDelay = min(_reconnectDelay * 2, 30000);
    });
  }

  // Reset delay on successful connection
  socket.on('connect', (_) {
    _reconnectDelay = 1000;
  });
}
```

#### Task 3.2: Aggiungere Indicatore Connessione UI
- [ ] Widget che mostra stato connessione (verde/rosso) in AppBar
- [ ] StreamBuilder collegato a `connectionStream`
- [ ] Tooltip che spiega lo stato

**Acceptance Criteria:**
- ✅ WebSocket riconnette automaticamente con exponential backoff
- ✅ Reconnect immediato quando network torna disponibile
- ✅ Indicatore visivo mostra stato connessione in real-time
- ✅ Logging dettagliato per debug
- ✅ Nessun crash se WebSocket fallisce

**Time Estimate:** 1 punto

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 3

---

### 4. Gestione Multi-Canale Notifiche 📬

#### Task 4.1: Foreground Notifications (App Aperta)
```dart
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  // Mostra in-app overlay notification
  NotificationService().showInAppNotification(message.data);

  // OPZIONALE: Mostra anche local notification
  NotificationService().showLocalNotification(
    title: message.notification?.title,
    body: message.notification?.body,
  );
});
```

#### Task 4.2: Background Notifications (App in Background)
```dart
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();

  // Mostra local notification
  await NotificationService().showLocalNotification(
    title: message.notification?.title,
    body: message.notification?.body,
    payload: message.data,
  );
}
```

#### Task 4.3: Notification Tap Handling (App Terminated)
```dart
// Handle initial message che ha aperto l'app
RemoteMessage? initialMessage = await FirebaseMessaging.instance.getInitialMessage();
if (initialMessage != null) {
  _navigateToInvitation(initialMessage.data['invitation_id']);
}

// Handle tap quando app è in background
FirebaseMessaging.onMessageOpenedApp.listen((message) {
  _navigateToInvitation(message.data['invitation_id']);
});
```

#### Task 4.4: Local Notifications con Suoni Custom
- [ ] Configurare `flutter_local_notifications` con canali Android
- [ ] Aggiungere suoni custom per notifiche (file `notification_sound.mp3`)
- [ ] Configurare vibrazione pattern
- [ ] Supporto per notification actions (Accept/Decline)

**Acceptance Criteria:**
- ✅ Notifiche mostrate correttamente in foreground
- ✅ Notifiche native mostrate in background
- ✅ Tap su notifica apre invito specifico
- ✅ Deep linking funziona correttamente
- ✅ Suoni e vibrazione funzionano
- ✅ Badge count aggiornato correttamente

**Time Estimate:** 2 punti

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 4

---

### 5. Notification Inbox Persistente 📥

#### Task 5.1: Creare NotificationInboxScreen
File: `lib/features/notifications/screens/notification_inbox_screen.dart`

Features:
- **Lazy Loading:** Carica 20 notifiche alla volta con pagination
- **Pull-to-Refresh:** Ricarica notifiche
- **Swipe-to-Delete:** Dismissable widget per eliminare
- **Mark as Read:** Tap su notifica la marca come letta
- **Mark All Read:** Action button in AppBar
- **Filtri:** Filtra per tipo notifica (invitations, friends, etc.)
- **Raggruppamento:** Raggruppa per data (Today, Yesterday, This Week)
- **Empty State:** Messaggio quando non ci sono notifiche

Endpoints Backend:
```dart
GET /api/notifications?limit=20&offset=0&read=false&type=invitation_received
GET /api/notifications/unread-count
PUT /api/notifications/{id}/read
PUT /api/notifications/mark-all-read
DELETE /api/notifications/{id}
```

#### Task 5.2: Aggiungere Badge su Tab/Icon
```dart
Badge(
  label: Text('$unreadCount'),
  child: Icon(Icons.notifications),
)
```

**Acceptance Criteria:**
- ✅ Inbox mostra tutte le notifiche con pagination
- ✅ Pull-to-refresh funziona
- ✅ Swipe-to-delete funziona
- ✅ Notifiche non lette evidenziate (bold + pallino blu)
- ✅ Tap su notifica naviga alla schermata corretta
- ✅ Badge count accurato
- ✅ Performance ottimizzata (lazy loading)

**Time Estimate:** 1.5 punti

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 5

---

### 6. Notification Preferences (Impostazioni) ⚙️

#### Task 6.1: Creare NotificationPreferencesScreen
File: `lib/features/notifications/screens/notification_preferences_screen.dart`

Settings:
- **Enable Push Notifications:** Toggle globale
- **Quiet Hours (Do Not Disturb):**
  - Toggle per abilitare
  - Time picker per orario inizio (es: 22:00)
  - Time picker per orario fine (es: 08:00)
  - Rispetta fuso orario utente
- **Notification Types:** Checkboxes per ogni tipo:
  - Invitation Received ✅
  - Invitation Accepted ✅
  - Invitation Declined ✅
  - Invitation Expired ✅
  - Invitation Expiring Soon (5 min warning) ✅
  - Friend Online ✅
  - Friend Joined Room ✅
  - Room Started ✅

Endpoint Backend:
```dart
GET /api/notifications/preferences
PUT /api/notifications/preferences
Body: {
  "push_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "timezone": "Europe/Rome",
  "notification_types": {
    "invitation_received": true,
    ...
  }
}
```

**Acceptance Criteria:**
- ✅ Toggle push notifications funziona
- ✅ Quiet hours con time picker funzionano
- ✅ Preferenze per tipo notifica funzionano
- ✅ Salvataggio preferenze persistente
- ✅ UI responsive e intuitiva
- ✅ Validazione input (orari validi)

**Time Estimate:** 1 punto

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 6

---

### 7. Global Notification Overlay 🎯

#### Task 7.1: Creare NotificationOverlay Widget
File: `lib/shared/widgets/notification_overlay.dart`

Features:
- **Overlay globale:** Mostra notifiche su tutte le pagine
- **Animazioni:** Slide in/out da top con CurvedAnimation
- **Auto-dismiss:** Dismiss automatico dopo 5 secondi
- **Tap to action:** Tap naviga a invito
- **Close button:** X per chiudere manualmente
- **Suono:** Riproduci suono quando appare

#### Task 7.2: Integrare in MaterialApp
```dart
MaterialApp(
  builder: (context, child) {
    return Stack(
      children: [
        child!,
        NotificationOverlay(), // Overlay sempre sopra
      ],
    );
  },
)
```

#### Task 7.3: Connettere a NotificationService Stream
```dart
NotificationService().notificationStream.listen((notification) {
  _showOverlay(notification);
});
```

**Acceptance Criteria:**
- ✅ Overlay appare su tutte le pagine
- ✅ Animazioni smooth
- ✅ Suono riprodotto correttamente
- ✅ Auto-dismiss dopo 5 secondi
- ✅ Tap naviga correttamente
- ✅ Close button funziona
- ✅ Non interferisce con UI sottostante

**Time Estimate:** 0.5 punti

**Riferimento:** `docs/FRONTEND_NOTIFICATION_GUIDE.md` - Sezione 7

---

### 8. Cache Locale & Sincronizzazione 💾

#### Task 8.1: Cache Inviti in SharedPreferences
- [ ] Salvare lista inviti localmente
- [ ] Caricare da cache al startup
- [ ] Sincronizzare con backend quando online

#### Task 8.2: Lazy Loading HomePage
- [ ] Caricare inviti esistenti quando HomePage viene aperta
- [ ] Mostrare cache mentre si ricarica da backend
- [ ] Merge intelligente cache + backend data

**Acceptance Criteria:**
- ✅ Inviti visibili anche offline (da cache)
- ✅ Sincronizzazione automatica al riavvio
- ✅ HomePage carica inviti on-demand (non solo su WebSocket event)
- ✅ Nessuna duplicazione dati

**Time Estimate:** 0.5 punti

---

## 📁 File da Creare/Modificare

### File da Creare (7 nuovi):
```
lib/core/services/
  ├── notification_service.dart          [NEW] - Singleton per gestione notifiche
  └── websocket_service.dart              [NEW] - WebSocket con reconnection

lib/features/notifications/
  ├── screens/
  │   ├── notification_inbox_screen.dart  [NEW] - Inbox persistente
  │   └── notification_preferences_screen.dart [NEW] - Settings notifiche
  └── models/
      └── notification_item.dart          [NEW] - Model notifica

lib/shared/widgets/
  └── notification_overlay.dart           [NEW] - Overlay globale

lib/core/navigation/
  └── deep_linking_handler.dart           [NEW] - Deep linking handler
```

### File da Modificare (4 esistenti):
```
lib/main.dart                             [MODIFY] - Firebase init, overlay wrapper
lib/main_common.dart                      [MODIFY] - Shared initialization
lib/features/games/multiplayer/
  └── presentation/services/
      └── global_multiplayer_listener.dart [MODIFY] - Add reconnection logic
pubspec.yaml                              [MODIFY] - Add dependencies
```

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] NotificationService - Token registration/deletion
- [ ] WebSocketService - Reconnection logic
- [ ] NotificationItem model - Serialization

### Widget Tests
- [ ] NotificationInboxScreen - UI rendering
- [ ] NotificationPreferencesScreen - Settings persistence
- [ ] NotificationOverlay - Animations

### Integration Tests
- [ ] End-to-end: Invito inviato → Notifica ricevuta → Tap → Schermata invito aperta
- [ ] Foreground/Background/Terminated notification handling
- [ ] WebSocket reconnection dopo network loss
- [ ] Cache & sync dopo app restart

### Manual Testing
- [ ] Test su dispositivo Android fisico
- [ ] Test su dispositivo iOS fisico
- [ ] Test con app in background
- [ ] Test con app chiusa (terminated)
- [ ] Test quiet hours (non disturbare)
- [ ] Test preferenze per tipo notifica
- [ ] Test badge count
- [ ] Test suoni e vibrazione
- [ ] Test deep linking da notifica

---

## 📚 Documentazione Backend Disponibile

Il backend team ha fornito documentazione completa:

1. **`docs/NOTIFICATION_SYSTEM_SUMMARY.md`** - Overview sistema notifiche
2. **`docs/FIREBASE_SETUP.md`** - Setup Firebase (per ottenere file config)
3. **`docs/FRONTEND_NOTIFICATION_GUIDE.md`** - Guida completa con codice Flutter

**Endpoint Backend Disponibili (15+):**
- `POST /api/devices/register` - Registra FCM token
- `GET /api/notifications` - Lista notifiche (paginated)
- `GET /api/notifications/unread-count` - Badge count
- `PUT /api/notifications/{id}/read` - Marca come letta
- `GET /api/notifications/preferences` - Preferenze utente
- `PUT /api/notifications/preferences` - Aggiorna preferenze
- ... e altri (vedi documentazione)

---

## 🎯 Definition of Done

### Functionality
- ✅ Utente riceve notifiche push quando app è chiusa
- ✅ Utente vede tutte le notifiche in inbox persistente
- ✅ Utente può configurare preferenze notifiche (push, quiet hours, tipi)
- ✅ Utente riceve warning 5 minuti prima che invito scada
- ✅ Utente vede indicatore connessione WebSocket
- ✅ Tap su notifica apre invito specifico
- ✅ Badge count mostra numero notifiche non lette
- ✅ Suoni e vibrazione funzionano correttamente

### Quality
- ✅ Nessun crash o errore in produzione
- ✅ Performance: Lazy loading notifiche (no lag)
- ✅ Codice coperto da unit tests (>80%)
- ✅ Documentazione codice inline
- ✅ Codice review approvata

### UX
- ✅ UI intuitiva e responsive
- ✅ Animazioni smooth
- ✅ Feedback visivo chiaro
- ✅ Error handling graceful (fallback se WebSocket offline)

---

## 🚀 Priorità Implementazione Suggerita

### Sprint 1 (3 punti) - Core Functionality
1. Setup Firebase & Dependencies (1 pt)
2. FCM Token Registration (1.5 pts)
3. WebSocket Reconnection (0.5 pts) - Quick win

### Sprint 2 (2.5 punti) - Notification Handling
4. Multi-Channel Notifications (2 pts)
5. Cache & Sync (0.5 pts)

### Sprint 3 (3 punti) - UI & Polish
6. Notification Inbox (1.5 pts)
7. Notification Preferences (1 pt)
8. Global Overlay (0.5 pts)

**Total: 8.5 punti**

---

## ⚠️ Note Importanti

### Performance
- Lazy loading è **critico** per inbox con migliaia di notifiche
- WebSocket reconnection deve essere **exponential** per evitare storm
- Cache locale previene **flashing** durante loading

### Security
- **Mai** loggare FCM tokens in produzione
- Validare **sempre** input da notifiche (XSS prevention)
- Usare **deep linking** validati per navigation

### Platform-Specific
- **iOS:** Richiedere permessi notifiche esplicitamente
- **Android:** Configurare notification channels correttamente
- **iOS:** APNs certificate deve essere caricato su Firebase (fatto da backend team)

---

## 🆘 Support & Resources

### Documentazione
- Backend docs: `docs/FRONTEND_NOTIFICATION_GUIDE.md`
- Firebase docs: https://firebase.flutter.dev/
- Socket.IO Client: https://socket.io/docs/v4/client-api/

### Backend Endpoints
- Base URL: `https://api.goodplay.com` (production)
- Base URL: `http://localhost:5000` (development)
- Swagger docs: `https://api.goodplay.com/docs` (quando disponibile)

### Contatti
- Backend Team: Per domande su API
- Design Team: Per mockup UI notifiche
- QA Team: Per testing su dispositivi fisici

---

## 🎉 Success Metrics

Dopo implementazione, monitorare:
- **Notification Delivery Rate:** >95% delivery success
- **User Engagement:** % utenti che aprono notifiche
- **Preference Adoption:** % utenti che customizzano preferenze
- **WebSocket Uptime:** >99% connection success
- **Crash Rate:** <0.1% crashes related to notifications

---

**Ready to implement?** Inizia con Sprint 1 e segui la documentazione in `docs/FRONTEND_NOTIFICATION_GUIDE.md` per codice dettagliato!

**Questions?** Contatta il backend team per chiarimenti su API o Firebase setup.
