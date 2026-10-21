<template>
  <div class="footer-container">
    <div class="footer-content">
      <p class="footer-copyright">
        © {{ currentYear }} Monitor Platform. All rights reserved.
      </p>
      <div class="footer-links">
        <a href="/privacy" class="footer-link">Privacy Policy</a>
        <span class="footer-separator">•</span>
        <a href="/terms" class="footer-link">Terms of Service</a>
        <span class="footer-separator">•</span>
        <a href="/support" class="footer-link">Support</a>
      </div>
      <p class="footer-version">
        Version {{ appVersion }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
// Versión canónica desde package.json (fuente única de verdad, en tiempo de build)
import { version } from '../../../package.json'

const currentYear = computed(() => new Date().getFullYear())
const appVersion = version
</script>

