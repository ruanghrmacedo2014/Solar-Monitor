from io import BytesIO

from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)


PAGE_WIDTH, PAGE_HEIGHT = A4


class SolarMonitorPDF:
    def __init__(self):
        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#123B2A"),
            spaceAfter=12,
        )

        self.subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#5B6B63"),
            spaceAfter=20,
        )

        self.section_style = ParagraphStyle(
            "SectionTitle",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#123B2A"),
            spaceBefore=8,
            spaceAfter=10,
        )

        self.body_style = ParagraphStyle(
            "Body",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#303833"),
            spaceAfter=6,
        )

        self.small_style = ParagraphStyle(
            "Small",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#6B756F"),
        )

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#D9E5DE")
        )
        canvas.setLineWidth(0.7)

        canvas.line(
            20 * mm,
            PAGE_HEIGHT - 18 * mm,
            PAGE_WIDTH - 20 * mm,
            PAGE_HEIGHT - 18 * mm,
        )

        canvas.setFont(
            "Helvetica-Bold",
            8,
        )

        canvas.setFillColor(
            colors.HexColor("#123B2A")
        )

        canvas.drawString(
            20 * mm,
            PAGE_HEIGHT - 14 * mm,
            "SOLAR MONITOR",
        )

        canvas.setStrokeColor(
            colors.HexColor("#D9E5DE")
        )

        canvas.line(
            20 * mm,
            16 * mm,
            PAGE_WIDTH - 20 * mm,
            16 * mm,
        )

        canvas.setFont(
            "Helvetica",
            7,
        )

        canvas.setFillColor(
            colors.HexColor("#6B756F")
        )

        canvas.drawString(
            20 * mm,
            10 * mm,
            "Solar Monitor — Relatório de geração",
        )

        canvas.drawRightString(
            PAGE_WIDTH - 20 * mm,
            10 * mm,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    def build_generation_chart(
        self,
        chart_data: list[dict],
        width: float = 160 * mm,
        height: float = 75 * mm,
    ):
        drawing = Drawing(
            width,
            height,
        )

        plot = LinePlot()

        plot.x = 35
        plot.y = 20
        plot.width = width - 55
        plot.height = height - 40

        expected_points = []
        actual_points = []

        for index, item in enumerate(chart_data):
            expected = item.get(
                "expected_kwh"
            )

            actual = item.get(
                "generation_kwh"
            )

            if expected is not None:
                expected_points.append(
                    (
                        index,
                        float(expected),
                    )
                )

            if actual is not None:
                actual_points.append(
                    (
                        index,
                        float(actual),
                    )
                )

        # O LinePlot precisa de pelo menos
        # dois pontos para desenhar uma linha.
        series = []

        if len(expected_points) >= 2:
            series.append(expected_points)

        if len(actual_points) >= 2:
            series.append(actual_points)

        # Se não houver nenhuma série com
        # pontos suficientes, não tenta desenhar.
        if not series:
            return Paragraph(
                "Dados insuficientes para gerar "
                "o gráfico deste período.",
                self.body_style,
            )

        plot.data = series

        # Primeira série
        # normalmente representa a geração esperada.
        if expected_points and len(expected_points) >= 2:
            plot.lines[0].strokeColor = (
                colors.HexColor("#6B756F")
            )
            plot.lines[0].strokeWidth = 2

        # Segunda série somente existe quando
        # há pelo menos dois pontos reais.
        if (
            len(expected_points) >= 2
            and len(actual_points) >= 2
        ):
            plot.lines[1].strokeColor = (
                colors.HexColor("#123B2A")
            )
            plot.lines[1].strokeWidth = 2

        plot.xValueAxis.valueMin = 0

        plot.xValueAxis.valueMax = max(
            len(chart_data) - 1,
            1,
        )

        plot.xValueAxis.valueStep = 1

        max_value = max(
            [
                value
                for series_data in [
                    expected_points,
                    actual_points,
                ]
                for _, value in series_data
            ],
            default=1,
        )

        plot.yValueAxis.valueMin = 0

        plot.yValueAxis.valueMax = (
            max_value * 1.15
        )

        plot.yValueAxis.valueStep = max(
            plot.yValueAxis.valueMax / 5,
            1,
        )

        drawing.add(plot)

        legend = Legend()

        legend.x = width - 95
        legend.y = height - 15
        legend.dx = 8
        legend.dy = 8
        legend.fontSize = 8

        legend.colorNamePairs = [
            (
                colors.HexColor("#6B756F"),
                "Esperada",
            ),
        ]

        if len(actual_points) >= 2:
            legend.colorNamePairs.append(
                (
                    colors.HexColor("#123B2A"),
                    "Real",
                )
            )

        drawing.add(legend)

        return drawing

    def build_plant_page(
        self,
        story,
        plant_data,
    ):
        story.append(
            Paragraph(
                plant_data.plant_name,
                self.section_style,
            )
        )

        installed_power = (
            f"{plant_data.installed_power_kwp:.2f} kWp"
            if plant_data.installed_power_kwp
            is not None
            else "Não informado"
        )

        story.append(
            Paragraph(
                f"<b>Potência instalada:</b> "
                f"{installed_power}",
                self.body_style,
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        story.append(
            Paragraph(
                f"<b>Geração real:</b> "
                f"{plant_data.actual_kwh:.2f} kWh",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Geração esperada:</b> "
                f"{plant_data.expected_kwh:.2f} kWh",
                self.body_style,
            )
        )

        performance_text = (
            f"{plant_data.performance_percent:.2f}%"
            if plant_data.performance_percent
            is not None
            else "Não disponível"
        )

        story.append(
            Paragraph(
                f"<b>Desempenho:</b> "
                f"{performance_text}",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Cobertura dos dados:</b> "
                f"{plant_data.coverage_percent:.2f}%",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Qualidade dos dados:</b> "
                f"{plant_data.data_quality}",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Classificação:</b> "
                f"{plant_data.classification}",
                self.body_style,
            )
        )

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        story.append(
            Paragraph(
                "GERAÇÃO REAL × ESPERADA",
                self.section_style,
            )
        )

        if plant_data.chart_data:
            story.append(
                self.build_generation_chart(
                    chart_data=plant_data.chart_data,
                )
            )
        else:
            story.append(
                Paragraph(
                    "Não existem dados disponíveis "
                    "para gerar o gráfico deste período.",
                    self.body_style,
                )
            )

    def build_customer_report(
        self,
        report_data,
    ) -> bytes:
        buffer = BytesIO()

        frame = Frame(
            20 * mm,
            22 * mm,
            PAGE_WIDTH - 40 * mm,
            PAGE_HEIGHT - 48 * mm,
            id="normal",
        )

        document = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=25 * mm,
            bottomMargin=22 * mm,
        )

        document.addPageTemplates(
            [
                PageTemplate(
                    id="solar-monitor",
                    frames=frame,
                    onPage=self._draw_header_footer,
                )
            ]
        )

        story = []

        # =========================
        # CAPA / RESUMO DO CLIENTE
        # =========================

        story.append(
            Spacer(
                1,
                35 * mm,
            )
        )

        story.append(
            Paragraph(
                "RELATÓRIO DE GERAÇÃO",
                self.title_style,
            )
        )

        story.append(
            Paragraph(
                "Monitoramento e desempenho "
                "do sistema fotovoltaico",
                self.subtitle_style,
            )
        )

        story.append(
            Spacer(
                1,
                15 * mm,
            )
        )

        story.append(
            Paragraph(
                f"<b>Cliente:</b> "
                f"{report_data.customer_name}",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Período:</b> "
                f"{report_data.period_start.strftime('%d/%m/%Y')}"
                f" a "
                f"{report_data.period_end.strftime('%d/%m/%Y')}",
                self.body_style,
            )
        )

        story.append(
            Spacer(
                1,
                20 * mm,
            )
        )

        story.append(
            Paragraph(
                "RESUMO",
                self.section_style,
            )
        )

        story.append(
            Paragraph(
                "Este documento apresenta o desempenho "
                "das usinas vinculadas ao cliente no período "
                "selecionado.",
                self.body_style,
            )
        )

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        story.append(
            Paragraph(
                f"<b>Geração real:</b> "
                f"{report_data.total_actual_kwh:.2f} kWh",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Geração esperada:</b> "
                f"{report_data.total_expected_kwh:.2f} kWh",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Cobertura média:</b> "
                f"{report_data.average_coverage_percent:.2f}%",
                self.body_style,
            )
        )

        performance_text = (
            f"{report_data.overall_performance_percent:.2f}%"
            if report_data.overall_performance_percent
            is not None
            else "Não disponível"
        )

        story.append(
            Paragraph(
                f"<b>Desempenho:</b> "
                f"{performance_text}",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Qualidade dos dados:</b> "
                f"{report_data.data_quality}",
                self.body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Classificação:</b> "
                f"{report_data.classification}",
                self.body_style,
            )
        )

        # =========================
        # PÁGINAS DAS USINAS
        # =========================

        for plant_data in report_data.plants:
            story.append(PageBreak())

            self.build_plant_page(
                story=story,
                plant_data=plant_data,
            )

        document.build(story)

        return buffer.getvalue()