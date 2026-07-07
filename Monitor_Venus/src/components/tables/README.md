# Table Components - Clickable Cards Implementation

## Overview

This directory contains table components that display data in both **desktop** (ion-grid) and **mobile** (ion-card) views. A new composable `useCardNavigation` has been implemented to make mobile cards clickable, allowing users to navigate to detail pages by tapping anywhere on the card.

## What Was Implemented

### 1. **New Composable: `useCardNavigation.js`**

Located at: `src/composables/useCardNavigation.js`

This reusable composable provides functionality to:
- Make cards clickable for navigation
- Prevent navigation when clicking action buttons inside cards
- Provide CSS classes for hover/active effects
- Support optional callbacks before navigation

**Key Features:**
- ✅ Smart click detection (ignores clicks on buttons/actions)
- ✅ Router integration for navigation
- ✅ Customizable with callbacks
- ✅ Reusable across all table components

### 2. **Responsive Design Pattern**

The tables use `useResponsiveView` composable to switch between:
- **Desktop View** (`!isMobile`): ion-grid with rows/columns
- **Mobile View** (`isMobile`): ion-card components (now clickable)

### 3. **Implementation Pattern**

The pattern has been applied to the following tables:
- ✅ `applications/TableApplications.vue`
- ✅ `devices/TableDevices.vue`
- ✅ `tenants/TableTenants.vue`
- ✅ `workspaces/TableWorkspaces.vue`

**Pending implementation:**
- `deviceProfiles/TableDeviceProfiles.vue`
- `gateways/TableGateways.vue`
- `locations/TableLocations.vue`
- `machines/TableMachines.vue`
- `managers/TableManagers.vue`

---

## How to Implement in New Tables

Follow these steps to add clickable card navigation to any table component:

### Step 1: Import the Composable and QuickActions

```javascript
// Add these imports to your script setup
import { useCardNavigation } from '@composables/useCardNavigation.js'
import QuickActions from '../../operators/quickActions.vue'

// Initialize the composable
const { getCardClickHandler, getCardClass } = useCardNavigation()
```

### Step 2: Update the Mobile Card Template

Find the mobile card section (usually inside `v-else` after the desktop ion-grid) and add the click handler:

**Before:**
```vue
<ion-card v-for="item in paginatedItems" :key="item.id" class="item-card">
  <ion-card-content>
    <!-- card content -->
  </ion-card-content>
</ion-card>
```

**After:**
```vue
<ion-card 
  v-for="item in paginatedItems" 
  :key="item.id" 
  class="item-card"
  :class="getCardClass(true)"
  @click="(event) => getCardClickHandler(`/route/to/${item.id}`)(event)"
>
  <ion-card-content>
    <!-- card content -->
  </ion-card-content>
</ion-card>
```

**Important:** Replace `/route/to/${item.id}` with the actual route for your detail page. This should match the `:toView` prop in your QuickActions component.

### Step 3: Add CSS Styles

Add these styles at the end of your `<style scoped>` section:

```css
/* Clickable Card Styles */
.clickable-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}

.clickable-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.clickable-card:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### Step 4: Verify QuickActions Component

Make sure your card has a QuickActions component with the `card-actions` wrapper:

```vue
<div class="card-actions">
  <QuickActions 
    type="your-type"
    :index="item.id" 
    :name="item.name"
    :toView="`/route/to/${item.id}`"
    to-edit
    to-delete
    :initial-data="setInitialData(item)"
    @item-edited="handleItemRefresh"
    @item-deleted="handleItemRefresh"
  />
</div>
```

The `.card-actions` class is detected by the composable to prevent navigation when clicking buttons inside.

---

## Complete Example

Here's a complete example from `TableApplications.vue`:

### Script Setup
```javascript
import { ref, computed, onMounted, nextTick, inject } from 'vue'
import { useRouter } from 'vue-router'
import API from '@utils/api/api'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useTableSorting } from '@composables/Tables/useTableSorting.js'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { useCardNavigation } from '@composables/useCardNavigation.js'
import QuickActions from '../../operators/quickActions.vue'

const icons = inject('icons', {})
const router = useRouter()

// Responsive composable
const { isMobile } = useResponsiveView(768)

// Card navigation composable
const { getCardClickHandler, getCardClass } = useCardNavigation()

// ... rest of your component logic
```

### Template - Mobile Cards Section
```vue
<!-- Mobile Card View -->
<div v-else class="mobile-cards">
  <ion-card 
    v-for="app in paginatedItems" 
    :key="app.id" 
    class="application-card"
    :class="getCardClass(true)"
    @click="(event) => getCardClickHandler(`/infrastructure/applications/${app.id}/devices`)(event)"
  >
    <ion-card-content>
      <!-- Header -->
      <div class="card-header">
        <div class="card-title-section">
          <h3 class="card-title">{{ app.name }}</h3>
          <p class="card-subtitle">ID: {{ app.cs_application_id }}</p>
        </div>
        <ion-chip :color="getStatusColor(app.sync_status)">
          {{ app.sync_status }}
        </ion-chip>
      </div>

      <!-- Card details -->
      <div class="card-details">
        <div class="card-detail-row">
          <span class="detail-label">Cliente:</span>
          <span class="detail-value">{{ app.workspace.tenant }}</span>
        </div>
        <!-- more details -->
      </div>

      <!-- Card actions -->
      <div class="card-actions">
        <QuickActions 
          type="application"
          :index="app.id" 
          :name="app.name"
          :toView="`/infrastructure/applications/${app.id}/devices`"
          to-edit
          to-delete
          :initial-data="setInitialData(app)"
          @item-edited="handleItemRefresh"
          @item-deleted="handleItemRefresh"
        />
      </div>
    </ion-card-content>
  </ion-card>
