using EstoqueIncenso.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace EstoqueIncenso.Api.Controladores;

[ApiController]
[Route("api/exportacao")]
public class ControladorExportacao : ControllerBase
{
    private readonly IServicoExportacao _servicoExportacao;

    public ControladorExportacao(IServicoExportacao servicoExportacao)
    {
        _servicoExportacao = servicoExportacao;
    }

    /// <summary>
    /// Gera e retorna o arquivo Excel com a grade de produção mensal e as faltas.
    /// </summary>
    [HttpGet("excel")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> GerarExcel(
        [FromQuery] int? ano,
        [FromQuery] int? mes)
    {
        if (ano is null || mes is null)
            return BadRequest(new { erro = "Os parâmetros 'ano' e 'mes' são obrigatórios." });

        if (mes < 1 || mes > 12)
            return BadRequest(new { erro = "O parâmetro 'mes' deve estar entre 1 e 12." });

        var bytes = await _servicoExportacao.GerarExcelAsync(ano.Value, mes.Value);

        return File(
            bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            $"producao_{ano}_{mes:D2}.xlsx");
    }
}
