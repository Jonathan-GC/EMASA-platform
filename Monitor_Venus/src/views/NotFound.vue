<template>
  <ion-page>
    <ion-content>
      <div class="notfound-container">
        <div class="content">
          <h2 class="code">404</h2>
          <h1 class="title">Página no encotrada</h1>
          <p class="subtitle">Perdona, no pudimos encontrar la página que buscas.</p>

          <router-link :to="paths.HOME" class="back-link">
            <ion-icon :icon="arrowBackSharp"></ion-icon>
            <span>Ir al inicio</span>
          </router-link>
        </div>
        <auth-footer />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { IonPage, IonContent, IonIcon } from '@ionic/vue'
import { arrowBackSharp } from 'ionicons/icons'
import { paths } from '@/plugins/router/paths'
</script>

  <style scoped>
  .footer-container {
    position: absolute;
    bottom: 0;
    width: 100%;
  }
.notfound-container {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, rgba(9,30,31,0.2), rgba(9,30,31,0.9)), url('/src/assets/img/verify.jpg');
  background-size: cover;
  background-position: center;
  color: #fff;
}

.content {
  text-align: center;
  padding: 3rem 2rem;
  backdrop-filter: blur(2px);
}

.code {
  font-size: 1rem;
  letter-spacing: 0.6rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

.title {
  font-size: 4rem;
  font-weight: 700;
  margin: 0.25rem 0 0.5rem;
}

.subtitle {
  color: rgba(255,255,255,0.85);
  margin-bottom: 1.25rem;
  font-size: 1.15rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  background: rgba(255,255,255,0.06);
  border-radius: 999px;
  padding: 10px 16px;
  text-decoration: none;
  font-weight: 600;
}

.back-link ion-icon { font-size: 18px; }

@media (max-width: 768px) {
  .title { font-size: 2.2rem; }
  .subtitle { font-size: 1rem; }
}
</style>
