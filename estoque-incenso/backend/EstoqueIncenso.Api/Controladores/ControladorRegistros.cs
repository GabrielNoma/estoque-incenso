using EstoqueIncenso.Application.DTOs;
using EstoqueIncenso.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace EstoqueIncenso.Api.Controladores;

[ApiController]
[Route("api/registros")]
public class ControladorRegistros : ControllerBase
{
    private readonly IServicoRegistro _servico;

    public ControladorRegistros(IServicoRegistro servico)
    {
        _servico = servico;
    }

    /// <summary>
    /// Retorna a grade mensal com todas as funcionárias e seus registros.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(GradeMensalDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ObterGradeMensal(
        [FromQuery] int? ano,
        [FromQuery] int? mes)
    {
        if (ano is null || mes is null)
            return BadRequest(new { erro = "Os parâmetros 'ano' e 'mes' são obrigatórios." });

        var grade = await _servico.MontarGradeMensalAsync(ano.Value, mes.Value);
        return Ok(grade);
    }

    /// <summary>
    /// Cria ou atualiza um registro diário (upsert por funcionária+data).
    /// </summary>
    [HttpPut]
    [ProducesResponseType(typeof(RegistroSalvoDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> SalvarOuAtualizar([FromBody] UpsertRegistroDto dto)
    {
        try
        {
            var salvo = await _servico.SalvarOuAtualizarAsync(dto);
            return Ok(salvo);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { erro = ex.Message });
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(new { erro = ex.Message });
        }
    }

    /// <summary>
    /// Remove um registro pelo Id (limpa a célula).
    /// </summary>
    [HttpDelete("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Excluir(int id)
    {
        try
        {
            await _servico.ExcluirAsync(id);
            return NoContent();
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(new { erro = ex.Message });
        }
    }
}
