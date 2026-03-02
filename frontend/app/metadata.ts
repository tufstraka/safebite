import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'SafeBite - Scan Menus for Allergens | Instant Food Safety Check',
  description: 'Snap a pic of any menu and instantly see which dishes are safe for your allergies. Gluten, dairy, nuts, shellfish - we check them all. Made in Kenya.',
  keywords: [
    'food allergen scanner',
    'allergen detection',
    'menu scanner',
    'food allergy app',
    'safe food finder',
    'restaurant menu checker',
    'gluten free finder',
    'dairy free checker',
    'nut allergy app',
    'safebite',
    'kenya food tech'
  ],
  authors: [{ name: 'Keith Kadima', url: 'https://github.com/tufstraka' }],
  creator: 'Keith Kadima',
  publisher: 'SafeBite',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://safebite.locsafe.org',
    title: 'SafeBite - Instant Menu Allergen Scanner',
    description: 'Snap a menu, see which dishes are safe for your allergies instantly. Gluten, dairy, nuts, shellfish - checked in seconds.',
    siteName: 'SafeBite',
    images: [
      {
        url: 'https://safebite.locsafe.org/og-image.png',
        width: 1200,
        height: 630,
        alt: 'SafeBite - Instant Menu Allergen Scanner',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeBite - Scan Menus for Allergens',
    description: 'Snap a menu, instantly see which dishes are safe for your allergies. Made in Kenya.',
    creator: '@dobynog',
    images: ['https://safebite.locsafe.org/og-image.png'],
  },
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'SafeBite',
  },
  formatDetection: {
    telephone: false,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}
