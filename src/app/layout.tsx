import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { SiteFooter } from "@/components/SiteFooter";
import { SiteNav } from "@/components/SiteNav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Felix Zuo | Manufacturing Project Coordination",
  description:
    "Manufacturing project coordination and digital process improvement portfolio with sanitized public case studies and tool evidence.",
  openGraph: {
    title: "Felix Zuo | Manufacturing Project Coordination",
    description:
      "Evidence-backed manufacturing project improvement portfolio focused on trial production, production notices, and operations visibility.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <SiteNav />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
