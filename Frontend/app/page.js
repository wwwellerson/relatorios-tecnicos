// Arquivo: frontend/app/page.js
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Users, FolderOpen } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-800">Sistema de Relatórios</CardTitle>
          <p className="text-gray-500 mt-2">Selecione uma opção para começar</p>
        </CardHeader>
        <CardContent className="space-y-4 p-6">
          <Link href="/novo-relatorio" className="block">
            <Button className="w-full h-14 text-lg justify-start" variant="default">
              <FileText className="mr-3 h-6 w-6" />
              Gerar Novo Relatório
            </Button>
          </Link>
          <Link href="/editar-clientes" className="block">
            <Button className="w-full h-14 text-lg justify-start" variant="outline">
              <Users className="mr-3 h-6 w-6" />
              Gerir Clientes e Motores
            </Button>
          </Link>
          <Link href="/relatorios-salvos" className="block">
            <Button className="w-full h-14 text-lg justify-start" variant="secondary">
              <FolderOpen className="mr-3 h-6 w-6" />
              Visualizar Relatórios Salvos
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}