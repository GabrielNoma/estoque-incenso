using EstoqueIncenso.Domain.Entidades;

namespace EstoqueIncenso.Application.Interfaces;

public interface IRepositorioRegistro
{
    Task<IEnumerable<RegistroDiario>> ListarPorMesAsync(int ano, int mes);
    Task<RegistroDiario?> BuscarPorFuncionariaEDataAsync(int funcionariaId, DateOnly data);
    Task<RegistroDiario> CriarOuAtualizarAsync(RegistroDiario registro);
    Task ExcluirAsync(int id);
}
