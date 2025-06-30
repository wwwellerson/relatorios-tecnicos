// Arquivo: frontend/app/novo-relatorio/page.js (Versão final com todos os campos)
"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { ArrowLeft, Upload, FileText, CheckCircle, Loader2 } from "lucide-react"

export default function NovoRelatorioPage() {
    const [clientes, setClientes] = useState([])
    const [motores, setMotores] = useState([])
    const [clienteSelecionado, setClienteSelecionado] = useState(null)
    const [motorSelecionado, setMotorSelecionado] = useState(null)
    const [arquivo, setArquivo] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [temVazao, setTemVazao] = useState(false)
    const [temNivel, setTemNivel] = useState(false)

    useEffect(() => {
        const fetchClientes = async () => {
            try {
                const response = await fetch("http://192.168.1.9:8000/api/clientes")
                const data = await response.json()
                if (data && !data.erro) setClientes(data)
            } catch (error) { console.error("Falha ao buscar clientes:", error) }
        }
        fetchClientes()
    }, [])

    useEffect(() => {
        if (!clienteSelecionado) {
            setMotores([]);
            setMotorSelecionado(null);
            return;
        }
        const fetchMotores = async () => {
            try {
                const response = await fetch(`http://192.168.1.9:8000/api/clientes/${clienteSelecionado.id_cliente}/motores`)
                const data = await response.json()
                setMotores(data && !data.erro ? data : []);
            } catch (error) {
                console.error("Falha ao buscar motores:", error);
                setMotores([]);
            }
        };
        fetchMotores();
    }, [clienteSelecionado]);

    const handleGerarRelatorio = async () => {
        if (!clienteSelecionado || !motorSelecionado || !arquivo) {
            alert("Por favor, selecione um cliente, um motor e um arquivo CSV.")
            return
        }

        const formData = new FormData();
        formData.append('id_motor', motorSelecionado.id_motor);
        formData.append('arquivo_csv', arquivo);
        formData.append('tem_vazao', temVazao);
        formData.append('tem_nivel', temNivel);

        setIsLoading(true);

        try {
            const response = await fetch("http://192.168.1.9:8000/api/relatorios", {
                method: 'POST',
                body: formData,
            });
            if (response.ok) {
                const header = response.headers.get('Content-Disposition');
                let filename = 'relatorio.pdf';
                if (header) {
                    const parts = header.split(';');
                    const filenamePart = parts.find(part => part.trim().startsWith('filename='));
                    if (filenamePart) filename = filenamePart.split('=')[1].replace(/"/g, '');
                }
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } else {
                const erro = await response.json();
                throw new Error(erro.detail || "Falha ao gerar o relatório.");
            }
        } catch (error) {
            alert(`Erro: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-gray-100 p-4">
            <div className="max-w-2xl mx-auto">
                <Card>
                    <CardHeader><CardTitle className="text-2xl font-bold text-center text-blue-600">GERAR NOVO RELATÓRIO</CardTitle></CardHeader>
                    <CardContent className="space-y-6">
                        {/* 1. SELEÇÃO DE CLIENTE */}
                        <div>
                            <Label className="block text-sm font-medium mb-2">1. Selecione o Cliente:</Label>
                            <Select onValueChange={(value) => setClienteSelecionado(clientes.find(c => c.id_cliente.toString() === value))}>
                                <SelectTrigger><SelectValue placeholder="Escolha um cliente..." /></SelectTrigger>
                                <SelectContent>{clientes.map((c) => (<SelectItem key={c.id_cliente} value={c.id_cliente.toString()}>{c.nome_cliente}</SelectItem>))}</SelectContent>
                            </Select>
                        </div>
                        {/* 2. SELEÇÃO DE MOTOR */}
                        <div>
                            <Label className="block text-sm font-medium mb-2">2. Selecione o Motor:</Label>
                            <Select onValueChange={(value) => setMotorSelecionado(motores.find(m => m.id_motor === value))} disabled={!clienteSelecionado}>
                                <SelectTrigger><SelectValue placeholder={!clienteSelecionado ? "Selecione um cliente primeiro..." : "Escolha um motor..."} /></SelectTrigger>
                                <SelectContent>{motores.map((m) => (<SelectItem key={m.id_motor} value={m.id_motor}>{m.descricao_motor}</SelectItem>))}</SelectContent>
                            </Select>
                        </div>
                        {/* 3. UPLOAD DE ARQUIVO */}
                        <div>
                            <Label className="block text-sm font-medium mb-2">3. Selecione o Arquivo de Dados (.csv):</Label>
                            <div className="flex items-center space-x-4">
                               <Label htmlFor="file-upload" className="flex-1 cursor-pointer bg-white text-blue-600 font-semibold rounded-md border border-blue-300 p-2.5 text-center hover:bg-blue-50">
                                   <Upload className="inline-block mr-2 h-4 w-4" />
                                   Selecionar Arquivo
                               </Label>
                                <Input id="file-upload" type="file" className="hidden" accept=".csv" onChange={(e) => setArquivo(e.target.files[0])} />
                                {arquivo && ( <div className="flex items-center text-sm text-green-600"><CheckCircle className="mr-2 h-5 w-5" /><span>{arquivo.name}</span></div> )}
                            </div>
                        </div>
                        {/* 4. ANÁLISES OPCIONAIS */}
                        <div className="space-y-4 pt-4">
                            <Label className="block text-sm font-medium">4. Análises Opcionais:</Label>
                            <div className="flex items-center space-x-2">
                                <Checkbox id="tem_vazao" checked={temVazao} onCheckedChange={setTemVazao} />
                                <label htmlFor="tem_vazao" className="text-sm font-medium leading-none cursor-pointer">
                                    Incluir dados de Vazão/Velocidade
                                </label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Checkbox id="tem_nivel" checked={temNivel} onCheckedChange={setTemNivel} />
                                <label htmlFor="tem_nivel" className="text-sm font-medium leading-none cursor-pointer">
                                    Incluir gráfico de Nível de Reservatório
                                </label>
                            </div>
                        </div>
                        {/* BOTÕES DE AÇÃO */}
                        <div className="flex gap-4 pt-4 border-t">
                            <Link href="/" className="flex-1"><Button variant="outline" className="w-full bg-transparent" disabled={isLoading}><ArrowLeft className="mr-2 h-4 w-4" />Voltar</Button></Link>
                            <Button onClick={handleGerarRelatorio} className="flex-1 bg-green-600 hover:bg-green-700" disabled={isLoading}>
                                {isLoading ? (<Loader2 className="mr-2 h-4 w-4 animate-spin" />) : (<FileText className="mr-2 h-4 w-4" />)}
                                {isLoading ? 'Gerando...' : 'Gerar Relatório'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}