</div>
```

### Styles
```css
/* Mobile Cards Styles */
.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.application-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}

/* Clickable Card Styles */
.clickable-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}

.clickable-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.clickable-card:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

---

## How It Works

### Click Handler Logic

The `getCardClickHandler` function returns a click handler that:

1. **Checks the clicked element** - Detects if the click was on:
   - `ion-button`
   - `.card-actions` div
   - Any `button` element

2. **Prevents navigation** if clicked on action buttons
   - Allows edit/delete/other actions to work normally

3. **Navigates to route** if clicked anywhere else on the card
   - Uses Vue Router's `push()` method

### Event Flow

```
User clicks card
    ↓
Click event captured
    ↓
Is it a button/action? ──YES──→ Do nothing (let button handle it)
    ↓ NO
Navigate to detail page
```

---

## Benefits

✅ **Better UX on Mobile** - Entire card is tappable, easier to interact with  
✅ **Consistent Behavior** - Same pattern across all tables  
✅ **Maintains Functionality** - Action buttons still work independently  
✅ **Visual Feedback** - Hover and press animations provide user feedback  
✅ **Reusable** - Single composable for all table components  

---

## Customization

### Change Animation Speed
Modify the transition duration in the CSS:
```css
.clickable-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease; /* Changed from 0.2s to 0.3s */
}
```

### Add Callback Before Navigation
```javascript
@click="(event) => getCardClickHandler(`/route/${item.id}`, () => {
  console.log('Navigating to item:', item.id)
})(event)"
```

### Disable Clickable Cards
Simply remove the `:class` and `@click` attributes:
```vue
<ion-card 
  v-for="item in paginatedItems" 
  :key="item.id" 
  class="item-card"
>
```

---

## Troubleshooting

### Cards not navigating?
- ✅ Check the route path is correct
- ✅ Verify the route exists in your router configuration
- ✅ Make sure you're calling the handler with `(event) => getCardClickHandler(route)(event)`

### Action buttons also navigating?
- ✅ Ensure buttons are wrapped in `<div class="card-actions">`
- ✅ Check that QuickActions component is imported correctly
- ✅ Verify the click event isn't propagating

### Hover effects not showing?
- ✅ Make sure the `.clickable-card` styles are in your `<style scoped>` section
- ✅ Verify the class is being applied with `:class="getCardClass(true)"`
- ✅ Check browser dev tools for style conflicts

### Cards not responsive?
- ✅ Ensure `useResponsiveView` composable is imported and initialized
- ✅ Verify the `v-else` condition for mobile cards is correct
- ✅ Check the breakpoint value (default is 768px)

---

## API Reference

### useCardNavigation()

Returns an object with the following methods:

#### `navigateToItem(route)`
Navigate to a specific route programmatically.
- **Parameters:** `route` (string) - The route path to navigate to
- **Returns:** void

#### `getCardClickHandler(route, callback?)`
Returns a click handler function for the card.
- **Parameters:** 
  - `route` (string) - The route path to navigate to
  - `callback?` (function) - Optional callback to execute before navigation
- **Returns:** Function - Click event handler

#### `getCardClass(clickable)`
Returns the CSS class name for clickable cards.
- **Parameters:** `clickable` (boolean) - Whether the card should be clickable
- **Returns:** string - 'clickable-card' or empty string

#### `getCardStyles(clickable)`
Returns inline style object for clickable cards.
- **Parameters:** `clickable` (boolean) - Whether the card should be clickable
- **Returns:** Object - Style object or empty object

---

## Next Steps

To complete the implementation across all tables, apply this pattern to:

1. **TableDeviceProfiles.vue** - Device profiles listing
2. **TableGateways.vue** - Gateways listing
3. **TableLocations.vue** - Locations listing
4. **TableMachines.vue** - Machines listing
5. **TableManagers.vue** - Managers/users listing

Each implementation should take approximately 5 minutes following the steps above.

---

## Related Files

- **Composable:** `src/composables/useCardNavigation.js`
- **Responsive Hook:** `src/composables/useResponsiveView.js`
- **Quick Actions:** `src/components/operators/quickActions.vue`
- **Tables:** `src/components/tables/`

---

## Notes

- The composable automatically handles router navigation
- No need to import `useRouter` in your component if only using for cards
- The composable is framework-agnostic and can be adapted for other Vue projects
- Works with both TypeScript and JavaScript components

---

**Last Updated:** November 10, 2025  
**Implemented By:** AI Assistant  
**Status:** ✅ Ready for use in remaining tables
