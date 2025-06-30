// Arquivo: frontend/app/layout.js

import { Inter as FontSans } from "next/font/google"
import "./globals.css" // Importa seus estilos globais do Tailwind CSS
import { cn } from "@/lib/utils" // Importa a função utilitária da shadcn

// Configuração da fonte padrão
const fontSans = FontSans({
  subsets: ["latin"],
  variable: "--font-sans",
})

// Metadados do seu site (bom para SEO e para o título na aba do navegador)
export const metadata = {
  title: "Sistema de Relatórios",
  description: "Gerador de relatórios técnicos de motores",
}
export default function RootLayout({ children }) {
  return (
    <html lang="pt-br" suppressHydrationWarning>
      <head />
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          fontSans.variable
        )}
      >
        {children}
      </body>
    </html>
  )
}