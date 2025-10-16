"""
Serviço de Geração de PDF para Projetos da Bragantec
Baseado no template oficial com cabeçalho vermelho
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

class BragantecPDFGenerator:
    """Gerador de PDF no formato oficial da Bragantec"""
    
    def __init__(self, projeto, participante):
        self.projeto = projeto
        self.participante = participante
        self.buffer = BytesIO()
        self.width, self.height = A4
        
        # Cores do template Bragantec
        self.cor_cabecalho = colors.HexColor('#E74C3C')  # Vermelho Bragantec
        self.cor_texto_destaque = colors.HexColor('#C0392B')  # Vermelho escuro
        self.cor_bordas = colors.HexColor('#34495E')  # Cinza azulado
        
    def gerar(self):
        """Gera o PDF completo e retorna o buffer"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2*cm
        )
        
        # Estilos
        self.criar_estilos()
        
        # Conteúdo
        story = []
        
        # Cabeçalho especial
        story.append(self._criar_cabecalho())
        story.append(Spacer(1, 0.5*cm))
        
        # Instruções iniciais
        story.append(self._criar_instrucoes())
        story.append(Spacer(1, 0.5*cm))
        
        # Título do Projeto
        story.append(self._criar_secao_titulo())
        story.append(Spacer(1, 0.3*cm))
        
        # Categoria
        story.append(self._criar_secao_categoria())
        story.append(Spacer(1, 0.3*cm))
        
        # Resumo
        story.append(self._criar_secao_resumo())
        story.append(Spacer(1, 0.3*cm))
        
        # Palavras-chave
        story.append(self._criar_secao_palavras_chave())
        story.append(Spacer(1, 0.5*cm))
        
        # Plano de Pesquisa (título)
        story.append(Paragraph("PLANO DE PESQUISA", self.style_titulo_secao))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "O PLANO DE PESQUISA É O PLANEJAMENTO INICIAL DO QUE SERÁ EXECUTADO EM SUA "
            "PESQUISA. ELE É NECESSARIAMENTE UM DOCUMENTO ESCRITO E QUE SERVIRÁ COMO UM "
            "DIRECIONADOR PARA AS SUAS ATIVIDADES.",
            self.style_instrucao_box
        ))
        story.append(Spacer(1, 0.5*cm))
        
        # Introdução
        story.append(self._criar_secao_introducao())
        story.append(Spacer(1, 0.3*cm))
        
        # Objetivos
        story.append(self._criar_secao_objetivos())
        story.append(Spacer(1, 0.3*cm))
        
        # Metodologia
        story.append(self._criar_secao_metodologia())
        story.append(Spacer(1, 0.3*cm))
        
        # Cronograma
        story.append(self._criar_secao_cronograma())
        story.append(Spacer(1, 0.3*cm))
        
        # Resultados Esperados
        story.append(self._criar_secao_resultados())
        story.append(Spacer(1, 0.3*cm))
        
        # Referências
        story.append(self._criar_secao_referencias())
        story.append(Spacer(1, 0.5*cm))
        
        # Continuação de Projeto Anterior (se aplicável)
        if self.projeto.eh_continuacao:
            story.append(PageBreak())
            story.append(self._criar_secao_continuacao())
        
        # Declaração final
        story.append(Spacer(1, 0.5*cm))
        story.append(self._criar_declaracao_final())
        
        # Gera PDF
        doc.build(story, onFirstPage=self._add_header, onLaterPages=self._add_header)
        
        self.buffer.seek(0)
        return self.buffer
    
    def criar_estilos(self):
        """Cria estilos personalizados"""
        styles = getSampleStyleSheet()
        
        # Título principal
        self.style_titulo = ParagraphStyle(
            'TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.cor_texto_destaque,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Título de seção
        self.style_titulo_secao = ParagraphStyle(
            'TituloSecao',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            spaceBefore=6
        )
        
        # Texto normal
        self.style_normal = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # Instruções em vermelho
        self.style_instrucao = ParagraphStyle(
            'Instrucao',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.cor_texto_destaque,
            leading=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Oblique'
        )
        
        # Caixa de instrução
        self.style_instrucao_box = ParagraphStyle(
            'InstrucaoBox',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            leading=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Label
        self.style_label = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.black
        )
    
    def _add_header(self, canvas, doc):
        """Adiciona cabeçalho vermelho com logo em todas as páginas"""
        canvas.saveState()
        
        # Retângulo vermelho no topo
        canvas.setFillColor(self.cor_cabecalho)
        canvas.rect(0, self.height - 2*cm, self.width, 2*cm, fill=1, stroke=0)
        
        # Logo da Bragantec (se existir)
        try:
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg
            
            logo = svg2rlg('static/img/logo_bragantec.svg')
            if logo:
                logo.width = 4*cm
                logo.height = 1.5*cm
                logo.scale(0.8, 0.8)
                renderPDF.draw(logo, canvas, 1.5*cm, self.height - 1.8*cm)
        except:
            # Fallback: texto se logo não disponível
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 18)
            canvas.drawString(2*cm, self.height - 1.3*cm, "BRAGANTEC")
        
        # Subtítulo
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(self.width/2, self.height - 1.7*cm, 
                                "13ª Feira de Ciências - IFSP Bragança Paulista")
        
        # Número da página (rodapé)
        canvas.setFillColor(colors.black)
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(self.width/2, 1*cm, f"Página {doc.page}")
        
        canvas.restoreState()
    
    def _criar_cabecalho(self):
        """Cria o cabeçalho com instruções"""
        instrucao = Paragraph(
            "<b>FAÇA UMA CÓPIA OU DOWNLOAD DESTE DOCUMENTO PARA PREENCHÊ-LO</b><br/>"
            "<i>Preencha os campos sobre o projeto e, antes de gerar o pdf para envio, "
            "apague todas as orientações em vermelho.</i>",
            self.style_instrucao
        )
        return instrucao
    
    def _criar_instrucoes(self):
        """Box de instruções"""
        return Paragraph("", self.style_normal)
    
    def _criar_secao_titulo(self):
        """Seção do título do projeto"""
        data = [
            [Paragraph("<b>TÍTULO DO PROJETO:</b>", self.style_label)],
            [Paragraph(self.projeto.nome or "", self.style_normal)],
            [Paragraph(
                "<i>O título é o primeiro contato que um visitante ou avaliador tem com seu projeto. "
                "Ele deve ser simples, direto e atrativo.</i>",
                self.style_instrucao
            )]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_categoria(self):
        """Seção de categoria com checkboxes"""
        categorias = [
            "Ciências da Natureza e Exatas",
            "Informática",
            "Ciências Humanas e Linguagens",
            "Engenharias"
        ]
        
        checkboxes = []
        for cat in categorias:
            checked = "☒" if self.projeto.categoria == cat else "☐"
            checkboxes.append(f"{checked} {cat}")
        
        data = [
            [Paragraph("<b>CATEGORIA (MARCAR APENAS UMA):</b>", self.style_label)],
            [Paragraph("<br/>".join(checkboxes), self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_resumo(self):
        """Seção do resumo"""
        data = [
            [Paragraph("<b>RESUMO:</b>", self.style_label)],
            [Paragraph(self.projeto.resumo or "", self.style_normal)],
            [Paragraph(
                "<i>O Resumo é o cartão de visita de seu projeto. Deve conter no máximo 300 palavras.</i>",
                self.style_instrucao
            )]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_palavras_chave(self):
        """Seção de palavras-chave"""
        data = [
            [Paragraph("<b>PALAVRAS-CHAVE:</b>", self.style_label)],
            [Paragraph(self.projeto.palavras_chave or "", self.style_normal)],
            [Paragraph("<i>(três palavras-chaves separadas por vírgula)</i>", self.style_instrucao)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_introducao(self):
        """Seção de introdução"""
        data = [
            [Paragraph("<b>INTRODUÇÃO:</b>", self.style_label)],
            [Paragraph(self.projeto.introducao or "", self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_objetivos(self):
        """Seção de objetivos"""
        objetivos_text = f"<b>Objetivo Geral:</b><br/>{self.projeto.objetivo_geral or ''}<br/><br/>"
        
        if self.projeto.objetivos_especificos:
            objetivos_text += "<b>Objetivos Específicos:</b><br/>"
            for i, obj in enumerate(self.projeto.objetivos_especificos, 1):
                objetivos_text += f"{i}. {obj}<br/>"
        
        data = [
            [Paragraph("<b>OBJETIVOS:</b>", self.style_label)],
            [Paragraph(objetivos_text, self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_metodologia(self):
        """Seção de metodologia"""
        data = [
            [Paragraph("<b>METODOLOGIA:</b>", self.style_label)],
            [Paragraph(self.projeto.metodologia or "", self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_cronograma(self):
        """Seção de cronograma com tabela"""
        if not self.projeto.cronograma:
            return Paragraph("<b>CRONOGRAMA:</b> Não informado", self.style_normal)
        
        # Cabeçalho da tabela
        meses = ['Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov']
        header = ['Etapa'] + meses
        
        # Dados do cronograma
        rows = [header]
        
        try:
            cronograma = self.projeto.cronograma if isinstance(self.projeto.cronograma, list) else []
            for item in cronograma:
                etapa = item.get('etapa', '')
                meses_marcados = item.get('meses', [])
                row = [etapa] + ['X' if mes in meses_marcados else '' for mes in meses]
                rows.append(row)
        except:
            pass
        
        if len(rows) == 1:
            rows.append(['Nenhuma etapa definida'] + ['']*9)
        
        table = Table(rows, colWidths=[6*cm] + [1.2*cm]*9)
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _criar_secao_resultados(self):
        """Seção de resultados esperados"""
        data = [
            [Paragraph("<b>RESULTADOS ESPERADOS:</b>", self.style_label)],
            [Paragraph(self.projeto.resultados_esperados or "", self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_referencias(self):
        """Seção de referências"""
        data = [
            [Paragraph("<b>REFERÊNCIAS BIBLIOGRÁFICAS:</b>", self.style_label)],
            [Paragraph(self.projeto.referencias_bibliograficas or "", self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_secao_continuacao(self):
        """Seção de continuação de projeto anterior"""
        data = [
            [Paragraph("<b>CONTINUAÇÃO DE PROJETO ANTERIOR</b>", self.style_titulo_secao)],
            [Paragraph(f"<b>Título:</b> {self.projeto.projeto_anterior_titulo or ''}", self.style_normal)],
            [Paragraph(f"<b>Resumo:</b> {self.projeto.projeto_anterior_resumo or ''}", self.style_normal)],
            [Paragraph(f"<b>Período:</b> {self.projeto.projeto_anterior_inicio} a {self.projeto.projeto_anterior_termino}", 
                      self.style_normal)]
        ]
        
        table = Table(data, colWidths=[self.width - 4*cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, self.cor_bordas),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return table
    
    def _criar_declaracao_final(self):
        """Declaração final"""
        texto = (
            "<b>AO INSCREVER O PROJETO CONCORDAMOS COM O REGULAMENTO DA 13ª BRAGANTEC E "
            "DECLARAMOS QUE AS INFORMAÇÕES ACIMA ESTÃO CORRETAS E O RESUMO E PÔSTER REFLETEM "
            "APENAS O TRABALHO REALIZADO AO LONGO DOS ÚLTIMOS 12 (DOZE) MESES.</b>"
        )
        
        return Paragraph(texto, self.style_instrucao_box)