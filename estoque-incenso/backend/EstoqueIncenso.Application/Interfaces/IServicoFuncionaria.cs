using EstoqueIncenso.Application.DTOs;

namespace EstoqueIncenso.Application.Interfaces;

public interface IServicoFuncionaria
{
    Task<IEnumerable<FuncionariaDto>> ListarAsync(bool incluirInativas);
    Task<FuncionariaDto> CriarAsync(CriarFuncionariaDto dto);
    Task<FuncionariaDto> AtualizarAsync(int id, AtualizarFuncionariaDto dto);
    Task<FuncionariaDto> AlterarStatusAsync(int id, bool ativa);
}
