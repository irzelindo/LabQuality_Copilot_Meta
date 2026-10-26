import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "LabQuality Copilot", description: "Avaliar. Melhorar. Verificar." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-MZ"><body>{children}</body></html>;
}
