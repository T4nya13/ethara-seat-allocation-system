import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ethara — Seat Allocation & Project Mapping System",
  description:
    "Manage seat allocation for 5,000+ employees. Quickly find where an employee is seated, which project they belong to, and which seats are available — with AI-assisted queries.",
  keywords: [
    "seat allocation",
    "project mapping",
    "employee management",
    "HR system",
    "Ethara",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
