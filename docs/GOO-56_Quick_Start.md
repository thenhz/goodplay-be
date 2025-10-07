# GOO-56: Quick Start Guide
## Get Up and Running in 5 Minutes

**For**: Backend & Frontend Developers
**Goal**: Test the multiplayer system ASAP

---

## 🚀 Quick Setup (2 minutes)

### 1. Start Backend
```bash
cd goodplay-be
python app.py
# Backend running on http://localhost:5000
```

### 2. Verify Backend is Running
```bash
curl http://localhost:5000/api/health
# Should return: {"status": "healthy"}
```

---

## 🧪 Quick Test (3 minutes)

### Test 1: Create Room (30 seconds)

**Using cURL**:
```bash
# Login first
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'

# Copy the access_token from response

# Create room
curl -X POST http://localhost:5000/api/multiplayer/rooms \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "tic_tac_toe",
    "max_players": 4
  }'

# Note the room_code in response (e.g., "ABC123")
```

---

### Test 2: Search Rooms (30 seconds)

```bash
curl -X POST http://localhost:5000/api/multiplayer/rooms/search \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "tic_tac_toe",
    "privacy": "public",
    "page": 1
  }'

# Should show your room in the list
```

---

### Test 3: Join Room (30 seconds)

```bash
# Login as second user or use another token

# Join via room code
curl -X GET "http://localhost:5000/api/multiplayer/rooms/code/ABC123" \
  -H "Authorization: Bearer SECOND_USER_TOKEN"

# Get room_id from response, then join
curl -X POST "http://localhost:5000/api/multiplayer/rooms/ROOM_ID/join" \
  -H "Authorization: Bearer SECOND_USER_TOKEN"

# Success! Player 2 joined
```

---

### Test 4: Toggle Ready (30 seconds)

```bash
# User 2 marks ready
curl -X POST "http://localhost:5000/api/multiplayer/rooms/ROOM_ID/ready" \
  -H "Authorization: Bearer SECOND_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_ready": true}'

# Check ready status
curl -X GET "http://localhost:5000/api/multiplayer/rooms/ROOM_ID/ready-status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Should show: ready_count: 1, total_players: 2
```

---

### Test 5: Quick Match (30 seconds)

```bash
# New user wants quick match
curl -X POST http://localhost:5000/api/multiplayer/quick-match \
  -H "Authorization: Bearer THIRD_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"game_id": "tic_tac_toe"}'

# Should automatically join your room
```

---

## 📱 Frontend Quick Test

If you've implemented GOOUI-40:

### Flow 1: Create & Join (2 minutes)
1. **Device A**: Open app → Login → "Create Room"
2. **Device A**: Select game → Create → Copy room code
3. **Device B**: Open app → Login → "Join Room" → Enter code
4. **Device B**: Click "Join" → Should see lobby
5. **Both devices**: See each other in player list ✅

### Flow 2: Quick Match (1 minute)
1. **Device C**: Open app → Login → "Quick Match"
2. **Device C**: Select game → "Find Match"
3. **Device C**: Should join existing room from Flow 1 ✅

---

## 🐛 Quick Troubleshooting

### Problem: "ROOM_NOT_FOUND"
**Solution**: Room might have expired. Create a new one.

### Problem: "ROOM_FULL"
**Solution**: Room at max capacity. Try different room.

### Problem: "AUTHENTICATION_REQUIRED"
**Solution**: Check if token is valid. Re-login if needed.

### Problem: "NO_ROOMS_AVAILABLE" (Quick Match)
**Solution**: No public rooms exist. Create one first.

---

## 📊 Quick Health Check

### All Systems Green?
```bash
# Check backend
curl http://localhost:5000/api/health

# Check multiplayer stats
curl http://localhost:5000/api/multiplayer/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show:
# - total_rooms: X
# - waiting_rooms: Y
# - playing_rooms: Z
```

---

## 📚 Next Steps

Once basic testing works:

1. **Full Testing**: Follow `GOO-56_Testing_Guide.md`
2. **API Reference**: Check `docs/openapi/games.yaml`
3. **Frontend Specs**: Review GOOUI-40 in Linear
4. **WebSocket**: Test real-time updates (see Testing Guide)

---

## 🎯 Expected Results Summary

After 5 minutes, you should have:
- ✅ Created a room
- ✅ Searched for rooms
- ✅ Joined a room
- ✅ Toggled ready state
- ✅ Tested quick match

**All working?** → Proceed to full testing guide! 🎉

**Issues?** → Check `GOO-56_Implementation_Summary.md` for troubleshooting

---

## 📞 Quick Help

- **API not responding**: Check if backend is running
- **401 Unauthorized**: Token expired, re-login
- **404 Not Found**: Wrong endpoint URL
- **500 Internal Server Error**: Check backend logs: `tail -f logs/app.log`

---

**Ready to dive deeper?**
→ Open `GOO-56_Testing_Guide.md` for comprehensive testing scenarios

**Need API details?**
→ Open GOOUI-40 Linear card for complete API specifications

---

_Quick Start Guide - GOO-56_
_Get started in 5 minutes! 🚀_
