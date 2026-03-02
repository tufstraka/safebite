import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'SafeBite - AI Food Allergen Scanner | Scan Menus Instantly',
  description: 'Scan restaurant menus with AI to detect allergens instantly. SafeBite analyzes dishes for gluten, dairy, nuts, shellfish, and more. Made in Kenya.',
  keywords: [
    'food allergen scanner',
    'allergen detection',
    'menu scanner',
    'food allergy app',
    'ai food safety',
    'restaurant menu analyzer',
    'gluten free scanner',
    'dairy free checker',
    'nut allergy detector',
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
    title: 'SafeBite - AI Food Allergen Scanner',
    description: 'Scan restaurant menus instantly with AI. Detect allergens like gluten, dairy, nuts, and shellfish. Safe dining made easy.',
    siteName: 'SafeBite',
    images: [
      {
        url: 'https://safebite.locsafe.org/og-image.png',
        width: 1200,
        height: 630,
        alt: 'SafeBite - AI Food Allergen Scanner',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeBite - AI Food Allergen Scanner',
    description: 'Scan menus with AI to detect allergens instantly. Safe dining made easy.',
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
