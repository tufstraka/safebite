import type { Metadata } from 'next'
import { Poppins } from 'next/font/google'
import './globals.css'
import Script from 'next/script'

const poppins = Poppins({ weight: ['400', '500', '600', '700'], subsets: ['latin'], display: 'swap' })

export const metadata: Metadata = {
  title: 'SafeBite | snap your food',
  description: 'take a pic of your menu. check for allergens instantly.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const gaId = process.env.NEXT_PUBLIC_GA_ID
  const analyticsEnabled = process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true'

  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#10b981" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="SafeBite" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        {analyticsEnabled && gaId && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${gaId}');
              `}
            </Script>
          </>
        )}
      </head>
      <body className={poppins.className}>{children}</body>
    </html>
  )
}
