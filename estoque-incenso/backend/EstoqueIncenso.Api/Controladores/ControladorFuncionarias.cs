using EstoqueIncenso.Application.DTOs;
using EstoqueIncenso.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace EstoqueIncenso.Api.Controladores;

[ApiController]
[Route("api/funcionarias")]
public class ControladorFuncionarias : ControllerBase
{
    private readonly IServicoFuncionaria _servico;

    public ControladorFuncionarias(IServicoFuncionaria servico)
    {
        _servico = servico;
    }

    /// <summary>
    /// Lista funcionárias. Por padrão retorna apenas ativas.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<FuncionariaDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> Listar([FromQuery] bool incluirInativas = false)
    {
        var funcionarias = await _servico.ListarAsync(incluirInativas);
        return Ok(funcionarias);
    }

    /// <summary>
    /// Cria uma nova funcionária.
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(FuncionariaDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Criar([FromBody] CriarFuncionariaDto dto)
    {
        try
        {
            var criada = await _servico.CriarAsync(dto);
            return CreatedAtAction(nameof(Listar), new { id = criada.Id }, criada);
        }
        catch (InvalidOperationException ex)
        {
            return Conflict(new { erro = ex.Message });
        }
    }

    /// <summary>
    /// Atualiza o nome de uma funcionária.
    /// </summary>
    [HttpPut("{id:int}")]
    [ProducesResponseType(typeof(FuncionariaDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Atualizar(int id, [FromBody] AtualizarFuncionariaDto dto)
    {
        var atualizada = await _servico.AtualizarAsync(id, dto);
        return Ok(atualizada);
    }

    /// <summary>
    /// Ativa ou desativa uma funcionária.
    /// </summary>
    [HttpPatch("{id:int}/status")]
    [ProducesResponseType(typeof(FuncionariaDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> AlterarStatus(int id, [FromBody] AtualizarStatusDto dto)
    {
        var atualizada = await _servico.AlterarStatusAsync(id, dto.Ativa);
        return Ok(atualizada);
    }
}
