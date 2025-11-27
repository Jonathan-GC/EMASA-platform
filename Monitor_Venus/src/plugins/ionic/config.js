// Ionic configuration - Default behaviors and settings
export const ionicConfig = {
  // Animation settings
  animated: true,
  
  // Platform mode (md = Material Design, ios = iOS style)
  mode: 'md', // Can be 'ios', 'md', or undefined for auto-detect
  
  // Hardware back button behavior
  hardwareBackButton: true,
  
  // Ripple effect
  rippleEffect: true,
  
  // Swipe back gesture (iOS style)
  swipeBackEnabled: true,
  
  // Status bar
  statusTap: true,
  
  // Keyboard settings
  keyboardHeight: 290,
  scrollAssist: true,
  scrollPadding: true,
  inputShims: true,
  
  // Safe area
  safeAreaEnabled: true,
}

// Component-specific defaults
export const componentDefaults = {
  // Button defaults
  IonButton: {
    fill: 'solid',
    shape: 'round',
    size: 'default',
  },
  
  // Input defaults
  IonInput: {
    clearInput: true,
    fill: 'solid',
    labelPlacement: 'floating',
  },
  
  // Card defaults
  IonCard: {
    button: false,
  },
  
  // Modal defaults
  IonModal: {
    backdropDismiss: true,
    showBackdrop: true,
  },
  
  // Toast defaults
  IonToast: {
    duration: 3000,
    position: 'bottom',
  },
  
  // Loading defaults
  IonLoading: {
    spinner: 'crescent',
    backdropDismiss: false,
  },
  
  // Alert defaults
  IonAlert: {
    backdropDismiss: true,
  },
}

export default ionicConfig
