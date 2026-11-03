import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "LabQuality Copilot", description: "Avaliar. Melhorar. Verificar." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Browser writing extensions can add attributes to body before React hydrates.
  return <html lang="pt-MZ"><body suppressHydrationWarning>{children}</body></html>;
}
