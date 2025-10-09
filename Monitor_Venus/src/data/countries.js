// Country data with phone codes and flags
export const countries = [
  { name: 'Argentina', code: 'AR', phoneCode: '+54', flag: '🇦🇷' },
  { name: 'Bolivia', code: 'BO', phoneCode: '+591', flag: '🇧🇴' },
  { name: 'Brasil', code: 'BR', phoneCode: '+55', flag: '🇧🇷' },
  { name: 'Chile', code: 'CL', phoneCode: '+56', flag: '🇨🇱' },
  { name: 'Colombia', code: 'CO', phoneCode: '+57', flag: '🇨🇴' },
  { name: 'Costa Rica', code: 'CR', phoneCode: '+506', flag: '🇨🇷' },
  { name: 'Cuba', code: 'CU', phoneCode: '+53', flag: '🇨🇺' },
  { name: 'Ecuador', code: 'EC', phoneCode: '+593', flag: '🇪🇨' },
  { name: 'El Salvador', code: 'SV', phoneCode: '+503', flag: '🇸🇻' },
  { name: 'Guatemala', code: 'GT', phoneCode: '+502', flag: '🇬🇹' },
  { name: 'Honduras', code: 'HN', phoneCode: '+504', flag: '🇭🇳' },
  { name: 'México', code: 'MX', phoneCode: '+52', flag: '🇲🇽' },
  { name: 'Nicaragua', code: 'NI', phoneCode: '+505', flag: '🇳🇮' },
  { name: 'Panamá', code: 'PA', phoneCode: '+507', flag: '🇵🇦' },
  { name: 'Paraguay', code: 'PY', phoneCode: '+595', flag: '🇵🇾' },
  { name: 'Perú', code: 'PE', phoneCode: '+51', flag: '🇵🇪' },
  { name: 'Puerto Rico', code: 'PR', phoneCode: '+1', flag: '🇵🇷' },
  { name: 'República Dominicana', code: 'DO', phoneCode: '+1', flag: '🇩🇴' },
  { name: 'Uruguay', code: 'UY', phoneCode: '+598', flag: '🇺🇾' },
  { name: 'Venezuela', code: 'VE', phoneCode: '+58', flag: '🇻🇪' },
  { name: 'Estados Unidos', code: 'US', phoneCode: '+1', flag: '🇺🇸' },
  { name: 'Canadá', code: 'CA', phoneCode: '+1', flag: '🇨🇦' },
  { name: 'España', code: 'ES', phoneCode: '+34', flag: '🇪🇸' }
]

// Sort alphabetically by country name
countries.sort((a, b) => a.name.localeCompare(b.name))