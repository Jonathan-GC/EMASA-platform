# Support Module (Ionic + Vue)

A frontend module for creating support tickets with an optional file attachment.  
The module is **auth-aware**: it toggles fields based on whether the user is signed in (via JWT token).  
It also **chains** the operations so that after creating a ticket (metadata), it **uploads** the attachment using the returned `ticket` id.

---

## Table of Contents

1. Overview  
2. Architecture & Files  
3. Routing & Navigation  
   - paths.js  
   - components.js  
   - routes.js 
4. UI/UX Decisions  
5. Auth Awareness & JWT  
6. [Endpoints & Contracts]
8. Submit Flow  
9. Validation Rules  
10. Checklist

---

## Overview

**Goal:** Provide a clean Support form with:
- **Always** required: `title`, `description`.
- **Guest users (no token)**: show and require `guest_name`, `guest_email`.
- **Authenticated users (with token)**: do **not** show guest fields; show a compact “Signed in as {account name}” badge; allow **file attachment**.
- **Two-step submission**:
  1) `POST support/ticket` (JSON metadata).
  2) If authenticated and a file is selected, `POST <ATTACMEENT_CREATE>` (FormData) with `{ file, ticket }`.

---

## Architecture & Files

```
src/
├─ components/
│  └─ forms/
│     └─ support/
│        └─ SupportForm.vue    # Main component (auth-aware + upload chaining)
├─ plugins/
│  └─ router/
│     ├─ paths.js              # Add SUPPORT: '/support'
│     ├─ components.js         # Add components.SUPPORT -> lazy load view
│     └─ routes.js             # Add route under DEFAULT_LAYOUT children
└─ api/
└─ api.js                # IMPORTANT: FormData handling fix
```

> We directly mounted `SupportForm.vue` in the router (no separate view wrapper).  
> If your project prefers `@views/support/index.vue`, you can wrap the form there.

---

## Routing & Navigation

### `paths.js`

Add the **Support path**:

```js
export const paths = {
  // ...existing entries
  SUPPORT: '/support',
}

```

### `components.js`

Register the Support view/component (lazy):

```js

    // rute support
    SUPPORT: () => import('@views/support/index.vue'),

```

### `routes.js`

Under the DEFAULT_LAYOUT children:

```js

         // ✅ Nueva ruta Support 

            {
            name: 'support',
            path: P.SUPPORT,
            component: C.SUPPORT,            
            meta: { title: 'Support' },       
            },

``` 

### `api.js`


```js
    //----[SUPPORT]----
    SUPPORT_TICKET = 'support/ticket/'
    ATTACMEENT_CREATE = 'support/attachment/'
```


### `Navbar.vue`

Add a Support item::

```vue

        // Support navbar 

        <router-link
          :to="paths.SUPPORT"
          class="nav-link"
          :class="{ active: $route.path.startsWith(paths.SUPPORT) }"
          @click="closeNavbar"
        >
          <ion-icon :icon="icons.helpBuoy"></ion-icon>
          Support
        </router-link>

```

## UI/UX Decision

Use floating labels with fill="solid" and class="custom" to match the design system.
Show a compact “Signed in as {account}” bar instead of a read-only input for user info.
Add icons (documentTextOutline, createOutline, personOutline, mailOutline, attachOutline) to improve scannability.
Use inline hints: errors on the left.
Show a chip-style preview for the selected file (name + size + remove).
Buttons: primary Submit, secondary Clear, both aligned to the right.

## Auth Awareness & JWT
- First I have to download the JWT decoder in order to extract the data.

```
npm install jwt-decode 
```

- The component calls API.getValidToken() to detect authentication (mirrors your useNotifications hook).
- It decodes the JWT (base64url) to extract the user_id claim (claims.user_id | claims.userId | claims.sub).
- The payload for the ticket uses the user field (not user_id) when logged in:


{ "title": "...", "description": "...", "user": 123 }

For guests, it sends:

{ "title": "...", "description": "...", "guest_name": "...", "guest_email": "..." }


