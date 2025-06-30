"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, PlusCircle, Edit, Trash2 } from "lucide-react"

// Componente do formulário (sem alterações)
function FormularioRegistro({ onSave, registroInicial, isEditMode }) {
    const [formData, setFormData] = useState({});
    useEffect(() => {
        const defaultState = {
            id_cliente: '', nome_cliente: '', descricao_motor: '', local_instalacao: '',
            corrente_nominal: '', potencia_cv: '', tipo_conexao: '', tensao_nominal_v: '',
            grupo_tarifario: '', telefone_contato: '', email_responsavel: '',
            data_da_instalacao: '', id_esp32: '', observacoes: ''
        };
        setFormData(isEditMode && registroInicial ? registroInicial : defaultState);
    }, [registroInicial, isEditMode]);

    const handleChange = (e) => {
        const { id, value } = e.target;
        setFormData(prev => ({ ...prev, [id]: value }));
    };
    const handleSubmit = (e) => { e.preventDefault(); onSave(formData); };
    const formatarLabel = (texto) => {
        const textoFormatado = texto.replace(/_/g, ' ');
        return textoFormatado.charAt(0).toUpperCase() + textoFormatado.slice(1);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 py-4 font-sans">
                {Object.keys(formData).map((key) => (
                    <div className="space-y-2" key={key}>
                        <Label htmlFor={key} className="font-semibold text-gray-800">{formatarLabel(key)}</Label>
                        <Input id={key} value={formData[key] || ''} onChange={handleChange} className="border-gray-300 focus:border-blue-500 focus:ring-blue-500" />
                    </div>
                ))}
            </div>
            <DialogFooter className="mt-4">
                <DialogClose asChild><Button type="button" variant="secondary">Cancelar</Button></DialogClose>
                <Button type="submit">Salvar Alterações</Button>
            </DialogFooter>
        </form>
    );
}

// Componente principal da página
export default function GerenciarClientesPage() {
    const [registros, setRegistros] = useState([])
    const [isDialogOpen, setDialogOpen] = useState(false);
    const [registroSelecionado, setRegistroSelecionado] = useState(null);
    const [isEditMode, setIsEditMode] = useState(false);

    const fetchRegistros = async () => {
        try {
            const response = await fetch("http://192.168.1.9:8000/api/registros")
            const data = await response.json()
            if (data && !data.erro) setRegistros(data)
        } catch (error) {
            console.error("Falha ao buscar registros:", error)
            alert("Não foi possível carregar os registros do servidor.")
        }
    }

    useEffect(() => { fetchRegistros() }, [])
    
    const handleAdicionar = () => {
        setIsEditMode(false);
        setRegistroSelecionado(null);
        setDialogOpen(true);
    };

    const handleEditar = (registro) => {
        setIsEditMode(true);
        setRegistroSelecionado(registro);
        setDialogOpen(true);
    };

    // ▼▼▼ AQUI ESTÁ A LÓGICA DE CONVERSÃO CORRIGIDA ▼▼▼
    const handleSave = async (formData) => {
        // Garante que os campos numéricos sejam enviados como números (ou null se vazios)
        const dadosParaEnviar = {
            ...formData,
            id_cliente: parseInt(formData.id_cliente) || null, // Converte para int ou null
            corrente_nominal: parseFloat(formData.corrente_nominal) || null,
            potencia_cv: parseFloat(formData.potencia_cv) || null,
            tensao_nominal_v: parseFloat(formData.tensao_nominal_v) || null
        };
        
        const url = isEditMode ? `http://192.168.1.9:8000/api/motores/${registroSelecionado.id_motor}` : "http://192.168.1.9:8000/api/motores";
        const method = isEditMode ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dadosParaEnviar) });
            const result = await response.json();
            if (response.ok) {
                alert(result.mensagem);
                setDialogOpen(false);
                fetchRegistros();
            } else {
                if (response.status === 422) {
                    const erroDetalhado = result.detail[0];
                    throw new Error(`Erro de validação no campo '${erroDetalhado.loc[1]}': ${erroDetalhado.msg}`);
                }
                throw new Error(result.detail || result.erro || "Falha ao salvar o registro.");
            }
        } catch (error) {
            console.error("Erro ao salvar:", error);
            alert(`Erro: ${error.message}`);
        }
    };

    const handleExcluir = async (id_motor) => {
        if (!window.confirm("Tem certeza?")) return;
        try {
            const response = await fetch(`http://192.168.1.9:8000/api/motores/${id_motor}`, { method: 'DELETE' });
            if (response.ok) {
                alert("Registro removido!");
                fetchRegistros();
            } else {
                const erro = await response.json();
                throw new Error(erro.detail || "Falha ao excluir.");
            }
        } catch (error) {
            console.error("Erro ao excluir:", error);
            alert(`Erro: ${error.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-2xl font-bold text-blue-600">GESTÃO DE CLIENTES E MOTORES</CardTitle>
                        <Button onClick={handleAdicionar}><PlusCircle className="mr-2 h-4 w-4" />Adicionar Novo</Button>
                    </CardHeader>
                    <CardContent>
                        <Table>
                           <TableHeader><TableRow><TableHead>Cliente</TableHead><TableHead>Motor/Equipamento</TableHead><TableHead className="text-center">Contato</TableHead><TableHead className="text-right">Ações</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {registros.map((registro) => (
                                    <TableRow key={registro.id_motor}>
                                        <TableCell>{registro.nome_cliente}</TableCell>
                                        <TableCell>{registro.descricao_motor}</TableCell>
                                        <TableCell className="text-center">{registro.telefone_contato}</TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Button variant="outline" size="icon" onClick={() => handleEditar(registro)}><Edit className="h-4 w-4" /></Button>
                                            <Button variant="destructive" size="icon" onClick={() => handleExcluir(registro.id_motor)}><Trash2 className="h-4 w-4" /></Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                         {registros.length === 0 && (<p className="text-center text-gray-500 py-8">Nenhum registro encontrado.</p>)}
                    </CardContent>
                </Card>
                 <div className="pt-4 mt-4 border-t">
                    <Link href="/"><Button variant="secondary" className="w-full md:w-auto"><ArrowLeft className="mr-2 h-4 w-4" />Voltar</Button></Link>
                </div>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="sm:max-w-4xl"><DialogHeader><DialogTitle>{isEditMode ? 'Editar Registro' : 'Novo Registro'}</DialogTitle></DialogHeader><FormularioRegistro onSave={handleSave} registroInicial={registroSelecionado} isEditMode={isEditMode} /></DialogContent>
            </Dialog>
        </div>
    )
}