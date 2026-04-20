using EstoqueIncenso.Domain.Entidades;

namespace EstoqueIncenso.Application.Interfaces;

public interface IRepositorioFuncionaria
{
    Task<IEnumerable<Funcionaria>> ListarAsync(bool incluirInativas);
    Task<Funcionaria?> BuscarPorIdAsync(int id);
    Task<bool> ExisteComNomeAsync(string nome, int? excluirId = null);
    Task<Funcionaria> CriarAsync(Funcionaria funcionaria);
    Task<Funcionaria> AtualizarAsync(Funcionaria funcionaria);
}
