# AI Conference Networking Finder

A dashboard-first conference networking product where each attendee creates a username and password, uploads a selfie, gets matched from group photos, and sees a live discovery panel ranked by interaction score.

## Product Flow

1. Attendee signs up with a unique username and password.
2. Attendee uploads a selfie and the system generates a 512D face embedding.
3. Event photos are uploaded and faces are detected automatically.
4. Each detected face is matched to an attendee using pgvector cosine similarity with a 0.6 threshold.
5. If 2 or more attendees appear in the same photo, their interaction score increases by 1.
6. The user dashboard shows a discovery panel sorted by interaction score.

## Dashboard Concept

### 1. Attendee Signup
- Fields: username, password, email, first name, last name.
- Username is the attendee's unique login identity.
- Each attendee maps to one Django user account and one attendee profile.
- The attendee profile is the record used for event matching and network discovery.

### 2. Onboarding Panel
- Upload selfie.
- Show embedding generation status.
- Show whether the profile is ready for matching.
- Allow selfie replacement.

### 3. Event Match Panel
- Show the current event.
- Show uploaded event photos.
- Show detection progress for each photo.
- Show matched attendees per photo.

### 4. Discovery Panel
- Show connections sorted by interaction score.
- Highlight strongest connections first.
- Show matched attendee name, event name, and score.
- Allow filtering by event.
- Surface attendees the user met most often.

### 5. Network Detail Panel
- Show all pairwise interactions.
- Show score trend.
- Show which photos caused the interaction increases.
- Show matched attendee profile details.

## Backend Contract

The backend should support these core concepts:

- One Django `User` per attendee login.
- One `Attendee` profile linked to that `User`.
- `Attendee.user.username` is the dashboard identity.
- `Interaction` records are stored per attendee pair and event.
- Discovery queries use attendee username or attendee ID.

### Recommended API Shape

- `POST /api/events/join/`
  - Creates user, attendee, and selfie upload.
  - Accepts `username`, `password`, `email`, `first_name`, `last_name`, `event_code`, `selfie`.

- `GET /api/attendees/{id}/`
  - Returns attendee profile details.

- `PATCH /api/attendees/{id}/update-selfie/`
  - Updates selfie and regenerates embedding.

- `GET /api/interactions/discovery_panel/?username=<username>&event_id=<id>`
  - Returns discovery feed sorted by interaction score.

- `GET /api/interactions/my_connections/?attendee_id=<id>&event_id=<id>`
  - Returns the attendee's network connections.

- `POST /api/events/{id}/upload_image/`
  - Uploads event photos for face detection.

- `GET /api/detected-faces/by_event/?event_id=<id>`
  - Returns recognized faces for an event.

## Suggested Frontend Screens

### Login / Signup
- Username and password login.
- Join event flow for new attendees.
- Selfie upload during onboarding.

### Attendee Dashboard
- Profile summary.
- Embedding ready state.
- Joined event(s).
- Latest photo matches.
- Interaction score summary.

### Discovery Panel
- Ranked list of strongest connections.
- Search by attendee name.
- Filter by event.
- Score badges.
- Match count per attendee.

### Event Feed
- Uploaded group photos.
- Face detection status.
- Matched attendee chips.
- Interaction increases triggered from the photo.

## Data Model Expectations

### Attendee
- Linked to Django `User`.
- Stores selfie.
- Stores 512D embedding.
- Tied to one event.

### Interaction
- Stores `event`, `attendee1`, `attendee2`, `score`.
- Pair ordering should be stable so duplicate records are avoided.
- Score increments when attendees appear together in a photo.

## UI Priority

The first frontend build should focus on:
- authentication and attendee signup,
- selfie onboarding,
- discovery panel sorted by score,
- event upload/matching status.

## Notes

- This repository currently contains the Django backend only.
- The frontend dashboard can be implemented as a separate web app that consumes these APIs.
- If a dedicated React frontend is added later, it should use the username-based attendee flow described above.
