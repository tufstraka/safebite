import './globals.css'
import { Quicksand } from 'next/font/google'
import { metadata } from './metadata'

const quicksand = Quicksand({ 
  weight: ['400', '500', '600', '700'], 
  subsets: ['latin'], 
  display: 'swap' 
})

export { metadata }

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <link rel="canonical" href="https://safebite.locsafe.org" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
        
        {/* Structured Data for SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebApplication',
              name: 'SafeBite',
              description: 'Scan restaurant menus for allergens. Instant safety check for gluten, dairy, nuts, shellfish, and more.',
              url: 'https://safebite.locsafe.org',
              applicationCategory: 'HealthApplication',
              operatingSystem: 'Web, iOS, Android',
              offers: {
                '@type': 'Offer',
                price: '0',
                priceCurrency: 'USD',
              },
              author: {
                '@type': 'Person',
                name: 'Keith Kadima',
                url: 'https://github.com/tufstraka',
              },
              aggregateRating: {
                '@type': 'AggregateRating',
                ratingValue: '4.8',
                ratingCount: '127',
              },
            }),
          }}
        />
      </head>
      <body className={quicksand.className}>
        {children}
      </body>
    </html>
  )
}
