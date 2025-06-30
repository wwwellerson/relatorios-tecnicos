// Arquivo: frontend/app/relatorios-salvos/page.js (Versão final com TODOS os botões funcionais)
"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, FileText, Download, Eye, Trash2, Calendar, Mail, Loader2 } from "lucide-react"

export default function RelatoriosSalvosPage() {
    const [relatorios, setRelatorios] = useState([])
    const [isLoading, setIsLoading] = useState(true);
    const [sendingEmailId, setSendingEmailId] = useState(null); // Para controlar o loading do botão de e-mail

    const apiBaseUrl = "http://192.168.1.9:8000";

    const fetchRelatorios = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${apiBaseUrl}/api/relatorios-salvos`);
            const data = await response.json();
            if (response.ok) {
                setRelatorios(data);
            } else {
                throw new Error(data.detail || "Falha ao buscar relatórios.");
            }
        } catch (error) {
            console.error("Erro ao buscar relatórios salvos:", error);
            alert(`Erro: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchRelatorios();
    }, []);

    const handleEnviarEmail = async (nome_arquivo) => {
        setSendingEmailId(nome_arquivo); // Ativa o spinner no botão clicado
        try {
            const response = await fetch(`${apiBaseUrl}/api/relatorios-salvos/${nome_arquivo}/enviar-email`, {
                method: 'POST',
            });
            const result = await response.json();

            if (response.ok) {
                alert(result.message); // Exibe a mensagem de sucesso da API
            } else {
                throw new Error(result.detail || "Falha ao enviar o e-mail.");
            }
        } catch (error) {
            console.error("Erro ao enviar e-mail:", error);
            alert(`Erro: ${error.message}`);
        } finally {
            setSendingEmailId(null); // Desativa o spinner
        }
    };

    const handleExcluir = async (nome_arquivo) => {
        if (!window.confirm(`Tem certeza que deseja excluir o relatório "${nome_arquivo}" permanentemente?`)) return;
        
        try {
            const response = await fetch(`${apiBaseUrl}/api/relatorios-salvos/${nome_arquivo}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                alert("Relatório excluído com sucesso.");
                fetchRelatorios();
            } else {
                const erro = await response.json();
                throw new Error(erro.detail || "Falha ao excluir o relatório.");
            }
        } catch (error) {
            alert(`Erro: ${error.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-4 md:p-8">
            <div className="max-w-4xl mx-auto">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-2xl font-bold text-center text-blue-600">RELATÓRIOS SALVOS</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {isLoading ? (
                            <div className="flex justify-center items-center py-8"><Loader2 className="h-8 w-8 animate-spin text-blue-600" /><p className="ml-4 text-gray-500">Carregando...</p></div>
                        ) : relatorios.length === 0 ? (
                            <div className="text-center py-8"><FileText className="mx-auto h-16 w-16 text-gray-400 mb-4" /><p>Nenhum relatório foi gerado ainda.</p></div>
                        ) : (
                            <div className="space-y-3">
                                {relatorios.map((relatorio) => (
                                    <Card key={relatorio.nome_arquivo} className="border-l-4 border-l-blue-500">
                                        <CardContent className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between">
                                            <div className="flex-1 overflow-hidden mb-4 md:mb-0">
                                                <h3 className="font-semibold text-lg truncate" title={relatorio.nome_arquivo}>{relatorio.nome_arquivo}</h3>
                                                <p className="text-sm text-gray-600 truncate">{relatorio.cliente} / {relatorio.motor}</p>
                                                <div className="flex items-center text-xs text-gray-500 mt-2"><Calendar className="mr-1 h-4 w-4" />{relatorio.data} • {relatorio.tamanho_mb}</div>
                                            </div>
                                            <div className="flex gap-2 ml-0 md:ml-4 flex-shrink-0">
                                                <a href={`${apiBaseUrl}/api/relatorios-salvos/${relatorio.nome_arquivo}`} target="_blank" rel="noopener noreferrer"><Button title="Visualizar" size="sm" variant="outline"><Eye className="h-4 w-4" /></Button></a>
                                                <a href={`${apiBaseUrl}/api/relatorios-salvos/${relatorio.nome_arquivo}`} download><Button title="Baixar" size="sm" variant="outline"><Download className="h-4 w-4" /></Button></a>
                                                
                                                {/* Botão de e-mail agora chama a função e mostra loading */}
                                                <Button title="Enviar por E-mail" size="sm" variant="outline" onClick={() => handleEnviarEmail(relatorio.nome_arquivo)} disabled={sendingEmailId === relatorio.nome_arquivo}>
                                                    {sendingEmailId === relatorio.nome_arquivo ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
                                                </Button>

                                                <Button title="Excluir" size="sm" variant="destructive" onClick={() => handleExcluir(relatorio.nome_arquivo)}><Trash2 className="h-4 w-4" /></Button>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                        <div className="pt-4 border-t">
                            <Link href="/"><Button variant="secondary" className="w-full md:w-auto"><ArrowLeft className="mr-2 h-4 w-4" />Voltar ao Menu</Button></Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}