import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AuthProvider } from "@/providers/AuthProvider";

const pretendard = localFont({
  src: [
    {
      path: "../fonts/PretendardVariable.woff2",
      weight: "45 920",
      style: "normal",
    },
  ],
  variable: "--font-pretendard",
  display: "swap",
  preload: true,
  adjustFontFallback: false,
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#558C8C",
};

export const metadata: Metadata = {
  title: {
    default: "소싱 대시보드",
    template: "%s | 소싱 대시보드",
  },
  description: "무신사 상품 수집 및 네이버 스마트스토어 자동 등록 관리 도구",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={`${pretendard.variable} scroll-smooth`}>
      <body className="min-h-screen bg-background text-foreground font-sans antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
