using System.Drawing;
using EstoqueIncenso.Application.Interfaces;
using Microsoft.Extensions.Logging;
using OfficeOpenXml;
using OfficeOpenXml.Style;

namespace EstoqueIncenso.Application.Servicos;

public class ServicoExportacao : IServicoExportacao
{
    private readonly IServicoRegistro _servicoRegistro;
    private readonly ILogger<ServicoExportacao> _logger;

    public ServicoExportacao(IServicoRegistro servicoRegistro, ILogger<ServicoExportacao> logger)
    {
        _servicoRegistro = servicoRegistro;
        _logger = logger;
    }

    public async Task<byte[]> GerarExcelAsync(int ano, int mes)
    {
        ExcelPackage.License.SetNonCommercialPersonal("EstoqueIncenso");

        _logger.LogInformation("Gerando Excel para {Mes}/{Ano}", mes, ano);

        var grade = await _servicoRegistro.MontarGradeMensalAsync(ano, mes);

        var diasNoMes = DateTime.DaysInMonth(ano, mes);
        var funcionarias = grade.Funcionarias.ToList();

        using var package = new ExcelPackage();

        // ── Aba "Produção" ────────────────────────────────────────────────────
        var wsProd = package.Workbook.Worksheets.Add("Produção");

        // Cabeçalho — linha 1
        wsProd.Cells[1, 1].Value = "Funcionária";
        for (int dia = 1; dia <= diasNoMes; dia++)
        {
            wsProd.Cells[1, dia + 1].Value = dia.ToString();
        }
        wsProd.Cells[1, diasNoMes + 2].Value = "Total";

        // Negrito no cabeçalho
        using (var cabecalho = wsProd.Cells[1, 1, 1, diasNoMes + 2])
        {
            cabecalho.Style.Font.Bold = true;
        }

        // Determinar colunas de fins de semana
        var colunasFimDeSemana = new HashSet<int>();
        for (int dia = 1; dia <= diasNoMes; dia++)
        {
            var data = new DateTime(ano, mes, dia);
            if (data.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday)
                colunasFimDeSemana.Add(dia + 1); // +1 porque col 1 é "Funcionária"
        }

        // Rastrear células de falta para não sobrescrever com cinza depois
        var celulasFalta = new HashSet<(int Linha, int Coluna)>();

        // Índice de registros por dia para cada funcionária
        int linhaFuncionaria = 2;
        foreach (var func in funcionarias)
        {
            var registrosPorDia = func.Registros
                .ToDictionary(r => r.Data.Day);

            wsProd.Cells[linhaFuncionaria, 1].Value = func.Nome;

            int totalMensal = 0;
            for (int dia = 1; dia <= diasNoMes; dia++)
            {
                int coluna = dia + 1;
                var celula = wsProd.Cells[linhaFuncionaria, coluna];

                if (registrosPorDia.TryGetValue(dia, out var reg))
                {
                    if (reg.Falta)
                    {
                        celula.Value = "FALTA";
                        celula.Style.Fill.PatternType = ExcelFillStyle.Solid;
                        celula.Style.Fill.BackgroundColor.SetColor(Color.LightYellow);
                        celulasFalta.Add((linhaFuncionaria, coluna));
                    }
                    else if (reg.Quantidade.HasValue)
                    {
                        celula.Value = reg.Quantidade.Value;
                        totalMensal += reg.Quantidade.Value;
                    }
                    // else: célula vazia (sem registro)
                }
                // else: célula vazia (sem registro para o dia)
            }

            wsProd.Cells[linhaFuncionaria, diasNoMes + 2].Value = totalMensal;

            linhaFuncionaria++;
        }

        // Linha "TOTAL" (soma por coluna de dia + total geral)
        int linhaTotal = linhaFuncionaria;
        wsProd.Cells[linhaTotal, 1].Value = "TOTAL";
        wsProd.Cells[linhaTotal, 1].Style.Font.Bold = true;

        int totalGeral = 0;
        for (int dia = 1; dia <= diasNoMes; dia++)
        {
            int coluna = dia + 1;
            int somaColuna = 0;
            for (int linha = 2; linha < linhaTotal; linha++)
            {
                var val = wsProd.Cells[linha, coluna].Value;
                if (val is int intVal)
                    somaColuna += intVal;
                else if (val is double dblVal)
                    somaColuna += (int)dblVal;
            }
            wsProd.Cells[linhaTotal, coluna].Value = somaColuna;
            wsProd.Cells[linhaTotal, coluna].Style.Font.Bold = true;
            totalGeral += somaColuna;
        }

        wsProd.Cells[linhaTotal, diasNoMes + 2].Value = totalGeral;
        wsProd.Cells[linhaTotal, diasNoMes + 2].Style.Font.Bold = true;

        // Aplicar fundo cinza nas colunas de fim de semana (da linha 1 até a linha de TOTAL)
        // Células de falta (amarelo) têm prioridade — não são sobrescritas
        foreach (var col in colunasFimDeSemana)
        {
            for (int linha = 1; linha <= linhaTotal; linha++)
            {
                if (celulasFalta.Contains((linha, col)))
                    continue; // preserva o amarelo de falta

                var celula = wsProd.Cells[linha, col];
                celula.Style.Fill.PatternType = ExcelFillStyle.Solid;
                celula.Style.Fill.BackgroundColor.SetColor(Color.LightGray);
            }
        }

        wsProd.Cells[wsProd.Dimension?.Address ?? "A1"].AutoFitColumns();

        // ── Aba "Faltas" ──────────────────────────────────────────────────────
        var wsFaltas = package.Workbook.Worksheets.Add("Faltas");

        // Cabeçalho
        wsFaltas.Cells[1, 1].Value = "Funcionária";
        wsFaltas.Cells[1, 2].Value = "Data";
        wsFaltas.Cells[1, 3].Value = "Motivo";
        wsFaltas.Cells[1, 4].Value = "Observação";

        using (var cabecalhoFaltas = wsFaltas.Cells[1, 1, 1, 4])
        {
            cabecalhoFaltas.Style.Font.Bold = true;
        }

        // Registros de falta, ordenados por data depois por nome
        var faltas = funcionarias
            .SelectMany(f => f.Registros
                .Where(r => r.Falta)
                .Select(r => new { Funcionaria = f.Nome, Registro = r }))
            .OrderBy(x => x.Registro.Data)
            .ThenBy(x => x.Funcionaria)
            .ToList();

        int linhaFalta = 2;
        foreach (var item in faltas)
        {
            wsFaltas.Cells[linhaFalta, 1].Value = item.Funcionaria;
            wsFaltas.Cells[linhaFalta, 2].Value = item.Registro.Data.ToString("dd/MM/yyyy");
            wsFaltas.Cells[linhaFalta, 3].Value = item.Registro.MotivoFalta ?? string.Empty;
            wsFaltas.Cells[linhaFalta, 4].Value = item.Registro.ObservacaoFalta ?? string.Empty;
            linhaFalta++;
        }

        wsFaltas.Cells[wsFaltas.Dimension?.Address ?? "A1"].AutoFitColumns();

        _logger.LogInformation(
            "Excel gerado: {QtdFuncionarias} funcionária(s), {QtdFaltas} falta(s)",
            funcionarias.Count, faltas.Count);

        return package.GetAsByteArray();
    }
}