```js

// ------------------ Auth (token + user name/email) ------------------
function base64UrlDecode(input: string): string {
  input = input.replace(/-/g, '+').replace(/_/g, '/')
  const pad = input.length % 4
  if (pad) input += '='.repeat(4 - pad)
  try { return atob(input) } catch { return '' }
}
function decodeJwtPayload(token: string): any | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const json = base64UrlDecode(parts[1])
  try { return JSON.parse(json) } catch { return null }
}
function extractUserId(claims: any): string | number | null {
  if (!claims || typeof claims !== 'object') return null
  return claims.user_id ?? claims.userId ?? claims.sub ?? null
}

```

## Endpoints & Contracts

### Create Ticket (JSON)

- Endpoint: support/ticket (tries alternative with/without trailing slash if needed).
- Method: POST
- Body (authenticated):

{ "title": "…", "description": "…", "user": 123 }

- Body (guest):

{ "title": "…", "description": "…", "guest_name": "…", "guest_email": "…" }

- Response: can be object ({ id: … }) or array ([{ id: … }]).
The code extracts ticketId from any of these shapes:

```js
const ticketId = Array.isArray(resTicket)
  ? resTicket[0]?.id ?? null
  : Array.isArray(resTicket?.data)
    ? resTicket.data[0]?.id ?? null
    : (resTicket?.data?.id ?? resTicket?.id ?? null)
```

## Upload Attachment (FormData)

- Endpoint constant: (API as any).ATTACMEENT_CREATE or fallback 'support/ticket/attachment'
- Method: POST
- Body (FormData):
file: <binary> (the uploaded file)
ticket: <id> (the id obtained from the ticket creation)


Example (Apidog):
```json
{
  "file": "<binary or URL in example>",
  "ticket": 72435142
}
```

Attachment upload (code excerpt):

```js
async function uploadAttachment(ticketId: string | number, file: File) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('ticket', String(ticketId))
  await API.post(ATTACHMENT_ENDPOINT, fd) // API helper now supports FormData
}
```

### API Helper: FormData Fix

To correctly send FormData, the api.js helper was updated so it does not stringify FormData and does not force Content-Type:

```js
            // Add body if applicable POST/PUT/PATCH
            if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
                // If it's FormData, we shouldn't use JSON.stringify or force Content-Type.
                // Let the browser set 'multipart/form-data' as the boundary.
                if (typeof FormData !== 'undefined' && data instanceof FormData) {
                    if (requestConfig.headers && requestConfig.headers['Content-Type']) {
                        delete requestConfig.headers['Content-Type']
                    }
                    requestConfig.body = data
                } else {
                    requestConfig.body = JSON.stringify(data);
                }
            }
```

This change ensures multipart/form-data; boundary=… is set by the browser and the server can parse the file.

### Submit Flow

1. Build ticket payload

- If logged in: { title, description, user }
- If guest: { title, description, guest_name, guest_email }


2. POST to support/ticket

- Extract ticketId from response (supports array or object).


3. If logged in and a file is selected:

- Build FormData with file and ticket.
- POST to ATTACMEENT_CREATE.


4. Show toasts for:

- Success (both steps)
- Success but attachment failed
- Validation warnings and server errors


### Validation Rules

- title: min 3 characters
- description: min 10 characters
- guest_name: min 2 characters (guest only)
- guest_email: valid email (guest only)
- Attachment:

Allowed types: png, jpg, jpeg, pdf, doc, docx, txt
Max size: 5 MB

### Checklist

- [x] Navigation: Navbar Support link routes to /support and highlights correctly.
- [x] Router: paths.SUPPORT, components.SUPPORT, routes.js entry under DEFAULT_LAYOUT present.
- [x] UI: Floating labels (fill="solid", class="custom"), icons, counters, helper notes.
- [x] Guest: Guest Name, Guest Email visible & required.
- [x] Logged in: badge “Signed in as {name}” visible; guest fields hidden.
- [x] Guest body: { title, description, guest_name, guest_email }.
- [x] Logged in body: { title, description, user }.
- [x] Extracts id from array or object responses.
- [x] Sends FormData with file and ticket.
